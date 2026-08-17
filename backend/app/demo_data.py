"""Shared roster + fixtures for demo/synthetic data, used by both
scripts/seed_demo_data.py (DB rows: users, sessions, Jira proposals, sync
runs) and app/api/github_stats.py's demo-mode PR overlay -- so a name that
shows up as a contributor on the Reports page is the same person who shows
up drafting tickets and chatting with personas elsewhere in the portal.

Nothing here touches a real external system. The GitHub overlay never
creates a real PR; the seed script never calls JiraClient or the real GitHub
API -- everything is inserted straight into this app's own Postgres, or
returned as a clearly `synthetic: true` field in an API response.
"""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.db.models.user import Role, Team

DEMO_EMAIL_DOMAIN = "demo.local"


@dataclass(frozen=True)
class DemoUser:
    email: str
    name: str
    team: Team
    role: Role
    github_login: str


DEMO_USERS: list[DemoUser] = [
    DemoUser("priya.shah@" + DEMO_EMAIL_DOMAIN, "Priya Shah", Team.ENGINEERING, Role.DEVELOPER, "priya-shah"),
    DemoUser("jordan.lee@" + DEMO_EMAIL_DOMAIN, "Jordan Lee", Team.ENGINEERING, Role.DEVELOPER, "jordan-lee"),
    DemoUser("marcus.chen@" + DEMO_EMAIL_DOMAIN, "Marcus Chen", Team.PRODUCT, Role.BUSINESS, "marcus-chen"),
    DemoUser("aisha.bello@" + DEMO_EMAIL_DOMAIN, "Aisha Bello", Team.QA, Role.DEVELOPER, "aisha-bello"),
    DemoUser("sam.okafor@" + DEMO_EMAIL_DOMAIN, "Sam Okafor", Team.DOCS, Role.DEVELOPER, "sam-okafor"),
    DemoUser("dana.whitfield@" + DEMO_EMAIL_DOMAIN, "Dana Whitfield", Team.ENGINEERING, Role.MANAGER, "dana-whitfield"),
]

DEMO_PASSWORD = "demo-portal-2026"


# (title, days_ago_created, state, merge_hours_or_none, author_index)
# merge_hours is None for open/closed-unmerged; state is "open"/"merged"/"closed".
# One deliberately sits past the 14-day stale-open threshold so the Reports
# page's amber "stale" badge has something real to show in the demo.
_SYNTHETIC_PR_FIXTURES: list[tuple[str, int, str, float | None, int]] = [
    ("Add retry backoff to sync worker's SQS poll loop", 2, "merged", 6.5, 0),
    ("Fix flaky toast timing in notification tests", 4, "merged", 3.0, 3),
    ("Migrate Playwright config to project-per-browser", 1, "open", None, 3),
    ("Refactor Jira action payload validation", 6, "merged", 21.0, 1),
    ("Document gRPC migration rollback plan", 8, "closed", None, 4),
    ("Add rate-limit handling to GitHub client", 19, "open", None, 0),
    ("Bump SQLAlchemy to 2.0.36", 3, "merged", 1.5, 1),
    ("Add contributor leaderboard to Reports API", 5, "merged", 9.0, 2),
]


def synthetic_prs_for(repo: str) -> list[dict]:
    """Fabricated PRs shaped like the GitHub API response, tagged
    synthetic=True. Deterministic per repo (seeded RNG) so the demo looks the
    same across a page refresh, but PR numbers are offset per repo so two
    repos' synthetic sets never collide."""
    rng = random.Random(repo)
    offset = rng.randint(500, 600)
    now = datetime.now(timezone.utc)

    prs = []
    for i, (title, days_ago, state, merge_hours, author_idx) in enumerate(_SYNTHETIC_PR_FIXTURES):
        author = DEMO_USERS[author_idx % len(DEMO_USERS)]
        created_at = now - timedelta(days=days_ago, hours=rng.randint(0, 20))
        merged_at = created_at + timedelta(hours=merge_hours) if merge_hours is not None else None
        prs.append({
            "number": offset + i,
            "title": title,
            "state": "closed" if state in ("merged", "closed") else "open",
            "user": {"login": author.github_login},
            "created_at": created_at.isoformat().replace("+00:00", "Z"),
            "merged_at": merged_at.isoformat().replace("+00:00", "Z") if merged_at else None,
            "html_url": f"https://github.com/{repo}/pulls",
            "synthetic": True,
        })
    return prs
