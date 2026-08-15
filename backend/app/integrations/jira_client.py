"""Thin Jira Cloud REST API v3 client. Search is read-only and safe to call
directly. create_issue/update_issue are real writes -- callers (chat_engine,
jira_actions API) must only invoke them after explicit human confirmation,
never directly off a model's tool call. This module doesn't enforce that
itself; it's just the HTTP layer. The approval gate lives one level up.
"""

import httpx

from app.config import get_settings


class JiraNotConfigured(Exception):
    pass


class JiraClient:
    def __init__(self):
        settings = get_settings()
        if not (settings.jira_base_url and settings.jira_email and settings.jira_api_token):
            raise JiraNotConfigured(
                "Jira integration is not configured (JIRA_BASE_URL/JIRA_EMAIL/JIRA_API_TOKEN)"
            )
        self._base_url = settings.jira_base_url.rstrip("/")
        self._auth = (settings.jira_email, settings.jira_api_token)

    async def search_issues(self, jql: str, max_results: int = 10) -> list[dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{self._base_url}/rest/api/3/search",
                params={
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": "summary,status,assignee,issuetype,priority,updated",
                },
                auth=self._auth,
            )
        resp.raise_for_status()
        issues = resp.json().get("issues", [])
        return [
            {
                "key": i["key"],
                "summary": i["fields"]["summary"],
                "status": i["fields"]["status"]["name"],
                "assignee": (i["fields"].get("assignee") or {}).get("displayName"),
                "issuetype": i["fields"]["issuetype"]["name"],
                "priority": (i["fields"].get("priority") or {}).get("name"),
                "updated": i["fields"]["updated"],
            }
            for i in issues
        ]

    async def create_issue(
        self, project_key: str, summary: str, description: str, issue_type: str = "Task"
    ) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self._base_url}/rest/api/3/issue",
                json={
                    "fields": {
                        "project": {"key": project_key},
                        "summary": summary,
                        "description": {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {"type": "paragraph", "content": [{"type": "text", "text": description}]}
                            ],
                        },
                        "issuetype": {"name": issue_type},
                    }
                },
                auth=self._auth,
            )
        resp.raise_for_status()
        return resp.json()

    async def update_issue(self, issue_key: str, fields: dict) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.put(
                f"{self._base_url}/rest/api/3/issue/{issue_key}",
                json={"fields": fields},
                auth=self._auth,
            )
        resp.raise_for_status()
