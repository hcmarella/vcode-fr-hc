import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.sync import SyncRun, SyncRunStatus
from app.sync_engine.source import clone_or_pull
from app.sync_engine.upsert import (
    sync_about,
    sync_agents,
    sync_commands,
    sync_knowledge,
    sync_skills,
)
from app.sync_engine.walker import walk_source


async def run_sync(
    session: AsyncSession,
    source: str,
    ref: str | None,
    scratch_dir: Path,
    triggered_by_user_id: uuid.UUID | None = None,
) -> SyncRun:
    now = datetime.now(timezone.utc)
    run = SyncRun(
        id=uuid.uuid4(),
        started_at=now,
        status=SyncRunStatus.RUNNING,
        triggered_by_user_id=triggered_by_user_id,
        source_ref=f"{source}@{ref}" if ref else source,
        counts_json={},
    )
    session.add(run)
    await session.flush()  # assigns run.id for use as FK in flag rows below

    try:
        repo_root, commit_sha = clone_or_pull(source, ref, scratch_dir)
        run.source_commit_sha = commit_sha
        walked = walk_source(repo_root)

        counts = {
            "agents": await sync_agents(session, walked.agents, repo_root, now, run.id),
            "skills": await sync_skills(session, walked.skills, repo_root, now, run.id),
            "commands": await sync_commands(session, walked.commands, repo_root, now, run.id),
            "knowledge": await sync_knowledge(session, walked.knowledge, repo_root, now, run.id),
            "about": await sync_about(session, walked.about, repo_root, now),
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
