import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { clearSession, getStoredUser } from "../lib/auth";

const navItems = [
  { to: "/", label: "Demo traders" },
  { to: "/data-health", label: "Data Health" },
  { to: "/screener", label: "Screener", phase: "Phase 3" },
  { to: "/ranking", label: "Ranking", phase: "Phase 3" },
  { to: "/compare", label: "Compare", phase: "Phase 4" },
  { to: "/risk", label: "Risk", phase: "Phase 4" },
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
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <aside className="fixed inset-y-0 left-0 hidden w-60 border-r border-slate-800 bg-slate-900/60 p-4 md:block">
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-widest text-emerald-400">
            CopytradeBinance
          </p>
          <p className="mt-1 text-sm text-slate-400">Screener &amp; Risk</p>
        </div>
        <nav className="space-y-1">
          {navItems.map((item) =>
            item.phase ? (
              <div
                key={item.to}
                className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-slate-500"
                title={`${item.label} — ${item.phase}`}
              >
                <span>{item.label}</span>
                <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px]">
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
                      ? "bg-emerald-500/10 text-emerald-300"
                      : "text-slate-300 hover:bg-slate-800"
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
        <header className="flex h-16 items-center justify-between border-b border-slate-800 bg-slate-900/40 px-4 md:px-8">
          <div className="flex items-center gap-3 text-sm text-slate-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span>Dữ liệu demo — fixture Phase 0</span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="hidden text-slate-400 sm:inline">{user?.email}</span>
            <span className="rounded-full border border-slate-700 px-2 py-0.5 text-xs uppercase text-slate-400">
              {user?.role}
            </span>
            <button
              type="button"
              onClick={logout}
              className="rounded-lg border border-slate-700 px-3 py-1.5 text-slate-300 hover:bg-slate-800"
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
