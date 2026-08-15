import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { ApiError } from "../api/client";
import { syncApi } from "../api/sync";
import PageHeader from "../components/ui/PageHeader";

export default function AdminSyncPage() {
  const queryClient = useQueryClient();
  const [source, setSource] = useState("../../vcode-w-hc");
  const [ref, setRef] = useState("");

  const runs = useQuery({ queryKey: ["sync", "runs"], queryFn: syncApi.runs });
  const flags = useQuery({ queryKey: ["sync", "flags"], queryFn: syncApi.flags });

  const trigger = useMutation({
    mutationFn: () => syncApi.trigger(source, ref || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sync"] });
      queryClient.invalidateQueries({ queryKey: ["personas"] });
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      queryClient.invalidateQueries({ queryKey: ["commands"] });
      queryClient.invalidateQueries({ queryKey: ["knowledge"] });
      queryClient.invalidateQueries({ queryKey: ["about"] });
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    trigger.mutate();
  }

  const latestRun = runs.data?.[0];

  return (
    <div>
      <PageHeader
        title="Sync administration"
        subtitle="Trigger a manual sync, or review webhook-triggered runs and flagged content mismatches."
      />

      <form
        onSubmit={handleSubmit}
        className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <label className="flex flex-col gap-1 text-sm">
          Source (path or git URL)
          <input
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="w-80 rounded-lg border border-slate-300 px-2.5 py-1.5 outline-none focus:border-slate-500"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Ref (optional)
          <input
            value={ref}
            onChange={(e) => setRef(e.target.value)}
            className="w-32 rounded-lg border border-slate-300 px-2.5 py-1.5 outline-none focus:border-slate-500"
          />
        </label>
        <button
          type="submit"
          disabled={trigger.isPending}
          className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-50"
        >
          {trigger.isPending ? "Syncing…" : "Re-sync from GitHub"}
        </button>
        {trigger.isError && (
          <p className="w-full text-sm text-red-600">
            {trigger.error instanceof ApiError ? trigger.error.message : "Sync failed"}
          </p>
        )}
      </form>

      {latestRun && (
        <div className="mt-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="font-medium text-slate-900">Last run</h2>
          <p className="text-sm text-slate-500">
            {latestRun.status} ({latestRun.trigger}) ·{" "}
            {new Date(latestRun.requested_at).toLocaleString()}
          </p>
          <pre className="mt-2 overflow-x-auto rounded-lg bg-slate-50 p-3 text-xs">
            {JSON.stringify(latestRun.counts_json, null, 2)}
          </pre>
        </div>
      )}

      <div className="mt-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-medium text-slate-900">Flagged mismatches / parse errors</h2>
        {flags.data?.length ? (
          <table className="mt-2 w-full text-left text-sm">
            <thead className="text-slate-500">
              <tr>
                <th className="pb-1">Type</th>
                <th className="pb-1">Path</th>
                <th className="pb-1">Details</th>
              </tr>
            </thead>
            <tbody>
              {flags.data.map((flag) => (
                <tr key={flag.id} className="border-t border-slate-100">
                  <td className="py-1">{flag.flag_type}</td>
                  <td className="py-1 font-mono text-xs">{flag.source_path}</td>
                  <td className="py-1 text-xs text-slate-500">{JSON.stringify(flag.details_json)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="mt-2 text-sm text-slate-500">No flags.</p>
        )}
      </div>

      <div className="mt-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-medium text-slate-900">Run history</h2>
        <table className="mt-2 w-full text-left text-sm">
          <thead className="text-slate-500">
            <tr>
              <th className="pb-1">Requested</th>
              <th className="pb-1">Status</th>
              <th className="pb-1">Trigger</th>
              <th className="pb-1">Source</th>
            </tr>
          </thead>
          <tbody>
            {runs.data?.map((run) => (
              <tr key={run.id} className="border-t border-slate-100">
                <td className="py-1">{new Date(run.requested_at).toLocaleString()}</td>
                <td className="py-1">{run.status}</td>
                <td className="py-1">{run.trigger}</td>
                <td className="py-1 font-mono text-xs">{run.source_ref}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
