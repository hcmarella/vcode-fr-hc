import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import UUIDPrimaryKeyMixin, pg_enum


class SyncRunStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


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

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[SyncRunStatus] = mapped_column(
        pg_enum(SyncRunStatus, "sync_run_status_enum")
    )
    triggered_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    source_ref: Mapped[str] = mapped_column(String)
    source_commit_sha: Mapped[str | None] = mapped_column(String, nullable=True)
    counts_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


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
