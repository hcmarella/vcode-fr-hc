import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import get_settings
from app.db.models.sync import SyncTrigger
from app.sync_engine.queue import get_sync_queue
from app.sync_engine.runner import SyncAlreadyInProgress, create_pending_run

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


def _verify_signature(secret: str, payload: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    provided = signature_header.removeprefix("sha256=")
    # constant-time compare -- a naive == here would leak timing info an
    # attacker could use to forge a valid signature byte-by-byte.
    return hmac.compare_digest(expected, provided)


@router.post("/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
) -> dict:
    settings = get_settings()
    if not settings.github_webhook_secret:
        # Fail closed: an unconfigured secret must not silently accept
        # unsigned requests.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Webhook not configured")

    raw_body = await request.body()
    if not _verify_signature(settings.github_webhook_secret, raw_body, x_hub_signature_256):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid signature")

    if x_github_event == "ping":
        # Sent once when the webhook is first created in GitHub's UI/API.
        return {"status": "pong"}

    if x_github_event != "push":
        return {"status": "ignored", "reason": f"unhandled event type: {x_github_event}"}

    payload = await request.json()
    repo_full_name = payload.get("repository", {}).get("full_name", "")
    ref = payload.get("ref", "")  # e.g. "refs/heads/main"
    branch = ref.removeprefix("refs/heads/")

    if repo_full_name != settings.sync_allowed_source_repo:
        logger.warning("Webhook push from unexpected repo: %s", repo_full_name)
        return {"status": "ignored", "reason": "repository not configured for sync"}

    if branch != settings.sync_source_ref:
        return {"status": "ignored", "reason": f"branch {branch!r} is not the sync source ref"}

    try:
        run = await create_pending_run(
            db, settings.sync_source_url, settings.sync_source_ref, SyncTrigger.WEBHOOK
        )
    except SyncAlreadyInProgress as exc:
        # Expected under rapid pushes or GitHub redelivering the same
        # delivery -- not an error, just "nothing new to do."
        return {"status": "already_in_progress", "sync_run_id": str(exc.existing_run.id)}

    await get_sync_queue().enqueue(run.id)
    return {"status": "queued", "sync_run_id": str(run.id)}
