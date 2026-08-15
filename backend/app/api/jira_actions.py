import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models.jira import JiraActionRequest, JiraActionStatus, JiraActionType
from app.db.models.user import User
from app.integrations.jira_client import JiraClient, JiraNotConfigured

router = APIRouter(prefix="/api/jira", tags=["jira"])


@router.get("/search")
async def search(
    jql: str = Query(min_length=1, max_length=500),
    _user: User = Depends(get_current_user),
) -> list[dict]:
    """Read-only -- no approval gate needed. This is the button-driven path
    (a dedicated Jira page/search box), distinct from the chat tool of the
    same name, but they call the same underlying client."""
    try:
        client = JiraClient()
    except JiraNotConfigured:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Jira isn't configured") from None
    try:
        return await client.search_issues(jql)
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Jira search failed: {exc}") from None


@router.get("/actions")
async def list_actions(
    status_filter: JiraActionStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    # Scoped to the requesting user's own proposals -- someone else's staged
    # Jira edit isn't this user's to see or approve. (Admin-wide visibility
    # into everyone's pending approvals would be a reasonable Phase 2 if this
    # portal grows past single-user proposal queues.)
    stmt = select(JiraActionRequest).where(JiraActionRequest.requested_by_user_id == user.id)
    if status_filter:
        stmt = stmt.where(JiraActionRequest.status == status_filter)
    stmt = stmt.order_by(JiraActionRequest.created_at.desc()).limit(50)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": str(r.id),
            "action_type": r.action_type.value,
            "preview_text": r.preview_text,
            "status": r.status.value,
            "created_at": r.created_at.isoformat(),
            "result": r.result_json,
            "error_message": r.error_message,
        }
        for r in rows
    ]


async def _get_owned_pending_action(
    db: AsyncSession, action_id: str, user: User
) -> JiraActionRequest:
    try:
        action_uuid = uuid.UUID(action_id)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid action id") from None
    action = await db.get(JiraActionRequest, action_uuid)
    if action is None or action.requested_by_user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Action not found")
    if action.status != JiraActionStatus.PENDING:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Action is already {action.status.value}, not pending"
        )
    return action


@router.post("/actions/{action_id}/reject")
async def reject_action(
    action_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    action = await _get_owned_pending_action(db, action_id, user)
    action.status = JiraActionStatus.REJECTED
    action.decided_at = datetime.now(timezone.utc)
    action.decided_by_user_id = user.id
    await db.commit()
    return {"status": "rejected"}


@router.post("/actions/{action_id}/confirm")
async def confirm_action(
    action_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """The only code path in this backend that actually calls
    JiraClient.create_issue/update_issue. Reached only by an explicit human
    click on a proposal this same user staged -- never by the model, never
    automatically."""
    action = await _get_owned_pending_action(db, action_id, user)
    action.status = JiraActionStatus.CONFIRMED
    action.decided_at = datetime.now(timezone.utc)
    action.decided_by_user_id = user.id
    await db.commit()

    try:
        client = JiraClient()
    except JiraNotConfigured:
        action.status = JiraActionStatus.FAILED
        action.error_message = "Jira isn't configured"
        await db.commit()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Jira isn't configured") from None

    try:
        if action.action_type == JiraActionType.CREATE_ISSUE:
            result = await client.create_issue(
                project_key=action.payload_json["project_key"],
                summary=action.payload_json["summary"],
                description=action.payload_json["description"],
                issue_type=action.payload_json.get("issue_type", "Task"),
            )
        else:
            await client.update_issue(
                issue_key=action.payload_json["issue_key"],
                fields=action.payload_json["fields"],
            )
            result = {"issue_key": action.payload_json["issue_key"], "updated": True}
        action.status = JiraActionStatus.EXECUTED
        action.result_json = result
        action.executed_at = datetime.now(timezone.utc)
        await db.commit()
        return {"status": "executed", "result": result}
    except Exception as exc:
        action.status = JiraActionStatus.FAILED
        action.error_message = str(exc)
        await db.commit()
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Jira write failed: {exc}") from None
