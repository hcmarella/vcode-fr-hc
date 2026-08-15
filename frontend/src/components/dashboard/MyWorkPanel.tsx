import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import { jiraApi } from "../../api/jira";
import { useCurrentUser } from "../../hooks/useAuth";
import Badge from "../ui/Badge";

// Real, live-pulled "day to day" work: tickets actually assigned to this
// user in Jira, plus their own pending approvals. Assumes the portal
// account's email matches the Jira account's email (JQL `assignee = "..."`)
// -- that's the honest limitation of API-token auth (a single service
// identity, not per-user OAuth): Jira has no notion of "the portal user,"
// only of Jira accounts, so this is a best-effort match, not a guarantee.
export default function MyWorkPanel() {
  const { data: user } = useCurrentUser();

  const assigned = useQuery({
    queryKey: ["jira", "search", "assigned-to-me", user?.email],
    queryFn: () => jiraApi.search(`assignee = "${user!.email}" AND status != Done ORDER BY updated DESC`),
    enabled: !!user,
    retry: false,
    throwOnError: false,
  });

  const actions = useQuery({ queryKey: ["jira", "actions"], queryFn: jiraApi.actions });
  const pendingCount = actions.data?.filter((a) => a.status === "pending").length ?? 0;

  const notConfigured = assigned.error instanceof ApiError && assigned.error.status === 503;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-slate-900">My work</h2>
        {pendingCount > 0 && (
          <Link to="/jira">
            <Badge tone="amber">{pendingCount} pending approval{pendingCount === 1 ? "" : "s"}</Badge>
          </Link>
        )}
      </div>

      {notConfigured && (
        <p className="mt-3 text-sm text-slate-400">
          Connect Jira (JIRA_BASE_URL/JIRA_EMAIL/JIRA_API_TOKEN) to see tickets assigned to you here.
        </p>
      )}
      {!notConfigured && assigned.isError && (
        <p className="mt-3 text-sm text-red-600">Couldn't load your assigned tickets.</p>
      )}
      {assigned.isLoading && <p className="mt-3 text-sm text-slate-400">Loading…</p>}

      {assigned.data && (
        <ul className="mt-3 space-y-2">
          {assigned.data.slice(0, 5).map((issue) => (
            <li key={issue.key} className="flex items-center justify-between gap-2 text-sm">
              <div className="min-w-0">
                <span className="font-mono text-xs text-slate-400">{issue.key}</span>{" "}
                <span className="text-slate-700">{issue.summary}</span>
              </div>
              <Badge tone={issue.priority === "High" ? "red" : "slate"}>{issue.status}</Badge>
            </li>
          ))}
          {assigned.data.length === 0 && (
            <li className="text-sm text-slate-400">Nothing assigned to you right now.</li>
          )}
        </ul>
      )}
    </div>
  );
}
