import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { knowledgeApi } from "../api/content";
import Badge from "../components/ui/Badge";
import ErrorState from "../components/ui/ErrorState";
import MarkdownBody from "../components/content/MarkdownBody";

export default function KnowledgeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: entry, isLoading, error } = useQuery({
    queryKey: ["knowledge", id],
    queryFn: () => knowledgeApi.get(id!),
    enabled: !!id,
  });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error || !entry) return <ErrorState message="Knowledge entry not found." />;

  return (
    <div className="animate-fade-in-up">
      <Link to="/knowledge" className="text-sm text-slate-500 hover:text-slate-900">
        ← Knowledge
      </Link>
      <h1 className="mt-3 text-2xl font-semibold text-slate-900">{entry.name}</h1>
      <p className="mt-1 text-slate-500">{entry.description}</p>
      <div className="mt-3 flex gap-1.5">
        <Badge tone="emerald">{entry.metadata_type}</Badge>
        <Badge tone="sky">{entry.effective_team}</Badge>
        {entry.team_mismatch && <Badge tone="red">team mismatch</Badge>}
      </div>
      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-6">
        <MarkdownBody>{entry.body_markdown}</MarkdownBody>
      </div>
    </div>
  );
}
