import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { personasApi } from "../api/content";
import MarkdownBody from "../components/content/MarkdownBody";

export default function PersonaDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: agent, isLoading, error } = useQuery({
    queryKey: ["personas", slug],
    queryFn: () => personasApi.get(slug!),
    enabled: !!slug,
  });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error || !agent) return <p className="text-red-600">Persona not found.</p>;

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{agent.name}</h1>
        {agent.status === "stale" && (
          <span className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800">stale</span>
        )}
      </div>
      <p className="mt-1 text-slate-500">{agent.description}</p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {agent.tools.map((tool) => (
          <span key={tool} className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
            {tool}
          </span>
        ))}
        <span className="text-xs text-slate-400">model: {agent.model}</span>
      </div>
      <button className="mt-4 rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white" disabled>
        Start chat session (Phase 4)
      </button>
      <MarkdownBody>{agent.body_markdown}</MarkdownBody>
    </div>
  );
}
