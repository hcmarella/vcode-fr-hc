from pydantic import BaseModel, ConfigDict, Field

from app.db.models.content import MemoryType
from app.db.models.user import Team


class AgentFrontmatter(BaseModel):
    name: str
    description: str
    tools: str
    model: str


class SkillFrontmatter(BaseModel):
    name: str
    description: str


class CommandFrontmatter(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    description: str
    argument_hint: str | None = Field(default=None, alias="argument-hint")


class KnowledgeMetadata(BaseModel):
    type: MemoryType
    team: Team


class KnowledgeFrontmatter(BaseModel):
    name: str
    description: str
    metadata: KnowledgeMetadata
