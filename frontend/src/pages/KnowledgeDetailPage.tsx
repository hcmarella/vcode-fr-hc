import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { knowledgeApi } from "../api/content";
import MarkdownBody from "../components/content/MarkdownBody";

export default function KnowledgeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: entry, isLoading, error } = useQuery({
    queryKey: ["knowledge", id],
    queryFn: () => knowledgeApi.get(id!),
    enabled: !!id,
  });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error || !entry) return <p className="text-red-600">Knowledge entry not found.</p>;

  return (
    <div>
      <h1 className="text-2xl font-semibold">{entry.name}</h1>
      <p className="mt-1 text-slate-500">{entry.description}</p>
      <div className="mt-2 flex gap-2 text-xs text-slate-500">
        <span className="rounded bg-slate-100 px-2 py-0.5">{entry.metadata_type}</span>
        <span className="rounded bg-slate-100 px-2 py-0.5">{entry.effective_team}</span>
      </div>
      <MarkdownBody>{entry.body_markdown}</MarkdownBody>
    </div>
  );
}
