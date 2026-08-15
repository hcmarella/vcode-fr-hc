import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { skillsApi } from "../api/content";

export default function SkillsPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["skills"], queryFn: skillsApi.list });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error) return <p className="text-red-600">Failed to load skills.</p>;

  return (
    <div>
      <h1 className="text-2xl font-semibold">Skills</h1>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {data?.map((skill) => (
          <Link
            key={skill.id}
            to={`/skills/${skill.slug}`}
            className="rounded border border-slate-200 bg-white p-4 hover:border-slate-400"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">{skill.name}</span>
              {skill.status === "stale" && (
                <span className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800">stale</span>
              )}
            </div>
            <p className="mt-1 text-sm text-slate-500">{skill.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
