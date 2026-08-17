import { useQuery } from "@tanstack/react-query";

import { commandsApi, knowledgeApi, personasApi, skillsApi } from "../api/content";
import CategoryBarChart from "../components/charts/CategoryBarChart";
import HeroBanner from "../components/dashboard/HeroBanner";
import KnowledgeSpotlightPanel from "../components/dashboard/KnowledgeSpotlightPanel";
import MyWorkPanel from "../components/dashboard/MyWorkPanel";
import NeedsAttentionPanel from "../components/dashboard/NeedsAttentionPanel";
import SyncStatusBadge from "../components/dashboard/SyncStatusBadge";
import StatTile from "../components/dashboard/StatTile";
import ValueDeliveredPanel from "../components/dashboard/ValueDeliveredPanel";
import Badge from "../components/ui/Badge";
import { useCurrentUser } from "../hooks/useAuth";

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export default function HomePage() {
  const { data: user } = useCurrentUser();

  const personas = useQuery({ queryKey: ["personas"], queryFn: personasApi.list });
  const skills = useQuery({ queryKey: ["skills"], queryFn: skillsApi.list });
  const commands = useQuery({ queryKey: ["commands"], queryFn: commandsApi.list });
  const knowledge = useQuery({ queryKey: ["knowledge"], queryFn: knowledgeApi.list });

  const contentMix = [
    { label: "Personas", value: personas.data?.length ?? 0 },
    { label: "Skills", value: skills.data?.length ?? 0 },
    { label: "Commands", value: commands.data?.length ?? 0 },
    { label: "Knowledge", value: knowledge.data?.length ?? 0 },
  ];
  const contentLoaded = personas.data && skills.data && commands.data && knowledge.data;
  // Separate entry per role: developer/admin get the execution-focused view
  // (stale-content triage, skill browsing); business/manager get a
  // read-oriented rollup instead -- triaging stale sync content isn't
  // actionable for them, so it's replaced rather than just also-shown.
  const isTechnical = user?.role === "developer" || user?.role === "admin";

  return (
    <div>
      <HeroBanner imageQuery="abstract technology network">
        <div className="flex items-center gap-2">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            {user?.team} workspace
          </p>
          {user && <Badge tone="violet">{user.role}</Badge>}
        </div>
        <h1 className="mt-1 text-3xl font-semibold">
          {greeting()}
          {user ? `, ${user.name.split(" ")[0]}` : ""}
        </h1>
        <p className="mt-2 max-w-xl text-sm text-slate-300">
          Personas, skills, commands, and team knowledge synced live from vcode-w-hc. Ask the
          portal anything in the chat widget, or browse below.
        </p>
        <div className="mt-4">
          <SyncStatusBadge />
        </div>
      </HeroBanner>

      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatTile
          label="Personas"
          value={personas.data?.length}
          to="/personas"
          accent="violet"
          delayMs={0}
        />
        <StatTile label="Skills" value={skills.data?.length} to="/skills" accent="sky" delayMs={75} />
        <StatTile
          label="Commands"
          value={commands.data?.length}
          to="/commands"
          accent="amber"
          delayMs={150}
        />
        <StatTile
          label="Knowledge"
          value={knowledge.data?.length}
          to="/knowledge"
          accent="emerald"
          delayMs={225}
        />
      </div>

      <div
        className="mt-6 grid animate-fade-in-up gap-4 opacity-0 sm:grid-cols-2"
        style={{ animationDelay: "260ms" }}
      >
        <ValueDeliveredPanel />
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-medium text-slate-900">Content mix</h2>
          {contentLoaded ? (
            <CategoryBarChart data={contentMix} />
          ) : (
            <div className="mt-3 h-[180px] animate-pulse rounded bg-slate-50" />
          )}
        </div>
      </div>

      <div
        className="mt-4 grid animate-fade-in-up gap-4 opacity-0 sm:grid-cols-2"
        style={{ animationDelay: "300ms" }}
      >
        <MyWorkPanel />
        {isTechnical ? (
          <NeedsAttentionPanel
            personas={personas.data}
            skills={skills.data}
            commands={commands.data}
            knowledge={knowledge.data}
          />
        ) : (
          <KnowledgeSpotlightPanel knowledge={knowledge.data} />
        )}
      </div>

      <div
        className="mt-4 animate-fade-in-up opacity-0"
        style={{ animationDelay: "375ms" }}
      >
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-medium text-slate-900">Available skills</h2>
          <ul className="mt-3 space-y-2">
            {(skills.data ?? []).slice(0, 5).map((s) => (
              <li key={s.id} className="text-sm">
                <span className="font-medium text-slate-700">{s.name}</span>
                <p className="truncate text-xs text-slate-400">{s.description}</p>
              </li>
            ))}
            {skills.data?.length === 0 && (
              <li className="text-sm text-slate-400">Nothing synced yet.</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
