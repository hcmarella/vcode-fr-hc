import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models.content import ContentKnowledge
from app.db.models.user import User
from app.schemas.content import KnowledgeResponse

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("", response_model=list[KnowledgeResponse])
async def list_knowledge(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[ContentKnowledge]:
    # Team-scoped by design -- every user, including admins, only sees their
    # own team's knowledge here. Cross-team visibility for admins is exposed
    # separately via /api/sync/flags, not by relaxing this filter.
    stmt = select(ContentKnowledge).where(ContentKnowledge.effective_team == user.team)
    stmt = stmt.order_by(ContentKnowledge.name)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge(
    knowledge_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContentKnowledge:
    entry = await db.get(ContentKnowledge, knowledge_id)
    if entry is None or entry.effective_team != user.team:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Knowledge entry not found")
    return entry
