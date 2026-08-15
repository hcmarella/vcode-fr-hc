import uuid
from datetime import datetime

from pydantic import BaseModel

from app.db.models.content import ContentStatus, MemoryType
from app.db.models.user import Team


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str
    tools: list[str]
    model: str
    body_markdown: str
    status: ContentStatus
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str
    body_markdown: str
    status: ContentStatus
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommandResponse(BaseModel):
    id: uuid.UUID
    slug: str
    description: str
    argument_hint: str | None
    body_markdown: str
    status: ContentStatus
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    metadata_type: MemoryType
    effective_team: Team
    team_mismatch: bool
    body_markdown: str
    status: ContentStatus
    updated_at: datetime

    model_config = {"from_attributes": True}


class AboutResponse(BaseModel):
    body_markdown: str
    updated_at: datetime

    model_config = {"from_attributes": True}
