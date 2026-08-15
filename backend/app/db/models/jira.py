import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import UUIDPrimaryKeyMixin, pg_enum, utcnow


class JiraActionType(str, enum.Enum):
    CREATE_ISSUE = "create_issue"
    UPDATE_ISSUE = "update_issue"


class JiraActionStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"  # human approved; execution is about to run or already ran
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


class JiraActionRequest(UUIDPrimaryKeyMixin, Base):
    """A staged Jira write, created by chat tool-use or a UI button, that sits
    at PENDING until a human confirms or rejects it. Nothing in this repo
    calls JiraClient.create_issue/update_issue except the confirm endpoint
    (app/api/jira_actions.py) acting on a row already in this table -- the
    model or a button click can never reach Jira's write API directly."""

    __tablename__ = "jira_action_requests"

    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    action_type: Mapped[JiraActionType] = mapped_column(
        pg_enum(JiraActionType, "jira_action_type_enum")
    )
    payload_json: Mapped[dict] = mapped_column(JSONB)
    preview_text: Mapped[str] = mapped_column(Text)
    status: Mapped[JiraActionStatus] = mapped_column(
        pg_enum(JiraActionStatus, "jira_action_status_enum"),
        default=JiraActionStatus.PENDING,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
