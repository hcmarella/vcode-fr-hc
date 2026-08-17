import { useQuery } from "@tanstack/react-query";

import { ApiError } from "../api/client";
import { githubApi } from "../api/github";
import type { GitHubRepoStats } from "../api/github";
import CategoryBarChart from "../components/charts/CategoryBarChart";
import Badge from "../components/ui/Badge";
import ErrorState from "../components/ui/ErrorState";
import PageHeader from "../components/ui/PageHeader";

const STATE_TONE: Record<string, "emerald" | "violet" | "slate"> = {
  open: "emerald",
  merged: "violet",
  closed: "slate",
};

function RepoSection({ stats }: { stats: GitHubRepoStats }) {
  const contributorData = stats.top_contributors.map((c) => ({
    label: c.login,
    value: c.pr_count,
  }));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="font-mono text-sm font-medium text-slate-900">{stats.repo}</h2>
        {stats.stale_open_count > 0 && (
          <Badge tone="amber">{stats.stale_open_count} stale open</Badge>
        )}
      </div>

      <div className="mt-4 grid grid-cols-4 gap-3 text-center">
        <div>
          <p className="text-xl font-semibold tabular-nums text-slate-900">{stats.open_count}</p>
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Open</p>
        </div>
        <div>
          <p className="text-xl font-semibold tabular-nums text-slate-900">{stats.merged_count}</p>
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Merged</p>
        </div>
        <div>
          <p className="text-xl font-semibold tabular-nums text-slate-900">
            {stats.closed_unmerged_count}
          </p>
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Closed</p>
        </div>
        <div>
          <p className="text-xl font-semibold tabular-nums text-slate-900">
            {stats.avg_merge_hours !== null ? `${Math.round(stats.avg_merge_hours)}h` : "—"}
          </p>
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Avg. merge time</p>
        </div>
      </div>

      {contributorData.length > 0 && (
        <div className="mt-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Top contributors
          </p>
          <CategoryBarChart data={contributorData} yAxisWidth={110} />
        </div>
      )}

      <div className="mt-5">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Recent PRs</p>
        <ul className="mt-2 divide-y divide-slate-100">
          {stats.recent_prs.map((pr) => (
            <li key={pr.number} className="flex items-center justify-between gap-3 py-2 text-sm">
              <a
                href={pr.html_url}
                target="_blank"
                rel="noreferrer"
                className="min-w-0 flex-1 truncate text-slate-700 hover:text-slate-900 hover:underline"
              >
                #{pr.number} {pr.title}
              </a>
              <span className="shrink-0 text-xs text-slate-400">{pr.author ?? "unknown"}</span>
              {pr.synthetic && <Badge tone="amber">demo</Badge>}
              <Badge tone={STATE_TONE[pr.state] ?? "slate"}>{pr.state}</Badge>
            </li>
          ))}
          {stats.recent_prs.length === 0 && (
            <li className="py-2 text-sm text-slate-400">No pull requests yet.</li>
          )}
        </ul>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  const query = useQuery({ queryKey: ["github", "stats"], queryFn: githubApi.stats });

  return (
    <div>
      <PageHeader
        title="Reports"
        subtitle="Pull request activity across the connected repos, pulled live from GitHub."
        action={
          query.data?.totals.demo_data_included ? (
            <Badge tone="amber">Includes demo data</Badge>
          ) : undefined
        }
      />

      {query.isLoading && (
        <div className="grid gap-4 sm:grid-cols-2">
          {[0, 1].map((i) => (
            <div key={i} className="h-64 animate-pulse rounded-xl bg-slate-100" />
          ))}
        </div>
      )}

      {query.isError && (
        <ErrorState
          message={
            query.error instanceof ApiError
              ? query.error.message
              : "Couldn't load GitHub stats."
          }
        />
      )}

      {query.data && (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Open PRs
              </p>
              <p className="mt-2 text-3xl font-semibold tabular-nums text-slate-900">
                {query.data.totals.open_count}
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Merged</p>
              <p className="mt-2 text-3xl font-semibold tabular-nums text-slate-900">
                {query.data.totals.merged_count}
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Closed</p>
              <p className="mt-2 text-3xl font-semibold tabular-nums text-slate-900">
                {query.data.totals.closed_unmerged_count}
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Stale open
              </p>
              <p className="mt-2 text-3xl font-semibold tabular-nums text-slate-900">
                {query.data.totals.stale_open_count}
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {query.data.repos.map((r) => (
              <RepoSection key={r.repo} stats={r} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
