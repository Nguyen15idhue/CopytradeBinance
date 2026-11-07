import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import {
  deleteView,
  getFunnelSummary,
  getSavedViews,
  getScreener,
  saveView,
  toQuery,
} from "../lib/api";
import type { ScreenerItem } from "../types/trader";

const TIER_LABELS: Record<string, string> = {
  high_upper: "High",
  qualified_upper: "Qualified",
  watch: "Watch",
  excluded: "Excluded",
};

const TIER_STYLES: Record<string, string> = {
  high_upper: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
  qualified_upper: "border-teal-500/40 bg-teal-500/10 text-teal-300",
  watch: "border-sky-500/40 bg-sky-500/10 text-sky-300",
  excluded: "border-amber-500/40 bg-amber-500/10 text-amber-300",
};

const RISK_STYLES: Record<string, string> = {
  critical: "text-red-300",
  high: "text-orange-300",
  medium: "text-amber-300",
  low: "text-sky-300",
  none: "text-slate-400",
  unknown: "text-slate-500",
};

const SORT_OPTIONS = [
  { value: "score", label: "Score" },
  { value: "confidence", label: "Confidence" },
  { value: "roi_90d", label: "ROI 90D" },
  { value: "mdd_90d", label: "MDD 90D" },
  { value: "sharpe", label: "Sharpe" },
  { value: "win_rate", label: "WinRate" },
  { value: "runtime_days", label: "Runtime" },
  { value: "current_copiers", label: "Copiers" },
  { value: "copy_aum", label: "Copy AUM" },
];

function number(value: number | null, digits = 2, suffix = ""): string {
  if (value === null || Number.isNaN(value)) return "N/A";
  return `${value.toFixed(digits)}${suffix}`;
}

function compact(value: number | null): string {
  if (value === null) return "N/A";
  return value.toLocaleString("vi-VN", { maximumFractionDigits: 0 });
}

function confidencePct(value: number | null): string {
  if (value === null) return "N/A";
  return `${Math.round(value * 100)}%`;
}

export default function ScreenerPage() {
  const [search, setSearch] = useState("");
  const [tier, setTier] = useState("high_upper");
  const [includeExcluded, setIncludeExcluded] = useState(false);
  const [roiMin, setRoiMin] = useState("");
  const [mddMax, setMddMax] = useState("");
  const [sharpeMin, setSharpeMin] = useState("");
  const [winRateMin, setWinRateMin] = useState("");
  const [runtimeMin, setRuntimeMin] = useState("");
  const [ordersMin, setOrdersMin] = useState("");
  const [leverageMax, setLeverageMax] = useState("");
  const [risk, setRisk] = useState("");
  const [sortBy, setSortBy] = useState("score");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [drawer, setDrawer] = useState<ScreenerItem | null>(null);
  const [viewName, setViewName] = useState("");

  const filters = useMemo(
    () => ({
      q: search,
      potential_tier: tier ? [tier] : [],
      include_excluded: includeExcluded,
      min_roi_90d: roiMin,
      max_mdd_90d: mddMax,
      min_sharpe: sharpeMin,
      min_win_rate: winRateMin,
      min_runtime_days: runtimeMin,
      min_total_orders: ordersMin,
      max_leverage: leverageMax,
      risk_level: risk ? [risk] : [],
      sort_by: sortBy,
      sort_dir: sortDir,
      page,
      page_size: 50,
    }),
    [
      search,
      tier,
      includeExcluded,
      roiMin,
      mddMax,
      sharpeMin,
      winRateMin,
      runtimeMin,
      ordersMin,
      leverageMax,
      risk,
      sortBy,
      sortDir,
      page,
    ],
  );

  const funnel = useQuery({ queryKey: ["funnel"], queryFn: getFunnelSummary });
  const screener = useQuery({ queryKey: ["screener", filters], queryFn: () => getScreener(filters) });
  const views = useQuery({ queryKey: ["saved-views"], queryFn: getSavedViews });

  function reset() {
    setSearch("");
    setTier("high_upper");
    setIncludeExcluded(false);
    setRoiMin("");
    setMddMax("");
    setSharpeMin("");
    setWinRateMin("");
    setRuntimeMin("");
    setOrdersMin("");
    setLeverageMax("");
    setRisk("");
    setSortBy("score");
    setSortDir("desc");
    setPage(1);
  }

  function applyView(filtersJson: Record<string, unknown>) {
    setSearch(String(filtersJson.q ?? ""));
    const tiers = filtersJson.potential_tier as string[] | undefined;
    setTier(tiers?.[0] ?? "");
    setIncludeExcluded(Boolean(filtersJson.include_excluded));
    setMddMax(String(filtersJson.max_mdd_90d ?? ""));
    setRoiMin(String(filtersJson.min_roi_90d ?? ""));
    setPage(1);
  }

  const data = screener.data;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Screener</h1>
          <p className="mt-2 text-slate-400">
            Lọc universe xuống shortlist theo score, rủi ro và chất lượng dữ liệu.
          </p>
        </div>
        {funnel.data ? (
          <div className="flex flex-wrap gap-2 text-sm">
            <span className="rounded-full border border-slate-700 px-3 py-1 text-slate-300">
              Universe {compact(funnel.data.universe)}
            </span>
            <span className="rounded-full border border-sky-500/40 bg-sky-500/10 px-3 py-1 text-sky-300">
              Watch {compact(funnel.data.watch + funnel.data.qualified + funnel.data.high)}
            </span>
            <span className="rounded-full border border-teal-500/40 bg-teal-500/10 px-3 py-1 text-teal-300">
              Qualified {compact(funnel.data.qualified + funnel.data.high)}
            </span>
            <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-emerald-300">
              High {compact(funnel.data.high)}
            </span>
          </div>
        ) : null}
      </div>

      <section className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="grid gap-3 md:grid-cols-4">
          <label className="text-sm text-slate-300">
            Tìm kiếm
            <input
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
              placeholder="nickname"
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
            />
          </label>
          <label className="text-sm text-slate-300">
            Tier
            <select
              value={tier}
              onChange={(event) => {
                setTier(event.target.value);
                setPage(1);
              }}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
            >
              <option value="">Tất cả (trừ excluded)</option>
              <option value="high_upper">High</option>
              <option value="qualified_upper">Qualified</option>
              <option value="watch">Watch</option>
              <option value="excluded">Excluded</option>
            </select>
          </label>
          <label className="text-sm text-slate-300">
            Risk
            <select
              value={risk}
              onChange={(event) => {
                setRisk(event.target.value);
                setPage(1);
              }}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
            >
              <option value="">Tất cả</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </label>
          <label className="text-sm text-slate-300">
            Sắp xếp
            <div className="mt-1 flex gap-2">
              <select
                value={sortBy}
                onChange={(event) => setSortBy(event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => setSortDir(sortDir === "desc" ? "asc" : "desc")}
                className="rounded-lg border border-slate-700 px-3 text-slate-300"
              >
                {sortDir === "desc" ? "↓" : "↑"}
              </button>
            </div>
          </label>
        </div>

        <div className="grid gap-3 md:grid-cols-6">
          <label className="text-xs uppercase tracking-wide text-slate-500">
            ROI ≥
            <input
              type="number"
              value={roiMin}
              onChange={(event) => { setRoiMin(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-100"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-slate-500">
            MDD ≤
            <input
              type="number"
              value={mddMax}
              onChange={(event) => { setMddMax(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-100"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-slate-500">
            Sharpe ≥
            <input
              type="number"
              value={sharpeMin}
              onChange={(event) => { setSharpeMin(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-100"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-slate-500">
            WinRate ≥
            <input
              type="number"
              value={winRateMin}
              onChange={(event) => { setWinRateMin(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-100"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-slate-500">
            Runtime ≥
            <input
              type="number"
              value={runtimeMin}
              onChange={(event) => { setRuntimeMin(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-100"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-slate-500">
            Orders ≥
            <input
              type="number"
              value={ordersMin}
              onChange={(event) => { setOrdersMin(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-100"
            />
          </label>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-sm">
          <label className="flex items-center gap-2 text-slate-300">
            <input
              type="checkbox"
              checked={includeExcluded}
              onChange={(event) => {
                setIncludeExcluded(event.target.checked);
                setPage(1);
              }}
            />
            Include excluded
          </label>
          <label className="text-slate-300">
            Leverage ≤
            <input
              type="number"
              value={leverageMax}
              onChange={(event) => setLeverageMax(event.target.value)}
              className="ml-2 w-20 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-slate-100"
            />
          </label>
          <button
            type="button"
            onClick={reset}
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-slate-300 hover:bg-slate-800"
          >
            Reset
          </button>
          <a
            href={`/api/v1/traders/export.csv?${toQuery(filters)}`}
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-slate-300 hover:bg-slate-800"
          >
            Export CSV
          </a>
          <div className="ml-auto flex items-center gap-2">
            <input
              value={viewName}
              onChange={(event) => setViewName(event.target.value)}
              placeholder="Tên view"
              className="w-32 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-slate-100"
            />
            <button
              type="button"
              disabled={!viewName.trim()}
              onClick={async () => {
                await saveView(viewName.trim(), filters);
                setViewName("");
                await views.refetch();
              }}
              className="rounded-lg bg-emerald-500 px-3 py-1.5 font-medium text-slate-950 disabled:opacity-50"
            >
              Lưu view
            </button>
          </div>
        </div>

        {views.data && views.data.length > 0 ? (
          <div className="flex flex-wrap gap-2 border-t border-slate-800 pt-3 text-sm">
            {views.data.map((view) => (
              <span key={view.id} className="flex items-center gap-1 rounded-full border border-slate-700 pl-3">
                <button
                  type="button"
                  onClick={() => applyView(view.filters)}
                  className="py-1 text-slate-300 hover:text-white"
                >
                  {view.name}
                </button>
                <button
                  type="button"
                  onClick={async () => {
                    await deleteView(view.id);
                    await views.refetch();
                  }}
                  className="px-2 text-slate-500 hover:text-red-300"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        ) : null}
      </section>

      <div className="flex items-center justify-between text-sm text-slate-400">
        <span>{data ? `${compact(data.total)} trader khớp` : "Đang tải..."}</span>
        {data ? (
          <span>
            Trang {data.page}/{totalPages} · score v{data.config_version}
          </span>
        ) : null}
      </div>

      {screener.isLoading ? (
        <div className="h-64 animate-pulse rounded-2xl bg-slate-900" />
      ) : screener.isError ? (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/5 p-5 text-red-300">
          Không tải được screener: {screener.error instanceof Error ? screener.error.message : "lỗi"}
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-center">
          <p className="text-slate-300">Không có trader khớp bộ lọc.</p>
          <div className="mt-4 flex flex-wrap justify-center gap-2 text-sm">
            <button type="button" onClick={() => setMddMax("")} className="rounded-lg border border-slate-700 px-3 py-1.5 text-slate-300">
              Bỏ filter MDD
            </button>
            <button type="button" onClick={() => setRuntimeMin("30")} className="rounded-lg border border-slate-700 px-3 py-1.5 text-slate-300">
              Runtime ≥ 30
            </button>
            <button type="button" onClick={() => setIncludeExcluded(true)} className="rounded-lg border border-slate-700 px-3 py-1.5 text-slate-300">
              Xem cả excluded
            </button>
          </div>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
          <table className="w-full min-w-[1100px] text-left text-sm">
            <thead className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-3">Trader</th>
                <th className="px-3 py-3">Tier</th>
                <th className="px-3 py-3">Score</th>
                <th className="px-3 py-3">Conf</th>
                <th className="px-3 py-3 text-right">ROI 90D</th>
                <th className="px-3 py-3 text-right">MDD</th>
                <th className="px-3 py-3 text-right">Sharpe</th>
                <th className="px-3 py-3 text-right">WinRate</th>
                <th className="px-3 py-3 text-right">Runtime</th>
                <th className="px-3 py-3 text-right">Copiers</th>
                <th className="px-3 py-3 text-right">Copy AUM</th>
                <th className="px-3 py-3 text-right">Lev</th>
                <th className="px-3 py-3">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {data.items.map((item) => (
                <tr key={item.id} className="hover:bg-slate-800/40">
                  <td className="px-3 py-3">
                    <Link to={`/traders/${item.id}`} className="text-slate-100 hover:text-emerald-300">
                      {item.nickname ?? item.id}
                    </Link>
                    <p className="text-xs text-slate-500">{item.portfolio_type ?? "N/A"}</p>
                  </td>
                  <td className="px-3 py-3">
                    <span className={`rounded-full border px-2 py-0.5 text-xs ${TIER_STYLES[item.potential_tier] ?? "border-slate-700 text-slate-300"}`}>
                      {TIER_LABELS[item.potential_tier] ?? item.potential_tier}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <button
                      type="button"
                      onClick={() => setDrawer(item)}
                      className="font-semibold text-slate-100 underline decoration-dotted hover:text-emerald-300"
                    >
                      {number(item.score, 1)}
                    </button>
                    <p className="text-xs text-slate-500">{item.band ?? "—"}</p>
                  </td>
                  <td className="px-3 py-3 text-slate-300">{confidencePct(item.confidence)}</td>
                  <td className="px-3 py-3 text-right text-slate-300">{number(item.roi_90d, 2, "%")}</td>
                  <td className={`px-3 py-3 text-right ${(item.mdd_90d ?? 0) > 20 ? "text-red-300" : "text-slate-300"}`}>
                    {number(item.mdd_90d, 2, "%")}
                  </td>
                  <td className="px-3 py-3 text-right text-slate-300">{number(item.sharpe)}</td>
                  <td className="px-3 py-3 text-right text-slate-300">
                    {number(item.win_rate_order_90d, 1, "%")}
                    {item.low_sample ? <span className="ml-1 text-amber-300">*</span> : null}
                  </td>
                  <td className="px-3 py-3 text-right text-slate-300">{number(item.runtime_days, 0)}</td>
                  <td className="px-3 py-3 text-right text-slate-300">{compact(item.current_copiers)}</td>
                  <td className="px-3 py-3 text-right text-slate-300">{compact(item.copy_aum)}</td>
                  <td className="px-3 py-3 text-right text-slate-300">{number(item.max_leverage, 1, "x")}</td>
                  <td className={`px-3 py-3 capitalize ${RISK_STYLES[item.risk_level ?? "unknown"] ?? ""}`}>
                    {item.risk_level ?? "unknown"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.total > data.page_size ? (
        <div className="flex justify-center gap-2">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 disabled:opacity-40"
          >
            Trang trước
          </button>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 disabled:opacity-40"
          >
            Trang sau
          </button>
        </div>
      ) : null}

      {drawer ? (
        <div className="fixed inset-0 z-40 flex justify-end bg-slate-950/70" onClick={() => setDrawer(null)}>
          <aside
            className="h-full w-full max-w-md overflow-y-auto border-l border-slate-800 bg-slate-900 p-5"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold">{drawer.nickname ?? drawer.id}</h2>
                <p className="text-sm text-slate-400">{drawer.band ?? "—"} · score {number(drawer.score, 1)}</p>
              </div>
              <button type="button" onClick={() => setDrawer(null)} className="text-slate-400">×</button>
            </div>
            <div className="mt-4 space-y-2">
              {Object.entries(drawer.breakdown.components ?? {}).map(([group, value]) => (
                <div key={group}>
                  <div className="flex justify-between text-sm">
                    <span className="capitalize text-slate-300">{group.replaceAll("_", " ")}</span>
                    <span className="text-slate-400">
                      {number(value.score, 1)} · w{value.weight}
                    </span>
                  </div>
                  <div className="mt-1 h-2 rounded bg-slate-800">
                    <div className="h-2 rounded bg-emerald-500" style={{ width: `${Math.min(value.score, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
            {drawer.breakdown.missing?.length ? (
              <p className="mt-4 text-xs text-amber-300">
                Thiếu thành phần: {drawer.breakdown.missing.join(", ")}
              </p>
            ) : null}
            {drawer.hard_flags.length ? (
              <p className="mt-2 text-xs text-red-300">Hard flags: {drawer.hard_flags.join(", ")}</p>
            ) : null}
            <Link
              to={`/traders/${drawer.id}`}
              className="mt-5 inline-block rounded-lg bg-emerald-500 px-3 py-2 text-sm font-medium text-slate-950"
            >
              Mở chi tiết
            </Link>
          </aside>
        </div>
      ) : null}
    </div>
  );
}
