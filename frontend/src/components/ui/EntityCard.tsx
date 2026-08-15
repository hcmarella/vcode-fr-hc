import type { ReactNode } from "react";
import { Link } from "react-router-dom";

const ACCENT_BORDER: Record<string, string> = {
  violet: "group-hover:border-violet-300",
  sky: "group-hover:border-sky-300",
  amber: "group-hover:border-amber-300",
  emerald: "group-hover:border-emerald-300",
};

interface EntityCardProps {
  to: string;
  accent?: keyof typeof ACCENT_BORDER;
  delayMs?: number;
  children: ReactNode;
}

// The shared list-item shape used by Personas/Skills/Commands/Knowledge --
// same hover lift + entrance animation everywhere so the four content types
// read as one system instead of four independently-styled pages.
export default function EntityCard({ to, accent, delayMs = 0, children }: EntityCardProps) {
  return (
    <Link
      to={to}
      style={{ animationDelay: `${delayMs}ms` }}
      className={`group block animate-fade-in-up rounded-xl border border-slate-200 bg-white p-4 opacity-0 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${accent ? ACCENT_BORDER[accent] : ""}`}
    >
      {children}
    </Link>
  );
}
