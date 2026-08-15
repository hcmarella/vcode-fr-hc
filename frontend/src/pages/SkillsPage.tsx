import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { skillsApi } from "../api/content";
import Badge from "../components/ui/Badge";
import CardGridSkeleton from "../components/ui/CardGridSkeleton";
import EmptyState from "../components/ui/EmptyState";
import EntityCard from "../components/ui/EntityCard";
import ErrorState from "../components/ui/ErrorState";
import PageHeader from "../components/ui/PageHeader";
import SearchInput from "../components/ui/SearchInput";

export default function SkillsPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["skills"], queryFn: skillsApi.list });
  const [query, setQuery] = useState("");

  const filtered = data?.filter(
    (s) =>
      s.name.toLowerCase().includes(query.toLowerCase()) ||
      s.description.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div>
      <PageHeader title="Skills" subtitle={data ? `${data.length} synced from vcode-w-hc` : undefined} />
      <div className="mb-4 max-w-sm">
        <SearchInput value={query} onChange={setQuery} placeholder="Search skills…" />
      </div>

      {isLoading && <CardGridSkeleton />}
      {error && <ErrorState message="Failed to load skills." />}
      {filtered && filtered.length === 0 && <EmptyState message="No skills match that search." />}

      <div className="grid gap-3 sm:grid-cols-2">
        {filtered?.map((skill, i) => (
          <EntityCard key={skill.id} to={`/skills/${skill.slug}`} accent="sky" delayMs={i * 40}>
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium text-slate-900">{skill.name}</span>
              {skill.status === "stale" && <Badge tone="amber">stale</Badge>}
            </div>
            <p className="mt-1 line-clamp-3 text-sm text-slate-500">{skill.description}</p>
          </EntityCard>
        ))}
      </div>
    </div>
  );
}
