import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { skillsApi } from "../api/content";
import MarkdownBody from "../components/content/MarkdownBody";

export default function SkillDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: skill, isLoading, error } = useQuery({
    queryKey: ["skills", slug],
    queryFn: () => skillsApi.get(slug!),
    enabled: !!slug,
  });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error || !skill) return <p className="text-red-600">Skill not found.</p>;

  return (
    <div>
      <h1 className="text-2xl font-semibold">{skill.name}</h1>
      <p className="mt-1 text-slate-500">{skill.description}</p>
      <MarkdownBody>{skill.body_markdown}</MarkdownBody>
    </div>
  );
}
