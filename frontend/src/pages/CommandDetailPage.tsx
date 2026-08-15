import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { commandsApi } from "../api/content";
import Badge from "../components/ui/Badge";
import ErrorState from "../components/ui/ErrorState";
import MarkdownBody from "../components/content/MarkdownBody";

export default function CommandDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: command, isLoading, error } = useQuery({
    queryKey: ["commands", slug],
    queryFn: () => commandsApi.get(slug!),
    enabled: !!slug,
  });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error || !command) return <ErrorState message="Command not found." />;

  return (
    <div className="animate-fade-in-up">
      <Link to="/commands" className="text-sm text-slate-500 hover:text-slate-900">
        ← Commands
      </Link>
      <div className="mt-3 flex items-center justify-between gap-3">
        <h1 className="font-mono text-2xl font-semibold text-slate-900">/{command.slug}</h1>
        {command.status === "stale" && <Badge tone="amber">stale</Badge>}
      </div>
      <p className="mt-1 text-slate-500">{command.description}</p>
      {command.argument_hint && (
        <p className="mt-2 font-mono text-sm text-slate-400">{command.argument_hint}</p>
      )}
      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-6">
        <MarkdownBody>{command.body_markdown}</MarkdownBody>
      </div>
    </div>
  );
}
