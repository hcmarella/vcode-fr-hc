import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, pg_enum, utcnow


class Team(str, enum.Enum):
    ENGINEERING = "engineering"
    PRODUCT = "product"
    QA = "qa"
    DOCS = "docs"


class Role(str, enum.Enum):
    # Mirrors the Developer/Business/Infra(->Manager)/Admin permission table
    # referenced in the FORGE architecture docs -- what each role can *do*
    # (Jira write, admin/sync tools) is enforced server-side in
    # app/api/deps.py and app/chat_engine/service.py, not just hidden in the
    # UI. Manager stands in for the "Infra (Phase 2)" row: a rollup/overview
    # role rather than a hands-on one.
    DEVELOPER = "developer"
    BUSINESS = "business"
    MANAGER = "manager"
    ADMIN = "admin"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    team: Mapped[Team] = mapped_column(pg_enum(Team, "team_enum"))
    role: Mapped[Role] = mapped_column(pg_enum(Role, "role_enum"), default=Role.DEVELOPER)


class UserLimits(Base):
    __tablename__ = "user_limits"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    max_sessions_per_day: Mapped[int] = mapped_column(default=10)
    max_tokens_per_day: Mapped[int] = mapped_column(default=2_000_000)


class AuthSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "auth_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
