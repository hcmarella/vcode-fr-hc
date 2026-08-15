import { Link } from "react-router-dom";

import type { AgentResponse, CommandResponse, KnowledgeResponse, SkillResponse } from "../../api/types";
import Badge from "../ui/Badge";

interface StaleItem {
  name: string;
  to: string;
  kind: string;
}

interface NeedsAttentionPanelProps {
  personas?: AgentResponse[];
  skills?: SkillResponse[];
  commands?: CommandResponse[];
  knowledge?: KnowledgeResponse[];
}

// Real triage list, computed from data the page already fetched -- no extra
// backend call. This is the docs-writer/integration-reviewer personas'
// day-to-day: content marked "stale" by the sync engine because it stopped
// showing up in vcode-w-hc, but nobody's gone and cleaned it up here yet.
export default function NeedsAttentionPanel({
  personas,
  skills,
  commands,
  knowledge,
}: NeedsAttentionPanelProps) {
  const stale: StaleItem[] = [
    ...(personas ?? [])
      .filter((p) => p.status === "stale")
      .map((p) => ({ name: p.name, to: `/personas/${p.slug}`, kind: "Persona" })),
    ...(skills ?? [])
      .filter((s) => s.status === "stale")
      .map((s) => ({ name: s.name, to: `/skills/${s.slug}`, kind: "Skill" })),
    ...(commands ?? [])
      .filter((c) => c.status === "stale")
      .map((c) => ({ name: `/${c.slug}`, to: `/commands/${c.slug}`, kind: "Command" })),
    ...(knowledge ?? [])
      .filter((k) => k.status === "stale")
      .map((k) => ({ name: k.name, to: `/knowledge/${k.id}`, kind: "Knowledge" })),
  ];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-slate-900">Needs attention</h2>
        {stale.length > 0 && <Badge tone="amber">{stale.length} stale</Badge>}
      </div>
      <p className="mt-1 text-xs text-slate-400">
        Content that stopped showing up in the last sync of vcode-w-hc.
      </p>
      <ul className="mt-3 space-y-2">
        {stale.slice(0, 6).map((item) => (
          <li key={item.to} className="flex items-center justify-between gap-2 text-sm">
            <Link to={item.to} className="min-w-0 truncate text-slate-700 hover:text-slate-900 hover:underline">
              {item.name}
            </Link>
            <span className="shrink-0 text-xs text-slate-400">{item.kind}</span>
          </li>
        ))}
        {stale.length === 0 && <li className="text-sm text-slate-400">Nothing stale right now.</li>}
      </ul>
    </div>
  );
}
