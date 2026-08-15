import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, pg_enum, utcnow
from app.db.models.user import Team


class ContentStatus(str, enum.Enum):
    ACTIVE = "active"
    STALE = "stale"


class MemoryType(str, enum.Enum):
    USER = "user"
    FEEDBACK = "feedback"
    PROJECT = "project"
    REFERENCE = "reference"


class SyncedContentMixin(UUIDPrimaryKeyMixin, TimestampMixin):
    """Common columns for every content type mirrored from vcode-w-hc."""

    description: Mapped[str] = mapped_column(Text)
    body_markdown: Mapped[str] = mapped_column(Text)
    source_path: Mapped[str] = mapped_column(String)
    content_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[ContentStatus] = mapped_column(
        pg_enum(ContentStatus, "content_status_enum"), default=ContentStatus.ACTIVE
    )
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentAgent(SyncedContentMixin, Base):
    __tablename__ = "content_agents"

    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    tools_raw: Mapped[str] = mapped_column(Text)
    tools: Mapped[list[str]] = mapped_column(JSONB)
    model: Mapped[str] = mapped_column(String)


class ContentSkill(SyncedContentMixin, Base):
    __tablename__ = "content_skills"

    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)


class ContentCommand(SyncedContentMixin, Base):
    __tablename__ = "content_commands"

    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    argument_hint: Mapped[str | None] = mapped_column(String, nullable=True)


class ContentKnowledge(SyncedContentMixin, Base):
    __tablename__ = "content_knowledge"

    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    metadata_type: Mapped[MemoryType] = mapped_column(pg_enum(MemoryType, "memory_type_enum"))
    folder_team: Mapped[Team] = mapped_column(pg_enum(Team, "team_enum"))
    metadata_team: Mapped[Team] = mapped_column(pg_enum(Team, "team_enum"))
    effective_team: Mapped[Team] = mapped_column(pg_enum(Team, "team_enum"), index=True)
    team_mismatch: Mapped[bool] = mapped_column(Boolean, default=False)


class ContentAbout(SyncedContentMixin, Base):
    __tablename__ = "content_about"

    slug: Mapped[str] = mapped_column(String, unique=True, default="root")
