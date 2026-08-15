import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.content import (
    ContentAbout,
    ContentAgent,
    ContentCommand,
    ContentKnowledge,
    ContentSkill,
    ContentStatus,
)
from app.db.models.sync import SyncContentType, SyncFlagType, SyncRunFlag
from app.db.models.user import Team
from app.sync_engine.parser import (
    ParseError,
    ParsedFile,
    parse_about,
    parse_agent,
    parse_command,
    parse_knowledge,
    parse_skill,
)
from app.sync_engine.walker import WalkResult


def _slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "-")


async def _upsert_row(
    session: AsyncSession, model_cls, key_field: str, key_value: str, parsed: ParsedFile, extra: dict, now: datetime
):
    stmt = select(model_cls).where(getattr(model_cls, key_field) == key_value)
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing is None:
        row = model_cls(
            **{key_field: key_value},
            description=parsed.frontmatter.description if hasattr(parsed.frontmatter, "description") else "",
            body_markdown=parsed.body_markdown,
            source_path=parsed.source_path,
            content_hash=parsed.content_hash,
            status=ContentStatus.ACTIVE,
            first_seen_at=now,
            last_seen_at=now,
            **extra,
        )
        session.add(row)
        return row, "inserted"

    existing.last_seen_at = now
    existing.status = ContentStatus.ACTIVE
    if existing.content_hash != parsed.content_hash:
        existing.description = getattr(parsed.frontmatter, "description", existing.description)
        existing.body_markdown = parsed.body_markdown
        existing.source_path = parsed.source_path
        existing.content_hash = parsed.content_hash
        for field, value in extra.items():
            setattr(existing, field, value)
        return existing, "updated"

    return existing, "unchanged"


async def _mark_stale(session: AsyncSession, model_cls, seen_paths: set[str]) -> int:
    stmt = select(model_cls).where(model_cls.status == ContentStatus.ACTIVE)
    rows = (await session.execute(stmt)).scalars().all()
    count = 0
    for row in rows:
        if row.source_path not in seen_paths:
            row.status = ContentStatus.STALE
            count += 1
    return count


async def sync_agents(
    session: AsyncSession, paths: list[Path], repo_root: Path, now: datetime, sync_run_id: uuid.UUID
) -> dict:
    counts = {"inserted": 0, "updated": 0, "unchanged": 0, "errors": 0}
    seen_paths: set[str] = set()
    for path in paths:
        try:
            parsed = parse_agent(path, repo_root)
        except ParseError as exc:
            counts["errors"] += 1
            await _log_parse_error(session, exc, SyncContentType.AGENT, sync_run_id, now)
            continue
        seen_paths.add(parsed.source_path)
        fm = parsed.frontmatter
        tools = [t.strip() for t in fm.tools.split(",") if t.strip()]
        _, action = await _upsert_row(
            session, ContentAgent, "name", fm.name, parsed, now=now,
            extra={"slug": _slugify(fm.name), "tools_raw": fm.tools, "tools": tools, "model": fm.model},
        )
        counts[action] += 1
    counts["stale"] = await _mark_stale(session, ContentAgent, seen_paths)
    return counts


async def sync_skills(
    session: AsyncSession, paths: list[Path], repo_root: Path, now: datetime, sync_run_id: uuid.UUID
) -> dict:
    counts = {"inserted": 0, "updated": 0, "unchanged": 0, "errors": 0}
    seen_paths: set[str] = set()
    for path in paths:
        try:
            parsed = parse_skill(path, repo_root)
        except ParseError as exc:
            counts["errors"] += 1
            await _log_parse_error(session, exc, SyncContentType.SKILL, sync_run_id, now)
            continue
        seen_paths.add(parsed.source_path)
        fm = parsed.frontmatter
        _, action = await _upsert_row(
            session, ContentSkill, "name", fm.name, parsed, now=now,
            extra={"slug": _slugify(fm.name)},
        )
        counts[action] += 1
    counts["stale"] = await _mark_stale(session, ContentSkill, seen_paths)
    return counts


async def sync_commands(
    session: AsyncSession, paths: list[Path], repo_root: Path, now: datetime, sync_run_id: uuid.UUID
) -> dict:
    counts = {"inserted": 0, "updated": 0, "unchanged": 0, "errors": 0}
    seen_paths: set[str] = set()
    for path in paths:
        try:
            parsed = parse_command(path, repo_root)
        except ParseError as exc:
            counts["errors"] += 1
            await _log_parse_error(session, exc, SyncContentType.COMMAND, sync_run_id, now)
            continue
        seen_paths.add(parsed.source_path)
        fm = parsed.frontmatter
        slug = _slugify(path.stem)
        _, action = await _upsert_row(
            session, ContentCommand, "slug", slug, parsed, now=now,
            extra={"argument_hint": fm.argument_hint},
        )
        counts[action] += 1
    counts["stale"] = await _mark_stale(session, ContentCommand, seen_paths)
    return counts


async def sync_knowledge(
    session: AsyncSession, paths: list[Path], repo_root: Path, now: datetime, sync_run_id: uuid.UUID
) -> dict:
    counts = {"inserted": 0, "updated": 0, "unchanged": 0, "errors": 0}
    seen_paths: set[str] = set()
    memory_root = repo_root / "memory"
    for path in paths:
        try:
            parsed = parse_knowledge(path, repo_root)
        except ParseError as exc:
            counts["errors"] += 1
            await _log_parse_error(session, exc, SyncContentType.KNOWLEDGE, sync_run_id, now)
            continue
        seen_paths.add(parsed.source_path)
        fm = parsed.frontmatter

        folder_team_raw = path.relative_to(memory_root).parts[0]
        try:
            folder_team = Team(folder_team_raw)
        except ValueError:
            counts["errors"] += 1
            await _log_parse_error(
                session,
                ParseError(parsed.source_path, f"unrecognized team folder '{folder_team_raw}'"),
                SyncContentType.KNOWLEDGE,
                sync_run_id,
                now,
            )
            continue

        metadata_team = fm.metadata.team
        mismatch = folder_team != metadata_team
        if mismatch:
            session.add(SyncRunFlag(
                sync_run_id=sync_run_id,
                flag_type=SyncFlagType.TEAM_MISMATCH,
                source_path=parsed.source_path,
                content_type=SyncContentType.KNOWLEDGE,
                details_json={
                    "name": fm.name,
                    "folder_team": folder_team.value,
                    "metadata_team": metadata_team.value,
                },
                created_at=now,
            ))

        _, action = await _upsert_row(
            session, ContentKnowledge, "name", fm.name, parsed, now=now,
            extra={
                "metadata_type": fm.metadata.type,
                "folder_team": folder_team,
                "metadata_team": metadata_team,
                "effective_team": folder_team,
                "team_mismatch": mismatch,
            },
        )
        counts[action] += 1
    counts["stale"] = await _mark_stale(session, ContentKnowledge, seen_paths)
    return counts


async def sync_about(session: AsyncSession, about_path: Path | None, repo_root: Path, now: datetime) -> dict:
    if about_path is None:
        return {"inserted": 0, "updated": 0, "unchanged": 0, "errors": 1}
    parsed = parse_about(about_path, repo_root)
    stmt = select(ContentAbout).where(ContentAbout.slug == "root")
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is None:
        session.add(ContentAbout(
            slug="root", description="", body_markdown=parsed.body_markdown,
            source_path=parsed.source_path, content_hash=parsed.content_hash,
            status=ContentStatus.ACTIVE, first_seen_at=now, last_seen_at=now,
        ))
        return {"inserted": 1, "updated": 0, "unchanged": 0, "errors": 0}
    existing.last_seen_at = now
    existing.status = ContentStatus.ACTIVE
    if existing.content_hash != parsed.content_hash:
        existing.body_markdown = parsed.body_markdown
        existing.content_hash = parsed.content_hash
        return {"inserted": 0, "updated": 1, "unchanged": 0, "errors": 0}
    return {"inserted": 0, "updated": 0, "unchanged": 1, "errors": 0}


async def _log_parse_error(
    session: AsyncSession,
    exc: ParseError,
    content_type: SyncContentType,
    sync_run_id: uuid.UUID,
    now: datetime,
) -> None:
    session.add(SyncRunFlag(
        sync_run_id=sync_run_id,
        flag_type=SyncFlagType.PARSE_ERROR,
        source_path=exc.source_path,
        content_type=content_type,
        details_json={"reason": exc.reason},
        created_at=now,
    ))
