import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { knowledgeApi } from "../api/content";
import type { MemoryType } from "../api/types";
import Badge from "../components/ui/Badge";
import CardGridSkeleton from "../components/ui/CardGridSkeleton";
import EmptyState from "../components/ui/EmptyState";
import EntityCard from "../components/ui/EntityCard";
import ErrorState from "../components/ui/ErrorState";
import PageHeader from "../components/ui/PageHeader";
import SearchInput from "../components/ui/SearchInput";
import { useCurrentUser } from "../hooks/useAuth";

const types: MemoryType[] = ["user", "feedback", "project", "reference"];

export default function KnowledgePage() {
  const { data: user } = useCurrentUser();
  const { data, isLoading, error } = useQuery({ queryKey: ["knowledge"], queryFn: knowledgeApi.list });
  const [filter, setFilter] = useState<MemoryType | "all">("all");
  const [query, setQuery] = useState("");

  const filtered = data?.filter(
    (entry) =>
      (filter === "all" || entry.metadata_type === filter) &&
      (entry.name.toLowerCase().includes(query.toLowerCase()) ||
        entry.description.toLowerCase().includes(query.toLowerCase()))
  );

  return (
    <div>
      <PageHeader
        title="Knowledge"
        subtitle={user ? `Scoped to the ${user.team} team` : undefined}
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="max-w-sm flex-1">
          <SearchInput value={query} onChange={setQuery} placeholder="Search knowledge…" />
        </div>
        <div className="flex gap-1.5 text-sm">
          <button
            onClick={() => setFilter("all")}
            className={`rounded-full px-3 py-1 transition ${
              filter === "all" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            All
          </button>
          {types.map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`rounded-full px-3 py-1 capitalize transition ${
                filter === t ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {isLoading && <CardGridSkeleton />}
      {error && <ErrorState message="Failed to load knowledge." />}
      {filtered && filtered.length === 0 && (
        <EmptyState message="No entries for this team match that filter." />
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {filtered?.map((entry, i) => (
          <EntityCard key={entry.id} to={`/knowledge/${entry.id}`} accent="emerald" delayMs={i * 40}>
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium text-slate-900">{entry.name}</span>
              <Badge tone="emerald">{entry.metadata_type}</Badge>
            </div>
            <p className="mt-1 line-clamp-2 text-sm text-slate-500">{entry.description}</p>
          </EntityCard>
        ))}
      </div>
    </div>
  );
}
