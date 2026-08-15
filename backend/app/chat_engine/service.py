""""Ask" chat: a stateless, single-turn Q&A endpoint grounded in whatever this
portal has already synced (personas/skills/commands + the user's team
knowledge). Deliberately NOT the sandboxed, per-repo persona session engine
implied by db/models/session.py (InvocationSession/ChatMessage) and the empty
app/sandbox_engine/ package -- that's a much larger, security-sensitive
feature (provisioning a container per session, cloning arbitrary repos into
it, executing agent tool calls inside) that deserves its own dedicated build
rather than being bolted on here. This module answers "what does the
pr-review skill do", not "go modify a repo for me".
"""

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models.content import ContentAgent, ContentCommand, ContentKnowledge, ContentSkill
from app.db.models.content import ContentStatus
from app.db.models.user import Team

MAX_CONTEXT_CHARS = 12_000  # keeps the grounding prompt (and cost) bounded regardless of how much content has synced


class ChatNotConfigured(Exception):
    pass


async def _build_context(session: AsyncSession, team: Team) -> str:
    agents = (
        await session.execute(
            select(ContentAgent).where(ContentAgent.status == ContentStatus.ACTIVE)
        )
    ).scalars().all()
    skills = (
        await session.execute(
            select(ContentSkill).where(ContentSkill.status == ContentStatus.ACTIVE)
        )
    ).scalars().all()
    commands = (
        await session.execute(
            select(ContentCommand).where(ContentCommand.status == ContentStatus.ACTIVE)
        )
    ).scalars().all()
    knowledge = (
        await session.execute(
            select(ContentKnowledge).where(
                ContentKnowledge.status == ContentStatus.ACTIVE,
                ContentKnowledge.effective_team == team,
            )
        )
    ).scalars().all()

    parts = ["# Personas"]
    parts += [f"- {a.name}: {a.description}" for a in agents]
    parts.append("\n# Skills")
    parts += [f"- {s.name}: {s.description}" for s in skills]
    parts.append("\n# Commands")
    parts += [f"- /{c.slug}: {c.description}" for c in commands]
    parts.append(f"\n# Knowledge ({team.value} team)")
    parts += [f"- {k.name}: {k.description}\n  {k.body_markdown[:500]}" for k in knowledge]

    context = "\n".join(parts)
    return context[:MAX_CONTEXT_CHARS]


async def ask(session: AsyncSession, team: Team, message: str) -> str:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ChatNotConfigured("ANTHROPIC_API_KEY is not set")

    context = await _build_context(session, team)
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model=settings.default_model,
        max_tokens=1024,
        system=(
            "You answer questions about this team's personas, skills, commands, and "
            "shared knowledge, using only the content below. If the answer isn't in "
            "it, say so plainly instead of guessing.\n\n" + context
        ),
        messages=[{"role": "user", "content": message}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
