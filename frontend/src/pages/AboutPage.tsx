import { useQuery } from "@tanstack/react-query";

import { aboutApi } from "../api/content";
import MarkdownBody from "../components/content/MarkdownBody";
import HeroBanner from "../components/dashboard/HeroBanner";
import ErrorState from "../components/ui/ErrorState";

export default function AboutPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["about"], queryFn: aboutApi.get });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error || !data) return <ErrorState message="About content not synced yet." />;

  return (
    <div className="animate-fade-in-up">
      <HeroBanner imageQuery="team collaboration office">
        <h1 className="text-2xl font-semibold">About this project</h1>
        <p className="mt-1 text-sm text-slate-300">Synced from vcode-w-hc's README.</p>
      </HeroBanner>
      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-6">
        <MarkdownBody>{data.body_markdown}</MarkdownBody>
      </div>
    </div>
  );
}
