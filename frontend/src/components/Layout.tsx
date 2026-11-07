import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { NAV_LABELS } from "../i18n/vi";
import { clearSession, getStoredUser } from "../lib/auth";
import ThemeToggle from "./ThemeToggle";

type NavItem = { to: string; label: string; phase?: string };

const navItems: NavItem[] = [
  { to: "/", label: NAV_LABELS.home },
  { to: "/data-health", label: NAV_LABELS.dataHealth },
  { to: "/screener", label: NAV_LABELS.screener },
  { to: "/ranking", label: NAV_LABELS.ranking },
  { to: "/compare", label: NAV_LABELS.compare },
  { to: "/risk", label: NAV_LABELS.risk },
  { to: "/settings", label: NAV_LABELS.settings },
  { to: "/help", label: NAV_LABELS.help },
  { to: "/technical", label: NAV_LABELS.technical },
];

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="space-y-1">
      {navItems.map((item) =>
        item.phase ? (
          <div
            key={item.to}
            className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-faint"
            title={`${item.label} — ${item.phase}`}
          >
            <span>{item.label}</span>
            <span className="rounded bg-elevated px-1.5 py-0.5 text-[10px]">{item.phase}</span>
          </div>
        ) : (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              `block rounded-lg px-3 py-2 text-sm ${
                isActive ? "bg-emerald-500/10 text-accent" : "text-body hover:bg-elevated"
              }`
            }
          >
            {item.label}
          </NavLink>
        ),
      )}
    </nav>
  );
}

export default function Layout() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const [menuOpen, setMenuOpen] = useState(false);

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
          <p className="mt-1 text-sm text-muted">Bộ lọc &amp; phân tích rủi ro</p>
        </div>
        <NavList />
      </aside>

      {menuOpen ? (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-slate-950/60"
            onClick={() => setMenuOpen(false)}
            aria-hidden="true"
          />
          <aside className="relative h-full w-64 border-r border-line bg-panel p-4">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-accent">
                  CopytradeBinance
                </p>
                <p className="mt-1 text-sm text-muted">Bộ lọc &amp; phân tích rủi ro</p>
              </div>
              <button
                type="button"
                onClick={() => setMenuOpen(false)}
                aria-label="Đóng menu"
                className="rounded-lg border border-line px-2 py-1 text-muted"
              >
                ×
              </button>
            </div>
            <NavList onNavigate={() => setMenuOpen(false)} />
          </aside>
        </div>
      ) : null}

      <div className="md:pl-60">
        <header className="flex h-16 items-center justify-between gap-2 border-b border-line bg-panel px-4 md:px-8">
          <div className="flex min-w-0 items-center gap-2 sm:gap-3">
            <button
              type="button"
              onClick={() => setMenuOpen(true)}
              aria-label="Mở menu"
              className="rounded-lg border border-line px-2 py-1 text-body md:hidden"
            >
              ☰
            </button>
            <div className="hidden items-center gap-3 text-sm text-muted sm:flex">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              <span className="truncate">Dữ liệu demo — bộ dữ liệu mẫu Phase 0</span>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2 text-sm sm:gap-3">
            <ThemeToggle />
            <span className="hidden text-muted lg:inline">{user?.email}</span>
            <span className="hidden rounded-full border border-line px-2 py-0.5 text-xs uppercase text-muted sm:inline">
              {user?.role === "admin" ? "quản trị" : "chỉ xem"}
            </span>
            <button
              type="button"
              onClick={logout}
              className="whitespace-nowrap rounded-lg border border-line px-2 py-1.5 text-body hover:bg-elevated sm:px-3"
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
