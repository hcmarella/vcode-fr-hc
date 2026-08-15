import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { personasApi } from "../api/content";

export default function PersonasPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["personas"], queryFn: personasApi.list });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error) return <p className="text-red-600">Failed to load personas.</p>;

  return (
    <div>
      <h1 className="text-2xl font-semibold">Personas</h1>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {data?.map((agent) => (
          <Link
            key={agent.id}
            to={`/personas/${agent.slug}`}
            className="rounded border border-slate-200 bg-white p-4 hover:border-slate-400"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">{agent.name}</span>
              {agent.status === "stale" && (
                <span className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800">stale</span>
              )}
            </div>
            <p className="mt-1 text-sm text-slate-500">{agent.description}</p>
            <div className="mt-2 flex flex-wrap gap-1">
              {agent.tools.map((tool) => (
                <span key={tool} className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                  {tool}
                </span>
              ))}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
