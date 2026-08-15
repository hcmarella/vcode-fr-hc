import { useQuery } from "@tanstack/react-query";

import { aboutApi } from "../api/content";
import MarkdownBody from "../components/content/MarkdownBody";

export default function AboutPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["about"], queryFn: aboutApi.get });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error || !data) return <p className="text-red-600">About content not synced yet.</p>;

  return (
    <div>
      <h1 className="text-2xl font-semibold">About this project</h1>
      <MarkdownBody>{data.body_markdown}</MarkdownBody>
    </div>
  );
}
