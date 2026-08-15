from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.db.models.user import AuthSession, Role, User, UserLimits
from app.schemas.user import LoginRequest, SignupRequest, UserResponse
from app.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.session_ttl_hours * 3600,
    )


async def _create_session(db: AsyncSession, user: User, response: Response) -> None:
    settings = get_settings()
    token = generate_session_token()
    now = datetime.now(timezone.utc)
    db.add(AuthSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        created_at=now,
        expires_at=now + timedelta(hours=settings.session_ttl_hours),
    ))
    await db.commit()
    _set_session_cookie(response, token)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest, response: Response, db: AsyncSession = Depends(get_db)) -> User:
    existing = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    if body.role == Role.ADMIN:
        # Belt and suspenders alongside the schema default -- a client could
        # still send role=admin directly in the request body, so reject it
        # here regardless of what the schema allows.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot self-assign the admin role")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        team=body.team,
        role=body.role,
    )
    db.add(user)
    await db.flush()
    db.add(UserLimits(user_id=user.id))
    await db.commit()
    await db.refresh(user)

    await _create_session(db, user, response)
    return user


@router.post("/login", response_model=UserResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)) -> User:
    user = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    await _create_session(db, user, response)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    portal_session: str | None = Cookie(default=None),
) -> None:
    settings = get_settings()
    if portal_session is not None:
        token_hash = hash_session_token(portal_session)
        stmt = select(AuthSession).where(
            AuthSession.user_id == user.id, AuthSession.token_hash == token_hash
        )
        auth_session = (await db.execute(stmt)).scalar_one_or_none()
        if auth_session is not None and auth_session.revoked_at is None:
            auth_session.revoked_at = datetime.now(timezone.utc)
            await db.commit()
    response.delete_cookie(settings.session_cookie_name)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> User:
    return user
