import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import UUIDPrimaryKeyMixin, pg_enum


class SyncRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class SyncTrigger(str, enum.Enum):
    MANUAL = "manual"
    WEBHOOK = "webhook"


class SyncFlagType(str, enum.Enum):
    TEAM_MISMATCH = "team_mismatch"
    PARSE_ERROR = "parse_error"
    OTHER = "other"


class SyncContentType(str, enum.Enum):
    AGENT = "agent"
    SKILL = "skill"
    COMMAND = "command"
    KNOWLEDGE = "knowledge"
    ABOUT = "about"


class SyncRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "sync_runs"

    # requested_at is set the instant the row is created (webhook receipt or
    # admin click); started_at is set when a worker actually claims and begins
    # executing it. They diverge under queue backlog -- that gap is the number
    # you'd alert on if sync latency ever becomes a problem.
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[SyncRunStatus] = mapped_column(
        pg_enum(SyncRunStatus, "sync_run_status_enum")
    )
    trigger: Mapped[SyncTrigger] = mapped_column(pg_enum(SyncTrigger, "sync_trigger_enum"))
    triggered_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    # Raw source/ref, used by the worker to actually run clone_or_pull.
    # Kept separate from source_ref (below) because git SSH URLs contain '@'
    # themselves (git@github.com:org/repo.git), making a combined string lossy
    # to parse back apart.
    source: Mapped[str] = mapped_column(String)
    ref: Mapped[str | None] = mapped_column(String, nullable=True)
    source_ref: Mapped[str] = mapped_column(String)
    source_commit_sha: Mapped[str | None] = mapped_column(String, nullable=True)
    counts_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        # Debounce at the database level, not in application code -- this is
        # what actually makes concurrent webhook deliveries and multiple API
        # replicas safe. Two requests racing to enqueue a sync for the same
        # source+ref will have one succeed and one hit a unique violation,
        # which the API/webhook layer catches and treats as "already queued"
        # rather than a real error.
        # ref uses COALESCE(ref, '') because Postgres treats NULL <> NULL in
        # unique indexes -- without it, two ref-less runs on the same source
        # wouldn't collide and the debounce would silently not apply to them.
        Index(
            "uq_sync_runs_active_source_ref",
            "source",
            text("COALESCE(ref, '')"),
            unique=True,
            postgresql_where=text("status IN ('pending', 'running')"),
        ),
    )


class SyncRunFlag(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "sync_run_flags"

    sync_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sync_runs.id"))
    flag_type: Mapped[SyncFlagType] = mapped_column(pg_enum(SyncFlagType, "sync_flag_type_enum"))
    source_path: Mapped[str] = mapped_column(String)
    content_type: Mapped[SyncContentType] = mapped_column(
        pg_enum(SyncContentType, "sync_content_type_enum")
    )
    details_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
