import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import UUIDPrimaryKeyMixin, pg_enum, utcnow


class ContainerStatus(str, enum.Enum):
    PROVISIONING = "provisioning"
    CLONING = "cloning"
    READY = "ready"
    RUNNING = "running"
    IDLE = "idle"
    ERROR = "error"
    TERMINATED = "terminated"


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    ENDED = "ended"
    ERROR = "error"
    TIMED_OUT = "timed_out"
    LIMIT_REACHED = "limit_reached"


class InvocationSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "invocation_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    persona_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_agents.id")
    )

    # Snapshotted at session start so a later persona edit never changes an in-flight
    # or historical session's behavior.
    persona_name: Mapped[str] = mapped_column(String)
    persona_tools: Mapped[list[str]] = mapped_column(JSONB)
    persona_model: Mapped[str] = mapped_column(String)
    persona_system_prompt: Mapped[str] = mapped_column(Text)

    repo_url: Mapped[str] = mapped_column(String)
    repo_branch: Mapped[str | None] = mapped_column(String, nullable=True)

    container_id: Mapped[str | None] = mapped_column(String, nullable=True)
    container_status: Mapped[ContainerStatus] = mapped_column(
        pg_enum(ContainerStatus, "container_status_enum"), default=ContainerStatus.PROVISIONING
    )
    status: Mapped[SessionStatus] = mapped_column(
        pg_enum(SessionStatus, "session_status_enum"), default=SessionStatus.ACTIVE
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    idle_timeout_seconds: Mapped[int] = mapped_column(Integer, default=900)
    wall_clock_limit_seconds: Mapped[int] = mapped_column(Integer, default=7200)

    total_input_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    total_output_tokens: Mapped[int] = mapped_column(BigInteger, default=0)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageContentType(str, enum.Enum):
    TEXT = "text"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"


class ChatMessage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invocation_sessions.id"), index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer)
    role: Mapped[MessageRole] = mapped_column(pg_enum(MessageRole, "message_role_enum"))
    content_type: Mapped[MessageContentType] = mapped_column(
        pg_enum(MessageContentType, "message_content_type_enum")
    )
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_input_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tool_use_id: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_result_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_error: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ToolCallAuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "tool_call_audit_log"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invocation_sessions.id"), index=True
    )
    chat_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=True
    )
    tool_name: Mapped[str] = mapped_column(String)
    tool_input_json: Mapped[dict] = mapped_column(JSONB)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    duration_ms: Mapped[int] = mapped_column(Integer)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stdout_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    truncated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_error: Mapped[bool] = mapped_column(Boolean, default=False)
    container_id: Mapped[str | None] = mapped_column(String, nullable=True)
