import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { chatApi } from "../../api/chat";
import type { ProposedAction } from "../../api/chat";
import { ApiError } from "../../api/client";
import ProposalCard from "./ProposalCard";

type ChatEntry =
  | { kind: "text"; role: "user" | "assistant" | "error"; text: string }
  | { kind: "proposal"; proposal: ProposedAction };

// Deliberately stateless/client-only history (no session persistence) --
// this is the lightweight "ask about synced content + propose Jira changes"
// widget, not the sandboxed per-repo persona session flow scaffolded at
// /sessions (that one needs InvocationSession/ChatMessage + a real
// sandbox_engine build).
export default function AskWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [entries, setEntries] = useState<ChatEntry[]>([]);

  const ask = useMutation({
    mutationFn: (message: string) => chatApi.ask(message),
    onSuccess: (res) =>
      setEntries((e) => [
        ...e,
        { kind: "text", role: "assistant", text: res.reply },
        ...res.proposed_actions.map((p): ChatEntry => ({ kind: "proposal", proposal: p })),
      ]),
    onError: (err) =>
      setEntries((e) => [
        ...e,
        {
          kind: "text",
          role: "error",
          text: err instanceof ApiError ? err.message : "Something went wrong asking that.",
        },
      ]),
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const message = input.trim();
    if (!message || ask.isPending) return;
    setEntries((prev) => [...prev, { kind: "text", role: "user", text: message }]);
    setInput("");
    ask.mutate(message);
  }

  return (
    <div className="fixed bottom-5 right-5 z-40">
      {open && (
        <div className="mb-3 flex h-96 w-80 animate-pop-in flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-200 bg-slate-900 px-4 py-3 text-white">
            <span className="text-sm font-medium">Ask the portal</span>
            <button
              onClick={() => setOpen(false)}
              className="text-slate-300 hover:text-white"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
          <div className="flex-1 space-y-3 overflow-y-auto p-3">
            {entries.length === 0 && (
              <p className="text-xs text-slate-400">
                Ask about any synced persona, skill, command, or your team's knowledge base, or
                ask it to search/create/update Jira issues -- e.g. "what's open in ENG right now?"
                Jira writes always need your explicit confirmation.
              </p>
            )}
            {entries.map((entry, i) =>
              entry.kind === "proposal" ? (
                <ProposalCard key={i} proposal={entry.proposal} />
              ) : (
                <div
                  key={i}
                  className={`animate-fade-in rounded-lg px-3 py-2 text-sm ${
                    entry.role === "user"
                      ? "ml-6 bg-slate-900 text-white"
                      : entry.role === "error"
                        ? "bg-red-50 text-red-700"
                        : "mr-6 bg-slate-100 text-slate-800"
                  }`}
                >
                  {entry.text}
                </div>
              )
            )}
            {ask.isPending && (
              <div className="mr-6 flex gap-1 rounded-lg bg-slate-100 px-3 py-2">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
              </div>
            )}
          </div>
          <form onSubmit={handleSubmit} className="flex gap-2 border-t border-slate-200 p-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question…"
              className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-sm outline-none focus:border-slate-500"
            />
            <button
              type="submit"
              disabled={ask.isPending}
              className="rounded-lg bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
            >
              Send
            </button>
          </form>
        </div>
      )}
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-900 text-2xl text-white shadow-lg transition hover:scale-105 hover:bg-slate-800"
        aria-label="Toggle chat"
      >
        {open ? "×" : "💬"}
      </button>
    </div>
  );
}
