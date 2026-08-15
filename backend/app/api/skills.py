from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models.content import ContentSkill
from app.schemas.content import SkillResponse

router = APIRouter(prefix="/api/skills", tags=["skills"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[SkillResponse])
async def list_skills(db: AsyncSession = Depends(get_db)) -> list[ContentSkill]:
    stmt = select(ContentSkill).order_by(ContentSkill.name)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/{slug}", response_model=SkillResponse)
async def get_skill(slug: str, db: AsyncSession = Depends(get_db)) -> ContentSkill:
    stmt = select(ContentSkill).where(ContentSkill.slug == slug)
    skill = (await db.execute(stmt)).scalar_one_or_none()
    if skill is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Skill not found")
    return skill
