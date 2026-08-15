import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { knowledgeApi } from "../api/content";
import type { MemoryType } from "../api/types";
import { useCurrentUser } from "../hooks/useAuth";

const types: MemoryType[] = ["user", "feedback", "project", "reference"];

export default function KnowledgePage() {
  const { data: user } = useCurrentUser();
  const { data, isLoading, error } = useQuery({ queryKey: ["knowledge"], queryFn: knowledgeApi.list });
  const [filter, setFilter] = useState<MemoryType | "all">("all");

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error) return <p className="text-red-600">Failed to load knowledge.</p>;

  const filtered = data?.filter((entry) => filter === "all" || entry.metadata_type === filter);

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Knowledge</h1>
        {user && <span className="text-sm text-slate-500">Team: {user.team}</span>}
      </div>
      <div className="mt-3 flex gap-2 text-sm">
        <button
          onClick={() => setFilter("all")}
          className={`rounded px-2 py-1 ${filter === "all" ? "bg-slate-900 text-white" : "bg-slate-100"}`}
        >
          All
        </button>
        {types.map((t) => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            className={`rounded px-2 py-1 ${filter === t ? "bg-slate-900 text-white" : "bg-slate-100"}`}
          >
            {t}
          </button>
        ))}
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {filtered?.map((entry) => (
          <Link
            key={entry.id}
            to={`/knowledge/${entry.id}`}
            className="rounded border border-slate-200 bg-white p-4 hover:border-slate-400"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">{entry.name}</span>
              <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                {entry.metadata_type}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-500">{entry.description}</p>
          </Link>
        ))}
        {filtered?.length === 0 && <p className="text-sm text-slate-500">No entries for this team.</p>}
      </div>
    </div>
  );
}
