import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { commandsApi } from "../api/content";
import Badge from "../components/ui/Badge";
import CardGridSkeleton from "../components/ui/CardGridSkeleton";
import EmptyState from "../components/ui/EmptyState";
import EntityCard from "../components/ui/EntityCard";
import ErrorState from "../components/ui/ErrorState";
import PageHeader from "../components/ui/PageHeader";
import SearchInput from "../components/ui/SearchInput";

export default function CommandsPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["commands"], queryFn: commandsApi.list });
  const [query, setQuery] = useState("");

  const filtered = data?.filter(
    (c) =>
      c.slug.toLowerCase().includes(query.toLowerCase()) ||
      c.description.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div>
      <PageHeader
        title="Commands"
        subtitle={data ? `${data.length} synced from vcode-w-hc` : undefined}
      />
      <div className="mb-4 max-w-sm">
        <SearchInput value={query} onChange={setQuery} placeholder="Search commands…" />
      </div>

      {isLoading && <CardGridSkeleton />}
      {error && <ErrorState message="Failed to load commands." />}
      {filtered && filtered.length === 0 && <EmptyState message="No commands match that search." />}

      <div className="grid gap-3 sm:grid-cols-2">
        {filtered?.map((command, i) => (
          <EntityCard key={command.id} to={`/commands/${command.slug}`} accent="amber" delayMs={i * 40}>
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono font-medium text-slate-900">/{command.slug}</span>
              {command.status === "stale" && <Badge tone="amber">stale</Badge>}
            </div>
            <p className="mt-1 line-clamp-2 text-sm text-slate-500">{command.description}</p>
            {command.argument_hint && (
              <p className="mt-2 font-mono text-xs text-slate-400">{command.argument_hint}</p>
            )}
          </EntityCard>
        ))}
      </div>
    </div>
  );
}
