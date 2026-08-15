from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models.content import ContentAbout
from app.schemas.content import AboutResponse

router = APIRouter(prefix="/api/about", tags=["about"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=AboutResponse)
async def get_about(db: AsyncSession = Depends(get_db)) -> ContentAbout:
    stmt = select(ContentAbout).where(ContentAbout.slug == "root")
    about = (await db.execute(stmt)).scalar_one_or_none()
    if about is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "About content not synced yet")
    return about
