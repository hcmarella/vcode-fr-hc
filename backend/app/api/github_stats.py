"""PR stats for the Reports page. Read-only, no approval gate needed -- same
shape as the Jira search endpoint, but there's no write path here at all
since GitHub PR state isn't something this portal ever mutates.
"""

from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.config import get_settings
from app.db.models.user import User
from app.demo_data import synthetic_prs_for
from app.integrations.github_client import GitHubClient, GitHubNotConfigured

router = APIRouter(prefix="/api/github", tags=["github"])

_STALE_OPEN_DAYS = 14
_TOP_CONTRIBUTORS = 5


def _parse(ts: str | None) -> datetime | None:
    if ts is None:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _repo_stats(repo: str, prs: list[dict]) -> dict:
    now = datetime.now(timezone.utc)
    open_prs = [p for p in prs if p["state"] == "open"]
    merged_prs = [p for p in prs if p.get("merged_at")]
    closed_unmerged = [p for p in prs if p["state"] == "closed" and not p.get("merged_at")]

    merge_hours = [
        (_parse(p["merged_at"]) - _parse(p["created_at"])).total_seconds() / 3600
        for p in merged_prs
    ]
    avg_merge_hours = round(sum(merge_hours) / len(merge_hours), 1) if merge_hours else None

    stale_open = [
        p for p in open_prs if (now - _parse(p["created_at"])).days >= _STALE_OPEN_DAYS
    ]

    contributors = Counter(p["user"]["login"] for p in prs if p.get("user"))
    top_contributors = [
        {"login": login, "pr_count": count}
        for login, count in contributors.most_common(_TOP_CONTRIBUTORS)
    ]

    recent = sorted(prs, key=lambda p: p["created_at"], reverse=True)[:10]

    return {
        "repo": repo,
        "open_count": len(open_prs),
        "merged_count": len(merged_prs),
        "closed_unmerged_count": len(closed_unmerged),
        "stale_open_count": len(stale_open),
        "avg_merge_hours": avg_merge_hours,
        "top_contributors": top_contributors,
        "demo_data_included": any(p.get("synthetic") for p in prs),
        "recent_prs": [
            {
                "number": p["number"],
                "title": p["title"],
                "state": "merged" if p.get("merged_at") else p["state"],
                "author": (p.get("user") or {}).get("login"),
                "created_at": p["created_at"],
                "merged_at": p.get("merged_at"),
                "html_url": p["html_url"],
                "synthetic": p.get("synthetic", False),
            }
            for p in recent
        ],
    }


@router.get("/stats")
async def stats(_user: User = Depends(get_current_user)) -> dict:
    try:
        client = GitHubClient()
    except GitHubNotConfigured:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "GitHub stats aren't configured") from None

    demo_mode = get_settings().github_stats_demo_mode

    per_repo = []
    for repo in client.repos:
        try:
            prs = await client.list_pull_requests(repo)
        except Exception as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"GitHub fetch failed for {repo}: {exc}") from None
        if demo_mode:
            prs = prs + synthetic_prs_for(repo)
        per_repo.append(_repo_stats(repo, prs))

    totals = {
        "open_count": sum(r["open_count"] for r in per_repo),
        "merged_count": sum(r["merged_count"] for r in per_repo),
        "closed_unmerged_count": sum(r["closed_unmerged_count"] for r in per_repo),
        "stale_open_count": sum(r["stale_open_count"] for r in per_repo),
        "demo_data_included": any(r["demo_data_included"] for r in per_repo),
    }

    return {"repos": per_repo, "totals": totals}
