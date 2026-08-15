from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models.sync import SyncRun, SyncRunStatus
from app.db.models.user import User
from app.schemas.sync import SyncRunResponse

# Separate from api/sync.py on purpose: that router requires admin (it exposes
# trigger + full flag detail). "When was this last synced and did it work" is
# harmless to show any authenticated user -- it's what the dashboard's
# freshness indicator reads, and gating it behind admin would mean regular
# users can't tell whether the content they're looking at is current.
router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.get("/status", response_model=SyncRunResponse | None)
async def sync_status(
    db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)
) -> SyncRun | None:
    stmt = (
        select(SyncRun)
        .where(SyncRun.status.in_([SyncRunStatus.SUCCESS, SyncRunStatus.FAILED]))
        .order_by(SyncRun.requested_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalars().first()
