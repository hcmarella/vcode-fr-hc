import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { personasApi } from "../api/content";
import Badge from "../components/ui/Badge";
import CardGridSkeleton from "../components/ui/CardGridSkeleton";
import EmptyState from "../components/ui/EmptyState";
import EntityCard from "../components/ui/EntityCard";
import ErrorState from "../components/ui/ErrorState";
import PageHeader from "../components/ui/PageHeader";
import SearchInput from "../components/ui/SearchInput";

export default function PersonasPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["personas"], queryFn: personasApi.list });
  const [query, setQuery] = useState("");

  const filtered = data?.filter(
    (a) =>
      a.name.toLowerCase().includes(query.toLowerCase()) ||
      a.description.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div>
      <PageHeader
        title="Personas"
        subtitle={data ? `${data.length} synced from vcode-w-hc` : undefined}
      />
      <div className="mb-4 max-w-sm">
        <SearchInput value={query} onChange={setQuery} placeholder="Search personas…" />
      </div>

      {isLoading && <CardGridSkeleton />}
      {error && <ErrorState message="Failed to load personas." />}
      {filtered && filtered.length === 0 && <EmptyState message="No personas match that search." />}

      <div className="grid gap-3 sm:grid-cols-2">
        {filtered?.map((agent, i) => (
          <EntityCard key={agent.id} to={`/personas/${agent.slug}`} accent="violet" delayMs={i * 40}>
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium text-slate-900">{agent.name}</span>
              {agent.status === "stale" && <Badge tone="amber">stale</Badge>}
            </div>
            <p className="mt-1 line-clamp-2 text-sm text-slate-500">{agent.description}</p>
            <div className="mt-3 flex flex-wrap gap-1">
              {agent.tools.slice(0, 4).map((tool) => (
                <Badge key={tool}>{tool}</Badge>
              ))}
              {agent.tools.length > 4 && <Badge>+{agent.tools.length - 4}</Badge>}
            </div>
          </EntityCard>
        ))}
      </div>
    </div>
  );
}
