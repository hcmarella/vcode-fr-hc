import { useQuery } from "@tanstack/react-query";

import { syncApi } from "../../api/sync";

function timeAgo(iso: string): string {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

// Polls rather than pushing -- "active pull" here means the dashboard keeps
// asking for the latest state on its own, not that the server streams it.
// 30s is frequent enough to feel live without hammering the API from every
// open tab across a growing number of teams.
const POLL_INTERVAL_MS = 30_000;

export default function SyncStatusBadge() {
  const { data } = useQuery({
    queryKey: ["sync", "status"],
    queryFn: syncApi.status,
    refetchInterval: POLL_INTERVAL_MS,
  });

  if (!data) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-400">
        <span className="h-1.5 w-1.5 rounded-full bg-slate-300" />
        No sync yet
      </span>
    );
  }

  const ok = data.status === "success";
  const timestamp = data.finished_at ?? data.requested_at;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${
        ok
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-red-200 bg-red-50 text-red-700"
      }`}
      title={`${data.trigger} sync from ${data.source_ref}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-emerald-500" : "bg-red-500"} ${
          ok ? "" : "animate-pulse"
        }`}
      />
      Synced {timeAgo(timestamp)}
    </span>
  );
}
