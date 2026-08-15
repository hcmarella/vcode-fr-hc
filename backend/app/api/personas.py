from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models.content import ContentAgent
from app.schemas.content import AgentResponse

router = APIRouter(prefix="/api/personas", tags=["personas"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AgentResponse])
async def list_personas(db: AsyncSession = Depends(get_db)) -> list[ContentAgent]:
    stmt = select(ContentAgent).order_by(ContentAgent.name)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/{slug}", response_model=AgentResponse)
async def get_persona(slug: str, db: AsyncSession = Depends(get_db)) -> ContentAgent:
    stmt = select(ContentAgent).where(ContentAgent.slug == slug)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Persona not found")
    return agent
