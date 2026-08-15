""""Ask" chat: answers questions grounded in already-synced content
(personas/skills/commands/team knowledge), and can search/create/update Jira
issues via tool-use.

The approval gate is the whole point of how this is wired: search_jira_issues
executes immediately (read-only, no risk), but propose_jira_create_issue and
propose_jira_update_issue only ever write a PENDING JiraActionRequest row --
they never call JiraClient.create_issue/update_issue directly. The model is
told this explicitly in its system prompt and cannot bypass it: there is no
tool in its toolset that performs the write. Actually reaching Jira's write
API only happens in app/api/jira_actions.py's confirm endpoint, gated behind
a human clicking Confirm on the staged proposal (frontend renders these as
cards in the chat widget).

Still deliberately not the sandboxed per-repo persona session engine implied
by db/models/session.py (InvocationSession/ChatMessage) -- that's a distinct,
larger, security-sensitive feature (container-per-session code execution).
"""

import json
import uuid

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models.content import ContentAgent, ContentCommand, ContentKnowledge, ContentSkill
from app.db.models.content import ContentStatus
from app.db.models.jira import JiraActionRequest, JiraActionStatus, JiraActionType
from app.db.models.user import User
from app.integrations.jira_client import JiraClient, JiraNotConfigured

MAX_CONTEXT_CHARS = 12_000
MAX_TOOL_ITERATIONS = 4  # hard cap so a confused tool-use loop can't run away


class ChatNotConfigured(Exception):
    pass


JIRA_TOOLS = [
    {
        "name": "search_jira_issues",
        "description": "Search Jira issues with JQL. Read-only -- executes immediately, no approval needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "jql": {
                    "type": "string",
                    "description": 'JQL query, e.g. \'project = ENG AND status = "In Progress"\'',
                }
            },
            "required": ["jql"],
        },
    },
    {
        "name": "propose_jira_create_issue",
        "description": (
            "Stage a new Jira issue for human approval. This does NOT create the issue -- "
            "it only records the proposal. The user must click Confirm in the UI before "
            "anything is written to Jira."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_key": {"type": "string"},
                "summary": {"type": "string"},
                "description": {"type": "string"},
                "issue_type": {"type": "string", "default": "Task"},
            },
            "required": ["project_key", "summary", "description"],
        },
    },
    {
        "name": "propose_jira_update_issue",
        "description": (
            "Stage an update to an existing Jira issue for human approval. This does NOT "
            "update the issue -- it only records the proposal. The user must click Confirm "
            "in the UI before anything is written to Jira."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string"},
                "fields": {
                    "type": "object",
                    "description": 'Jira fields to change, e.g. {"summary": "new title"}',
                },
            },
            "required": ["issue_key", "fields"],
        },
    },
]


async def _build_context(session: AsyncSession, team) -> str:
    agents = (
        (await session.execute(select(ContentAgent).where(ContentAgent.status == ContentStatus.ACTIVE)))
        .scalars()
        .all()
    )
    skills = (
        (await session.execute(select(ContentSkill).where(ContentSkill.status == ContentStatus.ACTIVE)))
        .scalars()
        .all()
    )
    commands = (
        (await session.execute(select(ContentCommand).where(ContentCommand.status == ContentStatus.ACTIVE)))
        .scalars()
        .all()
    )
    knowledge = (
        (
            await session.execute(
                select(ContentKnowledge).where(
                    ContentKnowledge.status == ContentStatus.ACTIVE,
                    ContentKnowledge.effective_team == team,
                )
            )
        )
        .scalars()
        .all()
    )

    parts = ["# Personas"]
    parts += [f"- {a.name}: {a.description}" for a in agents]
    parts.append("\n# Skills")
    parts += [f"- {s.name}: {s.description}" for s in skills]
    parts.append("\n# Commands")
    parts += [f"- /{c.slug}: {c.description}" for c in commands]
    parts.append(f"\n# Knowledge ({team.value} team)")
    parts += [f"- {k.name}: {k.description}\n  {k.body_markdown[:500]}" for k in knowledge]

    return "\n".join(parts)[:MAX_CONTEXT_CHARS]


async def _run_search(jql: str) -> str:
    try:
        client = JiraClient()
    except JiraNotConfigured:
        return "Jira isn't configured on this backend (missing JIRA_BASE_URL/JIRA_EMAIL/JIRA_API_TOKEN)."
    try:
        issues = await client.search_issues(jql)
    except Exception as exc:  # Jira 4xx/5xx, bad JQL, network error, etc.
        return f"Jira search failed: {exc}"
    return json.dumps(issues) if issues else "No issues matched that query."


async def _stage_proposal(
    session: AsyncSession,
    user: User,
    action_type: JiraActionType,
    payload: dict,
    preview_text: str,
) -> JiraActionRequest:
    action = JiraActionRequest(
        id=uuid.uuid4(),
        requested_by_user_id=user.id,
        action_type=action_type,
        payload_json=payload,
        preview_text=preview_text,
        status=JiraActionStatus.PENDING,
    )
    session.add(action)
    await session.commit()
    await session.refresh(action)
    return action


async def ask(session: AsyncSession, user: User, message: str) -> tuple[str, list[JiraActionRequest]]:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ChatNotConfigured("ANTHROPIC_API_KEY is not set")

    context = await _build_context(session, user.team)
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    system = (
        "You answer questions about this team's personas, skills, commands, and shared "
        "knowledge, and can search/create/update Jira issues via tools. Searching is "
        "read-only and immediate. Creating or updating a Jira issue always requires a "
        "separate human confirmation step in the UI -- your propose_* tool calls only "
        "stage the change, they never execute it. Never tell the user something was "
        "created or updated; say it's staged and awaiting their approval.\n\n" + context
    )

    messages: list[dict] = [{"role": "user", "content": message}]
    proposals: list[JiraActionRequest] = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = await client.messages.create(
            model=settings.default_model,
            max_tokens=1024,
            system=system,
            tools=JIRA_TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text"), proposals

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if block.name == "search_jira_issues":
                result_text = await _run_search(block.input["jql"])
            elif block.name == "propose_jira_create_issue":
                inp = block.input
                preview = f'Create {inp.get("issue_type", "Task")} in {inp["project_key"]}: "{inp["summary"]}"'
                action = await _stage_proposal(session, user, JiraActionType.CREATE_ISSUE, inp, preview)
                proposals.append(action)
                result_text = f"Staged for human approval (id={action.id}): {preview}"
            elif block.name == "propose_jira_update_issue":
                inp = block.input
                preview = f'Update {inp["issue_key"]}: {json.dumps(inp["fields"])}'
                action = await _stage_proposal(session, user, JiraActionType.UPDATE_ISSUE, inp, preview)
                proposals.append(action)
                result_text = f"Staged for human approval (id={action.id}): {preview}"
            else:
                result_text = f"Unknown tool: {block.name}"

            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": result_text}
            )
        messages.append({"role": "user", "content": tool_results})

    return "I wasn't able to finish that within the allowed number of tool calls.", proposals
