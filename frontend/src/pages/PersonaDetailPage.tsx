import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { personasApi } from "../api/content";
import Badge from "../components/ui/Badge";
import ErrorState from "../components/ui/ErrorState";
import MarkdownBody from "../components/content/MarkdownBody";

export default function PersonaDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: agent, isLoading, error } = useQuery({
    queryKey: ["personas", slug],
    queryFn: () => personasApi.get(slug!),
    enabled: !!slug,
  });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error || !agent) return <ErrorState message="Persona not found." />;

  return (
    <div className="animate-fade-in-up">
      <Link to="/personas" className="text-sm text-slate-500 hover:text-slate-900">
        ← Personas
      </Link>
      <div className="mt-3 flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-900">{agent.name}</h1>
        {agent.status === "stale" && <Badge tone="amber">stale</Badge>}
      </div>
      <p className="mt-1 text-slate-500">{agent.description}</p>
      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        {agent.tools.map((tool) => (
          <Badge key={tool}>{tool}</Badge>
        ))}
        <Badge tone="violet">model: {agent.model}</Badge>
      </div>
      <button
        className="mt-4 rounded-lg bg-slate-100 px-3 py-2 text-sm font-medium text-slate-400"
        disabled
        title="Sandboxed persona sessions are a separate, larger build (see InvocationSession) -- not yet implemented"
      >
        Start chat session (coming soon)
      </button>
      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-6">
        <MarkdownBody>{agent.body_markdown}</MarkdownBody>
      </div>
    </div>
  );
}
