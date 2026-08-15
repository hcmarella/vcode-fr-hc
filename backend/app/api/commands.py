from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models.content import ContentCommand
from app.schemas.content import CommandResponse

router = APIRouter(prefix="/api/commands", tags=["commands"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[CommandResponse])
async def list_commands(db: AsyncSession = Depends(get_db)) -> list[ContentCommand]:
    stmt = select(ContentCommand).order_by(ContentCommand.slug)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/{slug}", response_model=CommandResponse)
async def get_command(slug: str, db: AsyncSession = Depends(get_db)) -> ContentCommand:
    stmt = select(ContentCommand).where(ContentCommand.slug == slug)
    command = (await db.execute(stmt)).scalar_one_or_none()
    if command is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Command not found")
    return command
