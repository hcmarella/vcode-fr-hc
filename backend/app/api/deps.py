from datetime import datetime, timezone

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.base import get_db
from app.db.models.user import AuthSession, Role, User
from app.security import hash_session_token


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    portal_session: str | None = Cookie(default=None),
) -> User:
    settings = get_settings()
    if portal_session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    token_hash = hash_session_token(portal_session)
    stmt = select(AuthSession).where(AuthSession.token_hash == token_hash)
    auth_session = (await db.execute(stmt)).scalar_one_or_none()

    if auth_session is None or auth_session.revoked_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session")

    now = datetime.now(timezone.utc)
    if auth_session.expires_at < now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired")

    user = await db.get(User, auth_session.user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session")

    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user


async def require_jira_write(user: User = Depends(get_current_user)) -> User:
    """Gate for anything that reaches Jira's write API. Business/Manager are
    view-only for Jira per the Developer/Business/Infra/Admin permission
    table this app's role model mirrors -- enforced here, not just hidden in
    the UI, and also in chat_engine.service.ask() which doesn't even offer
    the model propose_* tools for these roles."""
    if user.role not in (Role.DEVELOPER, Role.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Developer or admin access required")
    return user
