import { NavLink, Outlet } from "react-router-dom";

import { useCurrentUser, useLogout } from "../../hooks/useAuth";
import AskWidget from "../chat/AskWidget";

const navItems = [
  { to: "/", label: "Home" },
  { to: "/about", label: "About" },
  { to: "/personas", label: "Personas" },
  { to: "/skills", label: "Skills" },
  { to: "/commands", label: "Commands" },
  { to: "/knowledge", label: "Knowledge" },
  { to: "/jira", label: "Jira" },
  { to: "/sessions", label: "Sessions" },
];

export default function AppShell() {
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-4">
          <span className="flex items-center gap-2 text-lg font-semibold">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-900 text-sm font-bold text-white">
              P
            </span>
            portal
          </span>
          <nav className="flex flex-1 gap-4 text-sm">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  isActive ? "font-medium text-slate-900" : "text-slate-500 hover:text-slate-900"
                }
              >
                {item.label}
              </NavLink>
            ))}
            {user?.role === "admin" && (
              <NavLink
                to="/admin/sync"
                className={({ isActive }) =>
                  isActive ? "font-medium text-slate-900" : "text-slate-500 hover:text-slate-900"
                }
              >
                Admin
              </NavLink>
            )}
          </nav>
          {user && (
            <div className="flex items-center gap-3 text-sm text-slate-500">
              <span>
                {user.name} · {user.team}
              </span>
              <button
                onClick={() => logout.mutate()}
                className="rounded border border-slate-300 px-2 py-1 text-slate-700 hover:bg-slate-100"
              >
                Log out
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
      <AskWidget />
    </div>
  );
}
