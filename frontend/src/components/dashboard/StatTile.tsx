import { Link } from "react-router-dom";

// Tailwind's JIT scanner needs full static class strings, not
// template-interpolated ones (`bg-${accent}-500` would never match anything
// at build time) -- so accent maps to a whole class here rather than being
// spliced into one.
const ACCENT_BAR: Record<string, string> = {
  violet: "bg-violet-500",
  sky: "bg-sky-500",
  amber: "bg-amber-500",
  emerald: "bg-emerald-500",
};

interface StatTileProps {
  label: string;
  value: number | undefined;
  to: string;
  accent: keyof typeof ACCENT_BAR;
  delayMs?: number;
}

export default function StatTile({ label, value, to, accent, delayMs = 0 }: StatTileProps) {
  return (
    <Link
      to={to}
      style={{ animationDelay: `${delayMs}ms` }}
      className="group relative overflow-hidden rounded-xl border border-slate-200 bg-white p-4 opacity-0 shadow-sm animate-fade-in-up transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <div
        className={`absolute inset-x-0 top-0 h-1 ${ACCENT_BAR[accent]} opacity-70 transition group-hover:opacity-100`}
      />
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold tabular-nums text-slate-900">
        {value === undefined ? (
          <span className="inline-block h-8 w-12 animate-pulse rounded bg-slate-100 align-middle" />
        ) : (
          value
        )}
      </p>
    </Link>
  );
}
