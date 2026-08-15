from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.config import get_settings
from app.db.models.sync import SyncRun, SyncRunFlag
from app.db.models.user import User
from app.schemas.sync import SyncRunFlagResponse, SyncRunRequest, SyncRunResponse
from app.sync_engine.runner import SyncAlreadyInProgress, run_sync

router = APIRouter(prefix="/api/sync", tags=["sync"], dependencies=[Depends(require_admin)])


@router.post("/run", response_model=SyncRunResponse)
async def trigger_sync(
    body: SyncRunRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> SyncRun:
    settings = get_settings()
    try:
        return await run_sync(db, body.source, body.ref, Path(settings.sync_scratch_dir), user.id)
    except SyncAlreadyInProgress as exc:
        # A webhook-triggered sync for this same source+ref is already
        # pending/running -- surface it instead of racing a second one.
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Sync already in progress (run {exc.existing_run.id}, status "
            f"{exc.existing_run.status.value})",
        ) from None


@router.get("/runs", response_model=list[SyncRunResponse])
async def list_sync_runs(db: AsyncSession = Depends(get_db)) -> list[SyncRun]:
    stmt = select(SyncRun).order_by(SyncRun.started_at.desc()).limit(50)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/flags", response_model=list[SyncRunFlagResponse])
async def list_sync_flags(db: AsyncSession = Depends(get_db)) -> list[SyncRunFlag]:
    stmt = select(SyncRunFlag).order_by(SyncRunFlag.created_at.desc()).limit(200)
    return list((await db.execute(stmt)).scalars().all())
