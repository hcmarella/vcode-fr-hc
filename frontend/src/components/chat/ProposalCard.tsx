import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ApiError } from "../../api/client";
import { jiraApi } from "../../api/jira";
import type { ProposedAction } from "../../api/chat";

interface ProposalCardProps {
  proposal: ProposedAction;
}

// Renders a staged Jira write inline in the chat -- this is the only UI for
// actually reaching Jira's write API. The chat model never executes this
// itself; clicking Confirm here is what calls POST /api/jira/actions/{id}/confirm.
export default function ProposalCard({ proposal }: ProposalCardProps) {
  const queryClient = useQueryClient();
  const [decided, setDecided] = useState<"confirmed" | "rejected" | null>(null);

  const confirm = useMutation({
    mutationFn: () => jiraApi.confirm(proposal.id),
    onSuccess: () => {
      setDecided("confirmed");
      queryClient.invalidateQueries({ queryKey: ["jira", "actions"] });
    },
  });
  const reject = useMutation({
    mutationFn: () => jiraApi.reject(proposal.id),
    onSuccess: () => {
      setDecided("rejected");
      queryClient.invalidateQueries({ queryKey: ["jira", "actions"] });
    },
  });

  const activeError = confirm.error ?? reject.error;
  const errorMessage = activeError
    ? activeError instanceof ApiError
      ? activeError.message
      : "Something went wrong."
    : null;

  return (
    <div className="mr-6 animate-fade-in rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-amber-700">
        Jira {proposal.action_type === "create_issue" ? "create" : "update"} — needs your approval
      </p>
      <p className="mt-1 text-slate-800">{proposal.preview_text}</p>

      {decided === null && (
        <div className="mt-2 flex gap-2">
          <button
            onClick={() => confirm.mutate()}
            disabled={confirm.isPending || reject.isPending}
            className="rounded bg-slate-900 px-2.5 py-1 text-xs font-medium text-white disabled:opacity-50"
          >
            {confirm.isPending ? "Confirming…" : "Confirm"}
          </button>
          <button
            onClick={() => reject.mutate()}
            disabled={confirm.isPending || reject.isPending}
            className="rounded border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-600 disabled:opacity-50"
          >
            Reject
          </button>
        </div>
      )}
      {decided === "confirmed" && (
        <p className="mt-2 text-xs font-medium text-emerald-700">Confirmed and sent to Jira.</p>
      )}
      {decided === "rejected" && (
        <p className="mt-2 text-xs font-medium text-slate-500">Rejected — nothing was sent.</p>
      )}
      {errorMessage && <p className="mt-2 text-xs font-medium text-red-600">{errorMessage}</p>}
    </div>
  );
}
