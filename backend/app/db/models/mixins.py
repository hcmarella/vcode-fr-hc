import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def pg_enum(enum_cls: type[enum.Enum], name: str) -> SAEnum:
    """Store the enum member's .value (e.g. "engineering"), not its .name
    (e.g. "ENGINEERING") -- SQLAlchemy defaults to .name, which would silently
    diverge from the lowercase string values used in vcode-w-hc frontmatter
    and in every raw/API-level query against these columns."""
    return SAEnum(enum_cls, name=name, values_callable=lambda obj: [e.value for e in obj])


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
