"""Illustrative "value delivered" panel for the Home dashboard. Counts real
rows this portal itself created (Jira proposals drafted, AI-assisted chat
sessions, syncs run) and multiplies by a documented per-task time estimate
-- these are assumptions, not measured task durations, and the API response
carries the assumptions back to the client so the number is never presented
as more precise than it is.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.db.models.jira import JiraActionRequest
from app.db.models.session import InvocationSession
from app.db.models.sync import SyncRun, SyncRunStatus
from app.db.models.user import User

router = APIRouter(prefix="/api/roi", tags=["roi"])

# Minutes saved per unit, vs. doing the task by hand with no AI assistance.
# Illustrative defaults -- there's no ground truth for "how long would this
# have taken a human," so these are round, defensible estimates a team can
# argue with and override (see ROI_HOURLY_RATE_USD in .env for the dollar
# side of the same caveat).
_MINUTES_SAVED_PER_JIRA_TICKET = 15
_MINUTES_SAVED_PER_DOC_SESSION = 25
_MINUTES_SAVED_PER_REVIEW_SESSION = 20
_MINUTES_SAVED_PER_SYNC_RUN = 5

_DOC_PERSONA_NAMES = ("docs-writer",)
_REVIEW_PERSONA_NAMES = ("engineer", "qa-engineer")


@router.get("/stats")
async def stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    jira_tickets_drafted = (
        await db.execute(select(func.count()).select_from(JiraActionRequest))
    ).scalar_one()

    doc_sessions = (
        await db.execute(
            select(func.count())
            .select_from(InvocationSession)
            .where(InvocationSession.persona_name.in_(_DOC_PERSONA_NAMES))
        )
    ).scalar_one()

    review_sessions = (
        await db.execute(
            select(func.count())
            .select_from(InvocationSession)
            .where(InvocationSession.persona_name.in_(_REVIEW_PERSONA_NAMES))
        )
    ).scalar_one()

    successful_syncs = (
        await db.execute(
            select(func.count())
            .select_from(SyncRun)
            .where(SyncRun.status == SyncRunStatus.SUCCESS)
        )
    ).scalar_one()

    breakdown = [
        {
            "label": "Jira tickets drafted",
            "count": jira_tickets_drafted,
            "minutes_per_unit": _MINUTES_SAVED_PER_JIRA_TICKET,
        },
        {
            "label": "Docs/knowledge sessions",
            "count": doc_sessions,
            "minutes_per_unit": _MINUTES_SAVED_PER_DOC_SESSION,
        },
        {
            "label": "Engineering & QA review sessions",
            "count": review_sessions,
            "minutes_per_unit": _MINUTES_SAVED_PER_REVIEW_SESSION,
        },
        {
            "label": "Content syncs run",
            "count": successful_syncs,
            "minutes_per_unit": _MINUTES_SAVED_PER_SYNC_RUN,
        },
    ]

    total_minutes = sum(item["count"] * item["minutes_per_unit"] for item in breakdown)
    hourly_rate = get_settings().roi_hourly_rate_usd

    return {
        "breakdown": breakdown,
        "total_minutes_saved": total_minutes,
        "total_hours_saved": round(total_minutes / 60, 1),
        "hourly_rate_usd": hourly_rate,
        "total_value_usd": round((total_minutes / 60) * hourly_rate, 2),
    }
