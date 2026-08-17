"""Thin GitHub REST API v3 client, read-only. Used by the Reports page to
pull pull-request stats for a fixed, server-configured list of repos -- see
app/api/github_stats.py. No write scope is ever requested or used here.
"""

import httpx

from app.config import get_settings

_API_BASE = "https://api.github.com"
_PAGE_SIZE = 100
_MAX_PAGES = 2  # up to 200 most-recent PRs per repo -- enough for trend stats
# without unbounded pagination against a portal endpoint hit on every page load.


class GitHubNotConfigured(Exception):
    pass


class GitHubClient:
    def __init__(self):
        settings = get_settings()
        if not settings.github_stats_repos.strip():
            raise GitHubNotConfigured("GITHUB_STATS_REPOS is not configured")
        self._repos = [r.strip() for r in settings.github_stats_repos.split(",") if r.strip()]
        self._headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            self._headers["Authorization"] = f"Bearer {settings.github_token}"

    @property
    def repos(self) -> list[str]:
        return self._repos

    async def list_pull_requests(self, repo: str) -> list[dict]:
        """All PRs (open + closed, most recent first) for one "owner/repo"."""
        prs: list[dict] = []
        async with httpx.AsyncClient(timeout=15, headers=self._headers) as client:
            for page in range(1, _MAX_PAGES + 1):
                resp = await client.get(
                    f"{_API_BASE}/repos/{repo}/pulls",
                    params={
                        "state": "all",
                        "sort": "created",
                        "direction": "desc",
                        "per_page": _PAGE_SIZE,
                        "page": page,
                    },
                )
                resp.raise_for_status()
                batch = resp.json()
                prs.extend(batch)
                if len(batch) < _PAGE_SIZE:
                    break
        return prs
