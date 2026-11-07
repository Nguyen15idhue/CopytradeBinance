import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import OnboardingBanner from "../components/OnboardingBanner";
import {
  BAND_LABELS,
  GROUP_LABELS,
  HARD_FLAG_LABELS,
  METRIC_LABELS,
  PORTFOLIO_TYPE_LABELS,
  RISK_LEVEL_LABELS,
  TIER_LABELS,
  label,
} from "../i18n/vi";

import {
  deleteView,
  getFunnelSummary,
  getSavedViews,
  getScreener,
  parseNlSearch,
  saveView,
  toQuery,
} from "../lib/api";
import {
  SCREENER_DEFAULTS,
  parseScreenerQuery,
  serializeScreenerParams,
  storeScreenerQuery,
} from "../lib/screenerQuery";
import type { ScreenerItem } from "../types/trader";

const TIER_STYLES: Record<string, string> = {
  high_upper: "border-emerald-500/40 bg-emerald-500/10 text-accent",
  qualified_upper: "border-teal-500/40 bg-teal-500/10 text-accent",
  watch: "border-sky-500/40 bg-sky-500/10 text-info",
  excluded: "border-amber-500/40 bg-amber-500/10 text-warn",
};

const RISK_STYLES: Record<string, string> = {
  critical: "text-danger",
  high: "text-warn",
  medium: "text-warn",
  low: "text-info",
  none: "text-muted",
  unknown: "text-faint",
};

const SORT_OPTIONS = [
  { value: "score", label: "Điểm" },
  { value: "confidence", label: "Độ tin cậy" },
  { value: "roi_90d", label: "ROI 90D" },
  { value: "mdd_90d", label: "MDD 90D" },
  { value: "sharpe", label: "Sharpe" },
  { value: "win_rate", label: "WinRate" },
  { value: "runtime_days", label: "Số ngày hoạt động" },
  { value: "current_copiers", label: "Số copier" },
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
  const [searchParams, setSearchParams] = useSearchParams();
  const [initial] = useState(() => parseScreenerQuery(searchParams));
  const [search, setSearch] = useState(initial.q);
  const [tier, setTier] = useState(initial.tier);
  const [includeExcluded, setIncludeExcluded] = useState(initial.include === "1");
  const [roiMin, setRoiMin] = useState(initial.roi_min);
  const [mddMax, setMddMax] = useState(initial.mdd_max);
  const [sharpeMin, setSharpeMin] = useState(initial.sharpe_min);
  const [winRateMin, setWinRateMin] = useState(initial.win_min);
  const [runtimeMin, setRuntimeMin] = useState(initial.runtime_min);
  const [ordersMin, setOrdersMin] = useState(initial.orders_min);
  const [leverageMax, setLeverageMax] = useState(initial.lev_max);
  const [risk, setRisk] = useState(initial.risk);
  const [minCopyMax, setMinCopyMax] = useState(initial.min_copy_max);
  const [nlText, setNlText] = useState("");
  const [nlChips, setNlChips] = useState<string[]>([]);
  const [nlAssumptions, setNlAssumptions] = useState<string[]>([]);
  const [nlPending, setNlPending] = useState<Record<string, unknown> | null>(null);
  const [nlError, setNlError] = useState<string | null>(null);
  const [nlBusy, setNlBusy] = useState(false);
  const [sortBy, setSortBy] = useState(initial.sort);
  const [sortDir, setSortDir] = useState<"asc" | "desc">(initial.dir as "asc" | "desc");
  const [page, setPage] = useState(Number(initial.page));
  const [drawer, setDrawer] = useState<ScreenerItem | null>(null);
  const [viewName, setViewName] = useState("");

  useEffect(() => {
    const params = serializeScreenerParams({
      ...SCREENER_DEFAULTS,
      q: search,
      tier,
      include: includeExcluded ? "1" : "",
      risk,
      roi_min: roiMin,
      mdd_max: mddMax,
      sharpe_min: sharpeMin,
      win_min: winRateMin,
      runtime_min: runtimeMin,
      orders_min: ordersMin,
      lev_max: leverageMax,
      min_copy_max: minCopyMax,
      sort: sortBy,
      dir: sortDir,
      page: String(page),
    });
    storeScreenerQuery(params.toString());
    setSearchParams(params, { replace: true });
  }, [
    search,
    tier,
    includeExcluded,
    risk,
    roiMin,
    mddMax,
    sharpeMin,
    winRateMin,
    runtimeMin,
    ordersMin,
    leverageMax,
    minCopyMax,
    sortBy,
    sortDir,
    page,
    setSearchParams,
  ]);

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
      max_min_copy_usd: minCopyMax,
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
      minCopyMax,
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
    setMinCopyMax("");
    setSortBy("score");
    setSortDir("desc");
    setPage(1);
    clearNl();
  }

  function clearNl() {
    setNlChips([]);
    setNlAssumptions([]);
    setNlPending(null);
    setNlError(null);
  }

  async function interpretNl() {
    if (!nlText.trim() || nlBusy) return;
    setNlBusy(true);
    setNlError(null);
    try {
      const result = await parseNlSearch(nlText.trim());
      setNlChips(result.chips ?? []);
      setNlAssumptions(result.assumptions ?? []);
      setNlPending(result.filters ?? null);
    } catch (err) {
      setNlError(err instanceof Error ? err.message : "Không diễn giải được mô tả");
    } finally {
      setNlBusy(false);
    }
  }

  function applyNl() {
    if (!nlPending) return;
    const get = (key: string) => nlPending[key];
    const levels = get("risk_level") as string[] | undefined;
    setRisk(levels?.[0] ?? "");
    setMddMax(get("max_mdd_90d") != null ? String(get("max_mdd_90d")) : "");
    setSharpeMin(get("min_sharpe") != null ? String(get("min_sharpe")) : "");
    setRuntimeMin(get("min_runtime_days") != null ? String(get("min_runtime_days")) : "");
    setLeverageMax(get("max_leverage") != null ? String(get("max_leverage")) : "");
    setMinCopyMax(get("min_copy_usd_max") != null ? String(get("min_copy_usd_max")) : "");
    const extra: string[] = [];
    if (get("has_slot")) extra.push("Còn slot: Screener chưa lọc slot — kiểm tra trong chat AI");
    if (get("min_score") != null) extra.push(`Điểm ≥ ${get("min_score")}: dùng sắp xếp Điểm giảm dần`);
    if (get("no_veto")) extra.push("Không veto: lọc thủ công trong bảng kết quả");
    setNlAssumptions((prev) => [...prev, ...extra]);
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
      <OnboardingBanner />
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Bộ lọc trader</h1>
          <p className="mt-2 text-muted">
            Lọc universe xuống danh sách ngắn theo điểm, rủi ro và chất lượng dữ liệu.
          </p>
        </div>
        {funnel.data ? (
          <div className="flex flex-wrap gap-2 text-sm">
            <span className="rounded-full border border-line px-3 py-1 text-body">
              Universe {compact(funnel.data.universe)}
            </span>
            <span className="rounded-full border border-sky-500/40 bg-sky-500/10 px-3 py-1 text-info">
              Theo dõi {compact(funnel.data.watch + funnel.data.qualified + funnel.data.high)}
            </span>
            <span className="rounded-full border border-teal-500/40 bg-teal-500/10 px-3 py-1 text-accent">
              Đạt {compact(funnel.data.qualified + funnel.data.high)}
            </span>
            <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-accent">
              Cao {compact(funnel.data.high)}
            </span>
          </div>
        ) : null}
      </div>

      <section className="space-y-3 rounded-2xl border border-line bg-panel p-4">
        <div>
          <h2 className="text-base font-semibold text-strong">Mô tả trader bạn muốn tìm</h2>
          <p className="text-sm text-muted">
            Ví dụ: “trader an toàn, còn slot, vốn tối thiểu dưới 100$”.
          </p>
        </div>
        <div className="flex flex-col gap-2 md:flex-row">
          <input
            value={nlText}
            onChange={(event) => setNlText(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") interpretNl();
            }}
            aria-label="Mô tả trader bạn muốn tìm"
            placeholder="Nhập mô tả bằng lời…"
            className="w-full rounded-lg border border-line bg-app px-3 py-2 text-strong"
          />
          <div className="flex shrink-0 gap-2">
            <button
              type="button"
              onClick={interpretNl}
              disabled={nlBusy || !nlText.trim()}
              className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              Diễn giải
            </button>
            <button
              type="button"
              onClick={applyNl}
              disabled={!nlPending}
              className="rounded-lg border border-line px-4 py-2 text-sm text-body disabled:opacity-50"
            >
              Áp dụng
            </button>
            <button
              type="button"
              onClick={() => {
                setNlText("");
                clearNl();
              }}
              className="rounded-lg border border-line px-3 py-2 text-sm text-muted"
            >
              Xóa
            </button>
          </div>
        </div>
        {nlError ? <p className="text-sm text-danger">{nlError}</p> : null}
        {nlChips.length > 0 ? (
          <div className="flex flex-wrap gap-2" aria-label="Điều kiện đã hiểu">
            {nlChips.map((chip) => (
              <span
                key={chip}
                className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-sm text-accent"
              >
                {chip}
              </span>
            ))}
          </div>
        ) : null}
        {nlAssumptions.length > 0 ? (
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
            {nlAssumptions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="space-y-3 rounded-2xl border border-line bg-panel p-4">
        <div className="grid gap-3 md:grid-cols-4">
          <label className="text-sm text-body">
            Tìm kiếm
            <input
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
              placeholder="biệt danh"
              className="mt-1 w-full rounded-lg border border-line bg-app px-3 py-2 text-strong"
            />
          </label>
          <label className="text-sm text-body">
            Nhóm
            <select
              value={tier}
              onChange={(event) => {
                setTier(event.target.value);
                setPage(1);
              }}
              className="mt-1 w-full rounded-lg border border-line bg-app px-3 py-2 text-strong"
            >
              <option value="">Tất cả (trừ bị loại)</option>
              <option value="high_upper">{TIER_LABELS.high_upper}</option>
              <option value="qualified_upper">{TIER_LABELS.qualified_upper}</option>
              <option value="watch">{TIER_LABELS.watch}</option>
              <option value="excluded">{TIER_LABELS.excluded}</option>
            </select>
          </label>
          <label className="text-sm text-body">
            Rủi ro
            <select
              value={risk}
              onChange={(event) => {
                setRisk(event.target.value);
                setPage(1);
              }}
              className="mt-1 w-full rounded-lg border border-line bg-app px-3 py-2 text-strong"
            >
              <option value="">Tất cả</option>
              <option value="critical">{RISK_LEVEL_LABELS.critical}</option>
              <option value="high">{RISK_LEVEL_LABELS.high}</option>
              <option value="medium">{RISK_LEVEL_LABELS.medium}</option>
              <option value="low">{RISK_LEVEL_LABELS.low}</option>
            </select>
          </label>
          <label className="text-sm text-body">
            Sắp xếp
            <div className="mt-1 flex gap-2">
              <select
                value={sortBy}
                onChange={(event) => setSortBy(event.target.value)}
                className="w-full rounded-lg border border-line bg-app px-3 py-2 text-strong"
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
                className="rounded-lg border border-line px-3 text-body"
              >
                {sortDir === "desc" ? "↓" : "↑"}
              </button>
            </div>
          </label>
        </div>

        <div className="grid gap-3 md:grid-cols-6">
          <label className="text-xs uppercase tracking-wide text-faint">
            ROI ≥
            <input
              type="number"
              value={roiMin}
              onChange={(event) => { setRoiMin(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-line bg-app px-2 py-1.5 text-sm text-strong"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-faint">
            MDD ≤
            <input
              type="number"
              value={mddMax}
              onChange={(event) => { setMddMax(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-line bg-app px-2 py-1.5 text-sm text-strong"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-faint">
            Sharpe ≥
            <input
              type="number"
              value={sharpeMin}
              onChange={(event) => { setSharpeMin(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-line bg-app px-2 py-1.5 text-sm text-strong"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-faint">
            WinRate ≥
            <input
              type="number"
              value={winRateMin}
              onChange={(event) => { setWinRateMin(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-line bg-app px-2 py-1.5 text-sm text-strong"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-faint">
            Số ngày hoạt động ≥
            <input
              type="number"
              value={runtimeMin}
              onChange={(event) => { setRuntimeMin(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-line bg-app px-2 py-1.5 text-sm text-strong"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-faint">
            Số lệnh ≥
            <input
              type="number"
              value={ordersMin}
              onChange={(event) => { setOrdersMin(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-line bg-app px-2 py-1.5 text-sm text-strong"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-faint">
            Vốn tối thiểu ≤ ($)
            <input
              type="number"
              value={minCopyMax}
              onChange={(event) => { setMinCopyMax(event.target.value); setPage(1); }}
              className="mt-1 w-full rounded-lg border border-line bg-app px-2 py-1.5 text-sm text-strong"
            />
          </label>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-sm">
          <label className="flex items-center gap-2 text-body">
            <input
              type="checkbox"
              checked={includeExcluded}
              onChange={(event) => {
                setIncludeExcluded(event.target.checked);
                setPage(1);
              }}
            />
            Bao gồm bị loại
          </label>
          <label className="text-body">
            Đòn bẩy ≤
            <input
              type="number"
              value={leverageMax}
              onChange={(event) => setLeverageMax(event.target.value)}
              className="ml-2 w-20 rounded border border-line bg-app px-2 py-1 text-strong"
            />
          </label>
          <button
            type="button"
            onClick={reset}
            className="rounded-lg border border-line px-3 py-1.5 text-body hover:bg-elevated"
          >
            Đặt lại
          </button>
          <a
            href={`/api/v1/traders/export.csv?${toQuery(filters)}`}
            className="rounded-lg border border-line px-3 py-1.5 text-body hover:bg-elevated"
          >
            Xuất CSV
          </a>
          <div className="ml-auto flex items-center gap-2">
            <input
              value={viewName}
              onChange={(event) => setViewName(event.target.value)}
              placeholder="Tên bộ lọc"
              className="w-32 rounded border border-line bg-app px-2 py-1 text-strong"
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
              Lưu bộ lọc
            </button>
          </div>
        </div>

        {views.data && views.data.length > 0 ? (
          <div className="flex flex-wrap gap-2 border-t border-line pt-3 text-sm">
            {views.data.map((view) => (
              <span key={view.id} className="flex items-center gap-1 rounded-full border border-line pl-3">
                <button
                  type="button"
                  onClick={() => applyView(view.filters)}
                  className="py-1 text-body hover:text-white"
                >
                  {view.name}
                </button>
                <button
                  type="button"
                  onClick={async () => {
                    await deleteView(view.id);
                    await views.refetch();
                  }}
                  className="px-2 text-faint hover:text-danger"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        ) : null}
      </section>

      <div className="flex items-center justify-between text-sm text-muted">
        <span>{data ? `${compact(data.total)} trader khớp` : "Đang tải..."}</span>
        {data ? (
          <span>
            Trang {data.page}/{totalPages} · điểm v{data.config_version}
          </span>
        ) : null}
      </div>

      {screener.isLoading ? (
        <div className="h-64 animate-pulse rounded-2xl bg-panel" />
      ) : screener.isError ? (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/5 p-5 text-danger">
          Không tải được screener: {screener.error instanceof Error ? screener.error.message : "lỗi"}
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="rounded-2xl border border-line bg-panel p-8 text-center">
          <p className="text-body">Không có trader khớp bộ lọc.</p>
          <div className="mt-4 flex flex-wrap justify-center gap-2 text-sm">
            <button type="button" onClick={() => setMddMax("")} className="rounded-lg border border-line px-3 py-1.5 text-body">
              Bỏ lọc MDD
            </button>
            <button type="button" onClick={() => setRuntimeMin("30")} className="rounded-lg border border-line px-3 py-1.5 text-body">
              Số ngày ≥ 30
            </button>
            <button type="button" onClick={() => setIncludeExcluded(true)} className="rounded-lg border border-line px-3 py-1.5 text-body">
              Xem cả bị loại
            </button>
          </div>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-line bg-panel">
          <table className="w-full min-w-[1100px] text-left text-sm">
            <thead className="border-b border-line text-xs uppercase tracking-wide text-faint">
              <tr>
                <th className="px-3 py-3">Trader</th>
                <th className="px-3 py-3">Nhóm</th>
                <th className="px-3 py-3">Điểm</th>
                <th className="px-3 py-3">Tin cậy</th>
                <th className="px-3 py-3 text-right">ROI 90D</th>
                <th className="px-3 py-3 text-right">MDD</th>
                <th className="px-3 py-3 text-right">Sharpe</th>
                <th className="px-3 py-3 text-right">WinRate</th>
                <th className="px-3 py-3 text-right">Số ngày</th>
                <th className="px-3 py-3 text-right">Số copier</th>
                <th className="px-3 py-3 text-right">Copy AUM</th>
                <th className="px-3 py-3 text-right">Đòn bẩy</th>
                <th className="px-3 py-3">Rủi ro</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.items.map((item) => (
                <tr key={item.id} className="hover:bg-elevated">
                  <td className="px-3 py-3">
                    <Link to={`/traders/${item.id}`} className="text-strong hover:text-accent">
                      {item.nickname ?? item.id}
                    </Link>
                    <p className="text-xs text-faint">
                      {label(PORTFOLIO_TYPE_LABELS, item.portfolio_type, "Chưa rõ")}
                    </p>
                  </td>
                  <td className="px-3 py-3">
                    <span className={`whitespace-nowrap rounded-full border px-2 py-0.5 text-xs ${TIER_STYLES[item.potential_tier] ?? "border-line text-body"}`}>
                      {label(TIER_LABELS, item.potential_tier, "Chưa rõ")}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <button
                      type="button"
                      onClick={() => setDrawer(item)}
                      className="font-semibold text-strong hover:text-accent hover:underline"
                    >
                      {number(item.score, 1)}
                    </button>
                    <p className="text-xs text-faint">
                      {label(BAND_LABELS, item.band, "—")}
                    </p>
                  </td>
                  <td className="px-3 py-3 text-body">{confidencePct(item.confidence)}</td>
                  <td className="px-3 py-3 text-right text-body">{number(item.roi_90d, 2, "%")}</td>
                  <td className={`px-3 py-3 text-right ${(item.mdd_90d ?? 0) > 20 ? "text-danger" : "text-body"}`}>
                    {number(item.mdd_90d, 2, "%")}
                  </td>
                  <td className="px-3 py-3 text-right text-body">{number(item.sharpe)}</td>
                  <td className="px-3 py-3 text-right text-body">
                    {number(item.win_rate_order_90d, 1, "%")}
                    {item.low_sample ? <span className="ml-1 text-warn">*</span> : null}
                  </td>
                  <td className="px-3 py-3 text-right text-body">{number(item.runtime_days, 0)}</td>
                  <td className="px-3 py-3 text-right text-body">{compact(item.current_copiers)}</td>
                  <td className="px-3 py-3 text-right text-body">{compact(item.copy_aum)}</td>
                  <td className="px-3 py-3 text-right text-body">{number(item.max_leverage, 1, "x")}</td>
                  <td className={`px-3 py-3 ${RISK_STYLES[item.risk_level ?? "unknown"] ?? ""}`}>
                    {label(RISK_LEVEL_LABELS, item.risk_level, "Chưa rõ")}
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
            className="rounded-lg border border-line px-3 py-1.5 text-sm text-body disabled:opacity-40"
          >
            Trang trước
          </button>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
            className="rounded-lg border border-line px-3 py-1.5 text-sm text-body disabled:opacity-40"
          >
            Trang sau
          </button>
        </div>
      ) : null}

      {drawer ? (
        <div className="fixed inset-0 z-40 flex justify-end bg-app/70" onClick={() => setDrawer(null)}>
          <aside
            className="h-full w-full max-w-md overflow-y-auto border-l border-line bg-panel p-5"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold">{drawer.nickname ?? drawer.id}</h2>
                <p className="text-sm text-muted">
                  {label(BAND_LABELS, drawer.band, "—")} · điểm {number(drawer.score, 1)}
                </p>
              </div>
              <button type="button" onClick={() => setDrawer(null)} className="text-muted">×</button>
            </div>
            <div className="mt-4 space-y-2">
              {Object.entries(drawer.breakdown.components ?? {}).map(([group, value]) => (
                <div key={group}>
                  <div className="flex justify-between text-sm">
                    <span className="text-body">{label(GROUP_LABELS, group, group)}</span>
                    <span className="text-muted">
                      {number(value.score, 1)} · trọng số {value.weight}
                    </span>
                  </div>
                  <div className="mt-1 h-2 rounded bg-elevated">
                    <div className="h-2 rounded bg-emerald-500" style={{ width: `${Math.min(value.score, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
            {drawer.breakdown.missing?.length ? (
              <p className="mt-4 text-xs text-warn">
                Thiếu thành phần: {drawer.breakdown.missing.map((key) => label(METRIC_LABELS, key, key)).join(", ")}
              </p>
            ) : null}
            {drawer.hard_flags.length ? (
              <p className="mt-2 text-xs text-danger">
                Cờ cứng: {drawer.hard_flags.map((flag) => label(HARD_FLAG_LABELS, flag, flag)).join(", ")}
              </p>
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
