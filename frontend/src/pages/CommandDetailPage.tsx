import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { commandsApi } from "../api/content";
import MarkdownBody from "../components/content/MarkdownBody";

export default function CommandDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: command, isLoading, error } = useQuery({
    queryKey: ["commands", slug],
    queryFn: () => commandsApi.get(slug!),
    enabled: !!slug,
  });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error || !command) return <p className="text-red-600">Command not found.</p>;

  return (
    <div>
      <h1 className="text-2xl font-semibold">/{command.slug}</h1>
      <p className="mt-1 text-slate-500">{command.description}</p>
      {command.argument_hint && (
        <p className="mt-1 font-mono text-sm text-slate-400">{command.argument_hint}</p>
      )}
      <MarkdownBody>{command.body_markdown}</MarkdownBody>
    </div>
  );
}
