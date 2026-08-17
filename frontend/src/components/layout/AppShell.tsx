import { NavLink, Outlet, useLocation } from "react-router-dom";

import { useCurrentUser, useLogout } from "../../hooks/useAuth";
import AskWidget from "../chat/AskWidget";
import SyncStatusBadge from "../dashboard/SyncStatusBadge";

interface NavItem {
  to: string;
  label: string;
  icon: string;
  end?: boolean;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  { label: "Workspace", items: [{ to: "/", label: "Home", icon: "🏠", end: true }] },
  {
    label: "Content",
    items: [
      { to: "/personas", label: "Personas", icon: "🧑‍💼" },
      { to: "/skills", label: "Skills", icon: "🛠️" },
      { to: "/commands", label: "Commands", icon: "⌘" },
      { to: "/knowledge", label: "Knowledge", icon: "📚" },
      { to: "/about", label: "About", icon: "ℹ️" },
    ],
  },
  {
    label: "Integrations",
    items: [
      { to: "/jira", label: "Jira", icon: "🎫" },
      { to: "/reports", label: "Reports", icon: "📊" },
    ],
  },
  { label: "Team", items: [{ to: "/sessions", label: "Sessions", icon: "💬" }] },
];

const PAGE_TITLES: Record<string, string> = {
  "/": "Home",
  "/about": "About",
  "/personas": "Personas",
  "/skills": "Skills",
  "/commands": "Commands",
  "/knowledge": "Knowledge",
  "/jira": "Jira",
  "/reports": "Reports",
  "/sessions": "Sessions",
  "/admin/sync": "Sync administration",
};

function currentTitle(pathname: string): string {
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];
  const base = "/" + pathname.split("/")[1];
  return PAGE_TITLES[base] ?? "Portal";
}

export default function AppShell() {
  const { data: user } = useCurrentUser();
  const logout = useLogout();
  const location = useLocation();

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      <aside className="flex w-60 flex-col border-r border-slate-200 bg-white">
        <div className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-sm font-bold text-white">
            P
          </span>
          <span className="text-base font-semibold">portal</span>
        </div>

        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
          {NAV_GROUPS.map((group) => (
            <div key={group.label}>
              <p className="px-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                {group.label}
              </p>
              <div className="mt-1 space-y-0.5">
                {group.items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    className={({ isActive }) =>
                      `flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition ${
                        isActive
                          ? "bg-slate-900 font-medium text-white"
                          : "text-slate-600 hover:bg-slate-100"
                      }`
                    }
                  >
                    <span className="text-base leading-none">{item.icon}</span>
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}

          {user?.role === "admin" && (
            <div>
              <p className="px-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Admin
              </p>
              <div className="mt-1 space-y-0.5">
                <NavLink
                  to="/admin/sync"
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition ${
                      isActive
                        ? "bg-slate-900 font-medium text-white"
                        : "text-slate-600 hover:bg-slate-100"
                    }`
                  }
                >
                  <span className="text-base leading-none">⚙️</span>
                  Sync admin
                </NavLink>
              </div>
            </div>
          )}
        </nav>

        {user && (
          <div className="border-t border-slate-200 p-3">
            <div className="flex items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-xs text-slate-500">
              <div className="min-w-0">
                <p className="truncate font-medium text-slate-700">{user.name}</p>
                <p className="truncate capitalize">{user.team}</p>
              </div>
              <button
                onClick={() => logout.mutate()}
                className="shrink-0 rounded border border-slate-300 px-2 py-1 text-slate-600 hover:bg-slate-100"
              >
                Log out
              </button>
            </div>
          </div>
        )}
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white/80 px-6 py-3 backdrop-blur">
          <span className="text-sm font-medium text-slate-500">{currentTitle(location.pathname)}</span>
          <SyncStatusBadge />
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
          <Outlet />
        </main>
      </div>
      <AskWidget />
    </div>
  );
}
