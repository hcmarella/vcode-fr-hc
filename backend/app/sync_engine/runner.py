import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.sync import SyncRun, SyncRunStatus, SyncTrigger
from app.sync_engine.source import clone_or_pull
from app.sync_engine.upsert import (
    sync_about,
    sync_agents,
    sync_commands,
    sync_knowledge,
    sync_skills,
)
from app.sync_engine.walker import walk_source


class SyncAlreadyInProgress(Exception):
    """Raised when a pending/running SyncRun already exists for this source+ref.

    Not an error condition -- webhook redeliveries and rapid successive pushes
    are expected to hit this. Callers should treat it as a no-op, not a 500.
    """

    def __init__(self, existing_run: SyncRun):
        self.existing_run = existing_run
        super().__init__(f"Sync already in progress: {existing_run.id}")


async def create_pending_run(
    session: AsyncSession,
    source: str,
    ref: str | None,
    trigger: SyncTrigger,
    triggered_by_user_id: uuid.UUID | None = None,
) -> SyncRun:
    """Insert a PENDING SyncRun row. Raises SyncAlreadyInProgress instead of
    creating a duplicate if one is already pending/running for source+ref --
    enforced by the DB-level partial unique index (see db/models/sync.py), so
    it's race-safe across concurrent requests and multiple API replicas."""
    now = datetime.now(timezone.utc)
    run = SyncRun(
        id=uuid.uuid4(),
        requested_at=now,
        status=SyncRunStatus.PENDING,
        trigger=trigger,
        triggered_by_user_id=triggered_by_user_id,
        source=source,
        ref=ref,
        source_ref=f"{source}@{ref}" if ref else source,
        counts_json={},
    )
    session.add(run)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = await _find_active_run(session, source, ref)
        if existing is not None:
            raise SyncAlreadyInProgress(existing) from None
        raise  # some other integrity error -- don't swallow it
    return run


async def _find_active_run(session: AsyncSession, source: str, ref: str | None) -> SyncRun | None:
    stmt = select(SyncRun).where(
        SyncRun.source == source,
        SyncRun.ref == ref,
        SyncRun.status.in_([SyncRunStatus.PENDING, SyncRunStatus.RUNNING]),
    )
    return (await session.execute(stmt)).scalars().first()


async def claim_run(session: AsyncSession, run: SyncRun) -> None:
    """Flip an already-known PENDING run to RUNNING. Used by the synchronous
    (admin-click) path, which just created the row itself in the same request
    -- no contention to guard against, so no row locking needed here."""
    run.status = SyncRunStatus.RUNNING
    run.started_at = datetime.now(timezone.utc)
    await session.commit()


async def claim_next_pending(session: AsyncSession) -> SyncRun | None:
    """Atomically claim the oldest PENDING run for the Postgres-poll worker.

    FOR UPDATE SKIP LOCKED is what makes this safe with multiple worker
    replicas polling concurrently: a row locked by one worker's in-flight
    transaction is invisible to everyone else's claim query rather than
    blocking on it, so N workers polling the same table never claim the same
    row twice and never queue up waiting on each other's locks.
    """
    stmt = (
        select(SyncRun)
        .where(SyncRun.status == SyncRunStatus.PENDING)
        .order_by(SyncRun.requested_at)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    run = (await session.execute(stmt)).scalars().first()
    if run is None:
        return None
    run.status = SyncRunStatus.RUNNING
    run.started_at = datetime.now(timezone.utc)
    await session.commit()
    return run


async def execute_run(session: AsyncSession, run: SyncRun, scratch_dir: Path) -> SyncRun:
    """Do the actual clone/parse/upsert work. Assumes `run` is already RUNNING
    (via claim_run or claim_next_pending) -- this function only handles the
    SUCCESS/FAILED transition, not the PENDING->RUNNING one, so it behaves
    identically whether called from the synchronous admin-click path or the
    async worker."""
    try:
        repo_root, commit_sha = clone_or_pull(run.source, run.ref, scratch_dir)
        run.source_commit_sha = commit_sha
        walked = walk_source(repo_root)

        counts = {
            "agents": await sync_agents(session, walked.agents, repo_root, run.started_at, run.id),
            "skills": await sync_skills(session, walked.skills, repo_root, run.started_at, run.id),
            "commands": await sync_commands(
                session, walked.commands, repo_root, run.started_at, run.id
            ),
            "knowledge": await sync_knowledge(
                session, walked.knowledge, repo_root, run.started_at, run.id
            ),
            "about": await sync_about(session, walked.about, repo_root, run.started_at),
        }
        run.counts_json = counts
        run.status = SyncRunStatus.SUCCESS
    except Exception as exc:
        run.status = SyncRunStatus.FAILED
        run.error_message = str(exc)
        raise
    finally:
        run.finished_at = datetime.now(timezone.utc)
        await session.commit()

    return run


async def run_sync(
    session: AsyncSession,
    source: str,
    ref: str | None,
    scratch_dir: Path,
    triggered_by_user_id: uuid.UUID | None = None,
) -> SyncRun:
    """Synchronous end-to-end sync: create + claim + execute in one call. Used
    by the admin-click API route and the manual CLI script, where a human is
    waiting on the result. Webhook-triggered syncs use create_pending_run()
    alone and let the worker claim + execute asynchronously instead -- see
    app/api/webhooks.py and app/workers/sync_worker.py."""
    run = await create_pending_run(session, source, ref, SyncTrigger.MANUAL, triggered_by_user_id)
    await claim_run(session, run)
    return await execute_run(session, run, scratch_dir)
