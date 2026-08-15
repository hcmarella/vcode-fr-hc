import { Link } from "react-router-dom";

import type { KnowledgeResponse } from "../../api/types";
import Badge from "../ui/Badge";

interface KnowledgeSpotlightPanelProps {
  knowledge?: KnowledgeResponse[];
}

// The Business/Manager equivalent of NeedsAttentionPanel -- "which content is
// stale" is an execution task for developer/docs-writer roles, not
// actionable for a read-only audience. This surfaces what's actually useful
// to them instead: the team's most recently-updated knowledge.
export default function KnowledgeSpotlightPanel({ knowledge }: KnowledgeSpotlightPanelProps) {
  const recent = [...(knowledge ?? [])]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 5);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-sm font-medium text-slate-900">Team knowledge spotlight</h2>
      <p className="mt-1 text-xs text-slate-400">Most recently updated for your team.</p>
      <ul className="mt-3 space-y-2">
        {recent.map((entry) => (
          <li key={entry.id}>
            <Link
              to={`/knowledge/${entry.id}`}
              className="flex items-center justify-between gap-2 text-sm text-slate-700 hover:text-slate-900 hover:underline"
            >
              <span className="min-w-0 truncate">{entry.name}</span>
              <Badge>{entry.metadata_type}</Badge>
            </Link>
          </li>
        ))}
        {recent.length === 0 && <li className="text-sm text-slate-400">Nothing synced yet.</li>}
      </ul>
    </div>
  );
}
