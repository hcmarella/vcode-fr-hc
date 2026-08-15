import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { ApiError } from "../api/client";
import { jiraApi } from "../api/jira";

export default function JiraPage() {
  const queryClient = useQueryClient();
  const [jql, setJql] = useState('project = ENG AND status != Done ORDER BY updated DESC');
  const [submittedJql, setSubmittedJql] = useState<string | null>(null);

  const search = useQuery({
    queryKey: ["jira", "search", submittedJql],
    queryFn: () => jiraApi.search(submittedJql!),
    enabled: submittedJql !== null,
  });

  const actions = useQuery({ queryKey: ["jira", "actions"], queryFn: jiraApi.actions });
  const pending = actions.data?.filter((a) => a.status === "pending") ?? [];

  const confirm = useMutation({
    mutationFn: (id: string) => jiraApi.confirm(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jira", "actions"] }),
  });
  const reject = useMutation({
    mutationFn: (id: string) => jiraApi.reject(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jira", "actions"] }),
  });

  function handleSearch(e: FormEvent) {
    e.preventDefault();
    setSubmittedJql(jql);
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Jira</h1>
      <p className="mt-1 text-sm text-slate-500">
        Search is read-only and runs immediately. Creating or updating a ticket (via the chat
        widget) always stages a proposal here for you to confirm first.
      </p>

      <form onSubmit={handleSearch} className="mt-4 flex gap-2">
        <input
          value={jql}
          onChange={(e) => setJql(e.target.value)}
          className="flex-1 rounded border border-slate-300 px-3 py-2 text-sm font-mono"
          placeholder="JQL, e.g. project = ENG AND status = &quot;In Progress&quot;"
        />
        <button
          type="submit"
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white"
        >
          Search
        </button>
      </form>

      {search.isError && (
        <p className="mt-3 text-sm text-red-600">
          {search.error instanceof ApiError ? search.error.message : "Search failed."}
        </p>
      )}

      {search.data && (
        <div className="mt-4 overflow-x-auto rounded border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-3 py-2">Key</th>
                <th className="px-3 py-2">Summary</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Assignee</th>
                <th className="px-3 py-2">Priority</th>
              </tr>
            </thead>
            <tbody>
              {search.data.map((issue) => (
                <tr key={issue.key} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-mono text-xs">{issue.key}</td>
                  <td className="px-3 py-2">{issue.summary}</td>
                  <td className="px-3 py-2">{issue.status}</td>
                  <td className="px-3 py-2">{issue.assignee ?? "Unassigned"}</td>
                  <td className="px-3 py-2">{issue.priority ?? "—"}</td>
                </tr>
              ))}
              {search.data.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-4 text-center text-slate-400">
                    No issues matched.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-8">
        <h2 className="text-lg font-medium">Pending approvals</h2>
        <p className="text-sm text-slate-500">
          Staged from the chat widget. Nothing here has reached Jira yet.
        </p>
        <div className="mt-3 space-y-2">
          {pending.map((action) => (
            <div
              key={action.id}
              className="flex items-center justify-between rounded border border-amber-200 bg-amber-50 p-3"
            >
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-amber-700">
                  {action.action_type === "create_issue" ? "Create" : "Update"}
                </p>
                <p className="text-sm text-slate-800">{action.preview_text}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => confirm.mutate(action.id)}
                  disabled={confirm.isPending || reject.isPending}
                  className="rounded bg-slate-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
                >
                  Confirm
                </button>
                <button
                  onClick={() => reject.mutate(action.id)}
                  disabled={confirm.isPending || reject.isPending}
                  className="rounded border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600 disabled:opacity-50"
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
          {pending.length === 0 && <p className="text-sm text-slate-400">Nothing pending.</p>}
        </div>
      </div>
    </div>
  );
}
