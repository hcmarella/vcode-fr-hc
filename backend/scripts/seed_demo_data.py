"""Seed the portal with synthetic activity for a team demo: demo user
accounts, AI-assisted chat sessions, staged Jira ticket proposals, and
content-sync history. Everything lands in this app's own Postgres --
no real Jira ticket is ever created (JiraClient is never called; rows are
inserted with a status/result already set) and no real Confluence/GitHub
write happens either.

Idempotent: re-running deletes and recreates every row this script owns,
identified by the @demo.local user email domain, so it's safe to re-run
right before a demo to get fresh-looking recent timestamps.

Usage:
    python scripts/seed_demo_data.py
    python scripts/seed_demo_data.py --wipe-only   # remove demo data, seed nothing
"""

import argparse
import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.db.base import async_session_factory
from app.db.models.content import ContentAgent
from app.db.models.jira import JiraActionRequest, JiraActionStatus, JiraActionType
from app.db.models.session import (
    ChatMessage,
    ContainerStatus,
    InvocationSession,
    MessageContentType,
    MessageRole,
    SessionStatus,
)
from app.db.models.sync import SyncRun, SyncRunStatus, SyncTrigger
from app.db.models.user import Role, User
from app.demo_data import DEMO_EMAIL_DOMAIN, DEMO_PASSWORD, DEMO_USERS
from app.security import hash_password

_PORTAL_REPO_URL = "https://github.com/hcmarella/vcode-fr-hc.git"
_CONTENT_REPO_URL = "https://github.com/hcmarella/vcode-w-hc.git"

# (user_email, persona_name, repo_url, days_ago, [(role, text_or_tool)])
# Text turns are (role, "text", content). Tool turns are
# (role, "tool_use"|"tool_result", tool_name, content).
_SESSIONS: list[dict] = [
    {
        "user": "priya.shah", "persona": "engineer", "repo": _PORTAL_REPO_URL, "days_ago": 1,
        "turns": [
            ("user", "text", "Can you look at ENG-482 and get started on the retry backoff fix for the sync worker?"),
            ("assistant", "text", "Restating scope: exponential backoff on the SQS poll loop after repeated ReceiveMessage failures, capped at 60s, with jitter. Implementing in app/workers/sync_worker.py plus a test for the backoff calculation."),
            ("assistant", "tool_use", "Bash", "pytest backend/tests/workers/test_sync_worker.py -k backoff"),
            ("assistant", "tool_result", None, "3 passed in 0.42s"),
            ("assistant", "text", "Backoff implemented and tested. Running pr-review before marking the PR ready."),
        ],
    },
    {
        "user": "jordan.lee", "persona": "qa-engineer", "repo": _PORTAL_REPO_URL, "days_ago": 3,
        "turns": [
            ("user", "text", "We got a report that toasts sometimes disappear before the user can read them. Can you help reproduce it?"),
            ("assistant", "text", "Repro: trigger two toasts within 300ms of each other. Expected: each keeps its own 4s timer. Actual: the second toast's mount resets a shared timer ref, so the first vanishes early. Filing as severity=medium per our SLA table (visual-only, no data loss)."),
        ],
    },
    {
        "user": "marcus.chen", "persona": "product-manager", "repo": _CONTENT_REPO_URL, "days_ago": 2,
        "turns": [
            ("user", "text", "I want to scope a ticket for adding CSV export to the Reports page."),
            ("assistant", "text", "Story: As a manager, I want to export PR stats as CSV, so I can share them outside the portal. Acceptance criteria: export button on Reports page; CSV includes every column shown in Recent PRs; respects the currently loaded repos. Non-goal: scheduled/email delivery (separate ticket). Drafted as ENG-511, staged for review."),
        ],
    },
    {
        "user": "sam.okafor", "persona": "docs-writer", "repo": _CONTENT_REPO_URL, "days_ago": 5,
        "turns": [
            ("user", "text", "We just finished the gRPC migration. Can you write up the decision record?"),
            ("assistant", "text", "Drafted under memory/engineering/grpc-migration.md. Status: accepted. Context: REST fan-out to six internal services was causing N+1 latency. Decision: internal service-to-service calls move to gRPC; the public API stays REST. Consequences: faster internal calls, added protobuf codegen to the build."),
        ],
    },
    {
        "user": "aisha.bello", "persona": "qa-engineer", "repo": _PORTAL_REPO_URL, "days_ago": 6,
        "turns": [
            ("user", "text", "Review the retry-backoff PR from a QA lens."),
            ("assistant", "text", "Using the pr-review checklist -- blocking: no test covers SQS staying down longer than the max backoff window. nit: rename the loop variable `n` to `attempt` for clarity."),
        ],
    },
    {
        "user": "priya.shah", "persona": "engineer", "repo": _PORTAL_REPO_URL, "days_ago": 8,
        "turns": [
            ("user", "text", "The GitHub stats endpoint is slow on first load, can you check why?"),
            ("assistant", "text", "It fetches up to 200 PRs per repo sequentially. Switching the per-repo fetch to asyncio.gather brought local p95 from ~1.8s to ~600ms."),
        ],
    },
    {
        "user": "dana.whitfield", "persona": "product-manager", "repo": _CONTENT_REPO_URL, "days_ago": 0,
        "turns": [
            ("user", "text", "Give me a one-paragraph status rollup of what shipped this week."),
            ("assistant", "text", "This week: sync-worker retry backoff merged, the toast-timer bug fixed, the gRPC migration decision documented, and CSV export for Reports scoped and staged for review. No blockers reported."),
        ],
    },
    {
        "user": "jordan.lee", "persona": "engineer", "repo": _PORTAL_REPO_URL, "days_ago": 10,
        "turns": [
            ("user", "text", "Can you add a stale-PR badge to the Reports page for anything open longer than 2 weeks?"),
            ("assistant", "text", "Added -- repo cards now show an amber 'N stale open' badge when stale_open_count > 0, computed server-side in github_stats.py."),
        ],
    },
    {
        "user": "marcus.chen", "persona": "product-manager", "repo": _CONTENT_REPO_URL, "days_ago": 12,
        "turns": [
            ("user", "text", "Bug: onboarding tour skips step 3 for business-role users."),
            ("assistant", "text", "Bug drafted: Environment: staging. Repro: sign up as business role, start the tour. Expected: all 5 steps shown. Actual: step 3 (Jira intro) is skipped. Severity: medium. Filed as ENG-497."),
        ],
    },
    {
        "user": "sam.okafor", "persona": "docs-writer", "repo": _CONTENT_REPO_URL, "days_ago": 14,
        "turns": [
            ("user", "text", "Draft a runbook for what to do when a sync run fails."),
            ("assistant", "text", "Drafted. Owner: platform team. When to use: SyncStatusBadge shows failed, or /admin/sync lists a failed run. Steps: check sync_runs.error_message on the admin page; re-trigger manually if it looks transient; escalate to #eng-platform if it fails twice in a row."),
        ],
    },
]

# (action_type, project_key, summary, preview_text, status, days_ago, requester_email, decider_email)
_JIRA_ACTIONS: list[tuple] = [
    ("create_issue", "ENG", "Add CSV export to Reports page", "Story: Add CSV export to Reports page (ENG-511)", "executed", 2, "marcus.chen", "dana.whitfield"),
    ("create_issue", "ENG", "Onboarding tour skips step 3 for business-role users", "Bug: Onboarding tour skips step 3 (ENG-497)", "executed", 12, "marcus.chen", "dana.whitfield"),
    ("create_issue", "ENG", "Add contributor leaderboard to Reports API", "Story: Contributor leaderboard on Reports (ENG-521)", "confirmed", 5, "marcus.chen", "priya.shah"),
    ("create_issue", "ENG", "Add rate-limit handling to GitHub client", "Task: Rate-limit handling for GitHub client (ENG-528)", "pending", 1, "priya.shah", None),
    ("create_issue", "ENG", "Toast dismiss timer shared across instances", "Bug: Toast dismiss timer shared across toasts (ENG-499)", "executed", 3, "jordan.lee", "dana.whitfield"),
    ("update_issue", "ENG", "Mark ENG-482 as Done", "Update: ENG-482 -> Done", "executed", 1, "priya.shah", "dana.whitfield"),
    ("create_issue", "DOCS", "Draft sync-failure runbook", "Task: Sync-failure runbook (DOCS-14)", "executed", 14, "sam.okafor", "dana.whitfield"),
    ("create_issue", "ENG", "Add stale-PR badge to Reports page", "Story: Stale-PR badge on Reports (ENG-505)", "executed", 10, "jordan.lee", "priya.shah"),
    ("create_issue", "QA", "Playwright flake in checkout spec", "Bug: Playwright flake in checkout spec (QA-33)", "rejected", 7, "aisha.bello", "dana.whitfield"),
    ("create_issue", "ENG", "Investigate GitHub stats endpoint latency", "Task: Investigate Reports endpoint latency (ENG-490)", "pending", 8, "priya.shah", None),
]

_SYNC_RUNS: list[tuple] = [
    (SyncRunStatus.SUCCESS, SyncTrigger.WEBHOOK, 0, {"agent": {"updated": 1}, "skill": {"updated": 0}, "command": {"updated": 0}, "knowledge": {"created": 1}}),
    (SyncRunStatus.SUCCESS, SyncTrigger.MANUAL, 2, {"agent": {"updated": 0}, "skill": {"created": 1}, "command": {"updated": 0}, "knowledge": {"updated": 2}}),
    (SyncRunStatus.SUCCESS, SyncTrigger.WEBHOOK, 4, {"agent": {"updated": 2}, "skill": {"updated": 0}, "command": {"created": 1}, "knowledge": {"updated": 0}}),
    (SyncRunStatus.FAILED, SyncTrigger.WEBHOOK, 5, {}),
    (SyncRunStatus.SUCCESS, SyncTrigger.WEBHOOK, 5, {"agent": {"updated": 0}, "skill": {"updated": 0}, "command": {"updated": 0}, "knowledge": {"updated": 4}}),
    (SyncRunStatus.SUCCESS, SyncTrigger.MANUAL, 9, {"agent": {"updated": 1}, "skill": {"updated": 1}, "command": {"updated": 0}, "knowledge": {"updated": 1}}),
    (SyncRunStatus.SUCCESS, SyncTrigger.WEBHOOK, 11, {"agent": {"updated": 0}, "skill": {"updated": 0}, "command": {"updated": 0}, "knowledge": {"created": 3}}),
    (SyncRunStatus.SUCCESS, SyncTrigger.WEBHOOK, 14, {"agent": {"created": 5}, "skill": {"created": 3}, "command": {"created": 3}, "knowledge": {"created": 17}}),
]


async def wipe_demo_data(db) -> None:
    demo_user_ids = (
        await db.execute(select(User.id).where(User.email.like(f"%@{DEMO_EMAIL_DOMAIN}")))
    ).scalars().all()
    if not demo_user_ids:
        return

    session_ids = (
        await db.execute(
            select(InvocationSession.id).where(InvocationSession.user_id.in_(demo_user_ids))
        )
    ).scalars().all()
    if session_ids:
        await db.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(session_ids)))
        await db.execute(delete(InvocationSession).where(InvocationSession.id.in_(session_ids)))

    await db.execute(
        delete(JiraActionRequest).where(JiraActionRequest.requested_by_user_id.in_(demo_user_ids))
    )
    await db.execute(delete(SyncRun).where(SyncRun.triggered_by_user_id.in_(demo_user_ids)))
    await db.execute(delete(User).where(User.id.in_(demo_user_ids)))
    await db.commit()
    print(f"Wiped {len(demo_user_ids)} demo users and their sessions/proposals/sync runs.")


async def seed(db) -> None:
    now = datetime.now(timezone.utc)

    users_by_local_part: dict[str, User] = {}
    for demo in DEMO_USERS:
        user = User(
            email=demo.email,
            password_hash=hash_password(DEMO_PASSWORD),
            name=demo.name,
            team=demo.team,
            role=demo.role,
        )
        db.add(user)
        users_by_local_part[demo.email.split("@")[0]] = user
    await db.flush()
    print(f"Created {len(DEMO_USERS)} demo users (password: {DEMO_PASSWORD}).")

    personas = (await db.execute(select(ContentAgent))).scalars().all()
    personas_by_name = {p.name: p for p in personas}
    missing = {s["persona"] for s in _SESSIONS} - personas_by_name.keys()
    if missing:
        print(f"Skipping sessions for personas not yet synced from vcode-w-hc: {sorted(missing)}")

    session_count = 0
    message_count = 0
    for spec in _SESSIONS:
        persona = personas_by_name.get(spec["persona"])
        if persona is None:
            continue
        user = users_by_local_part[spec["user"]]
        started = now - timedelta(days=spec["days_ago"], hours=random.randint(0, 6))

        inv = InvocationSession(
            user_id=user.id,
            persona_id=persona.id,
            persona_name=persona.name,
            persona_tools=persona.tools,
            persona_model=persona.model,
            persona_system_prompt=persona.body_markdown,
            repo_url=spec["repo"],
            repo_branch="main",
            container_status=ContainerStatus.TERMINATED,
            status=SessionStatus.ENDED,
            created_at=started,
            last_activity_at=started + timedelta(minutes=len(spec["turns"]) * 2),
            ended_at=started + timedelta(minutes=len(spec["turns"]) * 2 + 1),
            total_input_tokens=random.randint(800, 4200),
            total_output_tokens=random.randint(400, 2600),
        )
        db.add(inv)
        await db.flush()
        session_count += 1

        for i, turn in enumerate(spec["turns"]):
            role_str = turn[0]
            kind = turn[1]
            role = MessageRole.USER if role_str == "user" else MessageRole.ASSISTANT
            msg_time = started + timedelta(minutes=i * 2)
            if kind == "text":
                db.add(ChatMessage(
                    session_id=inv.id,
                    sequence_number=i,
                    role=role,
                    content_type=MessageContentType.TEXT,
                    text_content=turn[2],
                    created_at=msg_time,
                ))
            elif kind == "tool_use":
                db.add(ChatMessage(
                    session_id=inv.id,
                    sequence_number=i,
                    role=role,
                    content_type=MessageContentType.TOOL_USE,
                    tool_name=turn[2],
                    tool_input_json={"command": turn[3]},
                    tool_use_id=str(uuid.uuid4()),
                    created_at=msg_time,
                ))
            else:  # tool_result
                db.add(ChatMessage(
                    session_id=inv.id,
                    sequence_number=i,
                    role=role,
                    content_type=MessageContentType.TOOL_RESULT,
                    tool_result_content=turn[3],
                    created_at=msg_time,
                ))
            message_count += 1

    for action_type, project_key, summary, preview_text, status_str, days_ago, requester, decider in _JIRA_ACTIONS:
        requester_user = users_by_local_part[requester]
        decider_user = users_by_local_part[decider] if decider else None
        created_at = now - timedelta(days=days_ago, hours=random.randint(0, 8))
        status = JiraActionStatus(status_str)

        payload = (
            {"project_key": project_key, "summary": summary, "description": f"{summary}.", "issue_type": "Task"}
            if action_type == "create_issue"
            else {"issue_key": "ENG-482", "fields": {"status": "Done"}}
        )

        action = JiraActionRequest(
            requested_by_user_id=requester_user.id,
            action_type=JiraActionType(action_type),
            payload_json=payload,
            preview_text=preview_text,
            status=status,
            created_at=created_at,
        )
        if status != JiraActionStatus.PENDING:
            action.decided_at = created_at + timedelta(minutes=random.randint(5, 240))
            action.decided_by_user_id = decider_user.id if decider_user else None
        if status == JiraActionStatus.EXECUTED:
            action.executed_at = action.decided_at
            issue_key = summary.split("(")[-1].rstrip(")") if "(" in summary else f"{project_key}-{random.randint(400, 599)}"
            action.result_json = {"key": issue_key}
        db.add(action)
    print(f"Created {len(_JIRA_ACTIONS)} Jira action proposals.")

    admin_user = (
        await db.execute(select(User).where(User.role == Role.ADMIN).limit(1))
    ).scalar_one_or_none()

    for status, trigger, days_ago, counts in _SYNC_RUNS:
        requested_at = now - timedelta(days=days_ago, hours=random.randint(0, 10))
        started_at = requested_at + timedelta(seconds=random.randint(1, 8))
        finished_at = started_at + timedelta(seconds=random.randint(4, 45)) if status != SyncRunStatus.FAILED else started_at + timedelta(seconds=3)
        db.add(SyncRun(
            requested_at=requested_at,
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            trigger=trigger,
            triggered_by_user_id=admin_user.id if trigger == SyncTrigger.MANUAL and admin_user else None,
            source=_CONTENT_REPO_URL,
            ref="main",
            source_ref="main",
            source_commit_sha=uuid.uuid4().hex[:12],
            counts_json=counts,
            error_message="Clone timed out after 30s" if status == SyncRunStatus.FAILED else None,
        ))
    print(f"Created {len(_SYNC_RUNS)} sync run records.")

    await db.commit()
    print(f"Done: {session_count} sessions, {message_count} chat messages.")


async def main(wipe_only: bool) -> None:
    async with async_session_factory() as db:
        await wipe_demo_data(db)
        if not wipe_only:
            await seed(db)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--wipe-only", action="store_true", help="Remove demo data without reseeding")
    args = parser.parse_args()
    asyncio.run(main(args.wipe_only))
