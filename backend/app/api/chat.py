import uuid

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.chat_engine.service import ChatNotConfigured, ask
from app.db.models.user import User

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ProposedAction(BaseModel):
    id: uuid.UUID
    action_type: str
    preview_text: str


class ChatResponse(BaseModel):
    reply: str
    # Non-empty only when the model staged a Jira create/update this turn --
    # the frontend renders these as Confirm/Reject cards. Nothing in them has
    # been written to Jira yet.
    proposed_actions: list[ProposedAction] = []


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatResponse:
    try:
        reply, proposals = await ask(db, user, body.message)
    except ChatNotConfigured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Chat isn't configured (missing API key)"
        ) from None
    except anthropic.APIStatusError as exc:
        # Surfaces Claude API failures (low credit balance, rate limit, auth,
        # upstream outage) as a clean message instead of a raw 500 -- same
        # 502 pattern used for Jira/GitHub upstream failures elsewhere in
        # this API. exc.message is Anthropic's own human-readable string.
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Chat request failed: {exc.message}") from None
    return ChatResponse(
        reply=reply,
        proposed_actions=[
            ProposedAction(id=p.id, action_type=p.action_type.value, preview_text=p.preview_text)
            for p in proposals
        ],
    )
