import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { clearSession, getStoredUser } from "../lib/auth";
import ThemeToggle from "./ThemeToggle";

const navItems = [
  { to: "/", label: "Demo traders" },
  { to: "/data-health", label: "Data Health" },
  { to: "/screener", label: "Screener" },
  { to: "/ranking", label: "Ranking", phase: "Phase 4" },
  { to: "/compare", label: "Compare" },
  { to: "/risk", label: "Risk" },
  { to: "/settings", label: "Settings", phase: "Phase 5" },
];

export default function Layout() {
  const navigate = useNavigate();
  const user = getStoredUser();

  function logout() {
    clearSession();
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-app text-strong">
      <aside className="fixed inset-y-0 left-0 hidden w-60 border-r border-line bg-panel p-4 md:block">
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-widest text-accent">
            CopytradeBinance
          </p>
          <p className="mt-1 text-sm text-muted">Screener &amp; Risk</p>
        </div>
        <nav className="space-y-1">
          {navItems.map((item) =>
            item.phase ? (
              <div
                key={item.to}
                className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-faint"
                title={`${item.label} — ${item.phase}`}
              >
                <span>{item.label}</span>
                <span className="rounded bg-elevated px-1.5 py-0.5 text-[10px]">
                  {item.phase}
                </span>
              </div>
            ) : (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `block rounded-lg px-3 py-2 text-sm ${
                    isActive
                      ? "bg-emerald-500/10 text-accent"
                      : "text-body hover:bg-elevated"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ),
          )}
        </nav>
      </aside>

      <div className="md:pl-60">
        <header className="flex h-16 items-center justify-between border-b border-line bg-panel px-4 md:px-8">
          <div className="flex items-center gap-3 text-sm text-muted">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span>Dữ liệu demo — fixture Phase 0</span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <ThemeToggle />
            <span className="hidden text-muted sm:inline">{user?.email}</span>
            <span className="rounded-full border border-line px-2 py-0.5 text-xs uppercase text-muted">
              {user?.role}
            </span>
            <button
              type="button"
              onClick={logout}
              className="rounded-lg border border-line px-3 py-1.5 text-body hover:bg-elevated"
            >
              Đăng xuất
            </button>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 md:px-8 md:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
