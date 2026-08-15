import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { skillsApi } from "../api/content";
import Badge from "../components/ui/Badge";
import ErrorState from "../components/ui/ErrorState";
import MarkdownBody from "../components/content/MarkdownBody";

export default function SkillDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: skill, isLoading, error } = useQuery({
    queryKey: ["skills", slug],
    queryFn: () => skillsApi.get(slug!),
    enabled: !!slug,
  });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error || !skill) return <ErrorState message="Skill not found." />;

  return (
    <div className="animate-fade-in-up">
      <Link to="/skills" className="text-sm text-slate-500 hover:text-slate-900">
        ← Skills
      </Link>
      <div className="mt-3 flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-900">{skill.name}</h1>
        {skill.status === "stale" && <Badge tone="amber">stale</Badge>}
      </div>
      <p className="mt-1 text-slate-500">{skill.description}</p>
      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-6">
        <MarkdownBody>{skill.body_markdown}</MarkdownBody>
      </div>
    </div>
  );
}
