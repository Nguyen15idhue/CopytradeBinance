import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getPerformance,
  getPositions,
  getRisk,
  getScore,
  getTrades,
  getTrader,
  getTransfers,
} from "../lib/api";
import type { Metric, PositionRow } from "../types/trader";

const REASON_LABELS: Record<string, string> = {
  runtime_lt_30: "Runtime < 30 ngày",
  no_trade_7d: "Không giao dịch 7 ngày",
  roi_le_0: "ROI ≤ 0",
  pnl_le_0: "PnL ≤ 0",
  winrate_lt_40: "WinRate < 40%",
  mdd_gt_40: "MDD > 40%",
  aum_lt_5000: "AUM < 5.000",
  no_slots: "Hết slot copy",
  total_orders_lt_threshold: "Không đủ totalOrder cho tier",
};

const FLAG_LABELS: Record<string, string> = {
  missing_sharpe: "Thiếu Sharpe",
  missing_mdd: "Thiếu MDD",
  missing_benchmark: "Chưa có benchmark",
  no_copiers: "Không có copier",
  low_sample: "Mẫu giao dịch nhỏ",
  insufficient_positions: "Thiếu mẫu vị thế",
  missing_trades: "Chưa có trade history",
  derived_unavailable: "Chỉ số derived chưa có",
};

const TIER_STYLES: Record<string, string> = {
  high_upper: "border-emerald-500/40 bg-emerald-500/10 text-accent",
  qualified_upper: "border-teal-500/40 bg-teal-500/10 text-accent",
  watch: "border-sky-500/40 bg-sky-500/10 text-info",
  excluded: "border-amber-500/40 bg-amber-500/10 text-warn",
};

const METRIC_HELP: Record<string, string> = {
  roi_90d: "ROI published 90D từ Binance performance.",
  mdd_90d: "Max drawdown published; không tự tính từ chartItems.",
  sharpe: "Sharpe published; null nghĩa là N/A, không chấm 0.",
  win_rate_order: "winOrders / totalOrder của performance.",
  profit_factor: "Tổng lãi / |tổng lỗ| từ position-history; null nếu mẫu < 5.",
  max_leverage: "Leverage lớn nhất trong position-history.",
  avg_holding: "Thời gian giữ vị thế trung bình (derived).",
  copier_pnl: "PnL của copier theo performance.",
  copy_aum: "Vốn copier hiện tại từ detail.",
  copiers: "Số copier hiện tại / slot tối đa.",
};

function fmt(value: unknown, digits = 2, suffix = ""): string {
  const number = typeof value === "number" ? value : Number(value);
  if (value === null || value === undefined || Number.isNaN(number) || !Number.isFinite(number)) {
    return "N/A";
  }
  return `${number.toFixed(digits)}${suffix}`;
}

function money(value: unknown): string {
  const number = typeof value === "number" ? value : Number(value);
  if (value === null || value === undefined || Number.isNaN(number)) return "N/A";
  return number.toLocaleString("vi-VN", { maximumFractionDigits: 0 });
}

function MetricCard({ metric }: { metric: Metric }) {
  const numeric = metric.value === null ? null : Number(metric.value);
  const noCopier = metric.key === "copy_aum" && numeric === 0;
  return (
    <div
      className="rounded-xl border border-line bg-panel p-4"
      title={`${METRIC_HELP[metric.key] ?? metric.label} — nguồn: ${metric.source}${
        metric.window ? ` · cửa sổ ${metric.window}` : ""
      }${metric.note ? ` · ${metric.note}` : ""}`}
    >
      <p className="text-xs uppercase tracking-wide text-faint">{metric.label}</p>
      <p className="mt-2 text-2xl font-semibold">
        {noCopier ? "0" : fmt(numeric, 2, metric.unit === "%" ? "%" : "")}
        {metric.unit && numeric !== null && metric.unit !== "%" ? (
          <span className="ml-1 text-sm font-normal text-muted">{metric.unit}</span>
        ) : null}
      </p>
      <p className="mt-1 text-xs text-faint">
        {noCopier ? "Không có copier" : metric.note ?? metric.source}
        {metric.window ? ` · ${metric.window}` : ""}
      </p>
    </div>
  );
}

function drawdownSeries(chart: Array<{ date_time: number; value: number }>) {
  let peak = 0;
  return chart.map((point) => {
    const equity = 1 + (point.value ?? 0) / 100;
    peak = Math.max(peak, equity);
    const drawdown = peak > 0 ? ((peak - equity) / peak) * 100 : 0;
    return {
      date: new Date(point.date_time).toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" }),
      roi: point.value,
      drawdown: -Math.max(drawdown, 0),
    };
  });
}

function pnlHistogram(positions: PositionRow[]) {
  const values = positions
    .map((row) => row.closing_pnl)
    .filter((value): value is number => value !== null);
  if (!values.length) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const buckets = 7;
  const width = (max - min) / buckets || 1;
  const counts = Array.from({ length: buckets }, (_, index) => ({
    label: `${Math.round(min + index * width)}`,
    count: 0,
  }));
  for (const value of values) {
    const index = Math.min(buckets - 1, Math.max(0, Math.floor((value - min) / width)));
    counts[index].count += 1;
  }
  return counts;
}

export default function TraderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const enabled = Boolean(id);

  const trader = useQuery({ queryKey: ["trader", id], queryFn: () => getTrader(id!), enabled, retry: 0 });
  const performance = useQuery({ queryKey: ["perf", id], queryFn: () => getPerformance(id!), enabled });
  const score = useQuery({ queryKey: ["score", id], queryFn: () => getScore(id!), enabled });
  const risk = useQuery({ queryKey: ["risk", id], queryFn: () => getRisk(id!), enabled });
  const positions = useQuery({ queryKey: ["positions", id], queryFn: () => getPositions(id!, 1, 200), enabled });
  const trades = useQuery({ queryKey: ["trades", id], queryFn: () => getTrades(id!, 1, 10), enabled });
  const transfers = useQuery({ queryKey: ["transfers", id], queryFn: () => getTransfers(id!), enabled });

  if (trader.isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-32 animate-pulse rounded-2xl bg-panel" />
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          {Array.from({ length: 10 }).map((_, index) => (
            <div key={index} className="h-24 animate-pulse rounded-xl bg-panel" />
          ))}
        </div>
      </div>
    );
  }

  if (trader.isError || !trader.data) {
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/5 p-6">
        <h1 className="text-lg font-semibold text-danger">Không tải được trader</h1>
        <p className="mt-2 text-sm text-muted">
          {trader.error instanceof Error ? trader.error.message : "Lỗi không xác định"}
        </p>
        <Link to="/screener" className="mt-4 inline-block text-sm text-accent">
          ← Về Screener
        </Link>
      </div>
    );
  }

  const data = trader.data;
  const tierClass = TIER_STYLES[data.tier] ?? "border-line bg-elevated text-body";
  const series = drawdownSeries(performance.data?.chart ?? []);
  const histogram = pnlHistogram(positions.data?.items ?? []);
  const missing = [
    ...(data.flags ?? []),
    performance.data?.benchmark === null ? "missing_benchmark" : null,
    "open_positions_unavailable",
    "per_copier_unavailable",
    "funding_unavailable",
  ].filter(Boolean) as string[];

  return (
    <div className="space-y-6">
      <Link to="/screener" className="text-sm text-muted hover:text-strong">
        ← Screener
      </Link>

      <section className="rounded-2xl border border-line bg-panel p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold">{data.trader.nickname ?? data.trader.id}</h1>
              <span className={`rounded-full border px-2.5 py-0.5 text-xs uppercase ${tierClass}`}>
                {data.tier}
              </span>
              <span className="rounded-full border border-line px-2.5 py-0.5 text-xs text-muted">
                {data.trader.portfolio_type ?? "N/A"}
              </span>
              <span className="rounded-full border border-line px-2.5 py-0.5 text-xs text-muted">
                {data.trader.status ?? "N/A"}
              </span>
              {risk.data?.risk_level ? (
                <span className="rounded-full border border-orange-500/40 bg-orange-500/10 px-2.5 py-0.5 text-xs capitalize text-warn">
                  risk {risk.data.risk_level}
                </span>
              ) : null}
            </div>
            <p className="mt-2 max-w-2xl text-sm text-muted">
              {data.trader.description ?? "Không có mô tả"}
            </p>
            <p className="mt-2 font-mono text-xs text-faint">{data.trader.id}</p>
          </div>
          <div className="flex gap-6 text-right">
            <div>
              <p className="text-xs uppercase tracking-wide text-faint">Score</p>
              <p className="text-2xl font-semibold">{fmt(score.data?.score ?? null, 1)}</p>
              <p className="text-xs text-faint">{score.data?.band ?? "—"} · v{score.data?.config_version ?? 1}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-faint">Độ tin cậy</p>
              <p className="text-2xl font-semibold">{Math.round(data.confidence * 100)}%</p>
              <p className="text-xs text-faint">
                {data.provenance.source ?? "N/A"} · {data.provenance.window}
              </p>
            </div>
          </div>
        </div>

        {data.tier === "excluded" ? (
          <div className="mt-5 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
            <p className="text-sm font-medium text-warn">Trader bị loại khỏi shortlist</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {data.reasons.map((reason) => (
                <span key={reason} className="rounded-full border border-amber-500/30 px-2.5 py-1 text-xs text-warn">
                  {REASON_LABELS[reason] ?? reason}
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-faint">10 chỉ số cốt lõi</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          {data.metrics.map((metric) => (
            <MetricCard key={metric.key} metric={metric} />
          ))}
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-2xl border border-line bg-panel p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">ROI lũy kế</h2>
          <p className="mt-1 text-xs text-faint">{performance.data?.chart_note ?? "Đang tải..."}</p>
          <div className="mt-3 h-56">
            {series.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={series}>
                  <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fill: "var(--text-faint)", fontSize: 11 }} minTickGap={30} />
                  <YAxis tick={{ fill: "var(--text-faint)", fontSize: 11 }} width={50} />
                  <Tooltip contentStyle={{ background: "var(--panel)", border: "1px solid var(--line)", color: "var(--text-body)" }} />
                  <Line type="monotone" dataKey="roi" stroke="var(--accent)" dot={false} name="ROI %" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted">Không có chuỗi chartItems.</p>
            )}
          </div>
        </section>

        <section className="rounded-2xl border border-line bg-panel p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">
            Drawdown (estimated)
          </h2>
          <p className="mt-1 text-xs text-warn/80">
            Ước tính từ chartItems, chưa điều chỉnh nạp/rút — chỉ tham khảo.
          </p>
          <div className="mt-3 h-56">
            {series.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={series}>
                  <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fill: "var(--text-faint)", fontSize: 11 }} minTickGap={30} />
                  <YAxis tick={{ fill: "var(--text-faint)", fontSize: 11 }} width={50} />
                  <Tooltip contentStyle={{ background: "var(--panel)", border: "1px solid var(--line)", color: "var(--text-body)" }} />
                  <Area type="monotone" dataKey="drawdown" stroke="var(--danger)" fill="#ef4444" fillOpacity={0.25} name="DD %" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted">Không có dữ liệu drawdown.</p>
            )}
          </div>
        </section>

        <section className="rounded-2xl border border-line bg-panel p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">
            Phân bố PnL vị thế
          </h2>
          <p className="mt-1 text-xs text-faint">
            {positions.data ? `${positions.data.items.length} vị thế gần nhất` : "Đang tải..."}
          </p>
          <div className="mt-3 h-56">
            {histogram.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={histogram}>
                  <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fill: "var(--text-faint)", fontSize: 10 }} />
                  <YAxis tick={{ fill: "var(--text-faint)", fontSize: 11 }} width={40} />
                  <Tooltip contentStyle={{ background: "var(--panel)", border: "1px solid var(--line)", color: "var(--text-body)" }} />
                  <Bar dataKey="count" fill="#38bdf8" name="Số vị thế" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted">Chưa có position-history.</p>
            )}
          </div>
        </section>

        <section className="rounded-2xl border border-line bg-panel p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">
            Score breakdown
          </h2>
          <div className="mt-3 space-y-2">
            {Object.entries(score.data?.breakdown.components ?? {}).map(([group, value]) => (
              <div key={group}>
                <div className="flex justify-between text-sm">
                  <span className="capitalize text-body">{group.replaceAll("_", " ")}</span>
                  <span className="text-muted">
                    {fmt(value.score, 1)} · w{value.weight}
                  </span>
                </div>
                <div className="mt-1 h-2 rounded bg-elevated">
                  <div className="h-2 rounded bg-emerald-500" style={{ width: `${Math.min(value.score, 100)}%` }} />
                </div>
              </div>
            ))}
            {!score.data?.breakdown.components ? (
              <p className="text-sm text-muted">Trader chưa có score.</p>
            ) : null}
          </div>
          {score.data?.hard_flags.length ? (
            <p className="mt-3 text-xs text-danger">Hard flags: {score.data.hard_flags.join(", ")}</p>
          ) : null}
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <section className="rounded-2xl border border-line bg-panel p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">Risk flags</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {(risk.data?.events ?? []).map((event) => (
              <span key={event.code} className="rounded-full border border-orange-500/30 bg-orange-500/10 px-2.5 py-1 text-xs text-orange-200" title={JSON.stringify(event.evidence)}>
                {event.code} · {event.label}
              </span>
            ))}
            {risk.data && risk.data.events.length === 0 ? (
              <span className="text-sm text-muted">Không có risk event.</span>
            ) : null}
          </div>
          <Link to={`/risk?trader=${data.trader.id}`} className="mt-4 inline-block text-sm text-accent">
            Mở Risk Monitor →
          </Link>
        </section>

        <section className="rounded-2xl border border-line bg-panel p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">What&apos;s missing</h2>
          <ul className="mt-3 space-y-1.5 text-sm text-muted">
            {[...new Set(missing)].map((flag) => (
              <li key={flag}>• {FLAG_LABELS[flag] ?? flag}</li>
            ))}
          </ul>
        </section>

        <section className="rounded-2xl border border-line bg-panel p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">Nguồn dữ liệu</h2>
          <dl className="mt-3 space-y-2 text-sm">
            {[
              ["Source", data.provenance.source ?? "N/A"],
              ["Window", data.provenance.window],
              ["Published", data.provenance.published ? "Có" : "Không"],
              ["Benchmark", performance.data?.benchmark === null ? "Không có" : "Có"],
              [
                "Thu thập",
                data.provenance.collected_at
                  ? new Date(data.provenance.collected_at).toLocaleString("vi-VN")
                  : "N/A",
              ],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between gap-3">
                <dt className="text-faint">{label}</dt>
                <dd className="text-right">{value}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>

      <section className="rounded-2xl border border-line bg-panel p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">Positions</h2>
          <span className="text-xs text-faint">{positions.data ? `${positions.data.total} vị thế đóng` : ""}</span>
        </div>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-faint">
              <tr>
                <th className="pb-2">Symbol</th>
                <th className="pb-2">Side</th>
                <th className="pb-2 text-right">Lev</th>
                <th className="pb-2 text-right">PnL</th>
                <th className="pb-2 text-right">ROI</th>
                <th className="pb-2">Đóng lúc</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {(positions.data?.items ?? []).slice(0, 10).map((row) => (
                <tr key={row.id}>
                  <td className="py-2 text-body">{row.symbol ?? "—"}</td>
                  <td className="py-2 text-muted">{row.side ?? "—"}</td>
                  <td className="py-2 text-right text-muted">{fmt(row.leverage, 0, "x")}</td>
                  <td className={`py-2 text-right ${(row.closing_pnl ?? 0) < 0 ? "text-danger" : "text-accent"}`}>
                    {money(row.closing_pnl)}
                  </td>
                  <td className={`py-2 text-right ${(row.roi ?? 0) < 0 ? "text-danger" : "text-accent"}`}>
                    {fmt(row.roi === null ? null : row.roi * 100, 1, "%")}
                  </td>
                  <td className="py-2 text-faint">
                    {row.closed_at ? new Date(row.closed_at).toLocaleString("vi-VN") : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!positions.data?.items.length ? (
            <p className="py-3 text-sm text-muted">Chưa có position-history cho trader này.</p>
          ) : null}
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-2xl border border-line bg-panel p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">Trades gần nhất</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {(trades.data?.items ?? []).map((row) => (
              <li key={row.hash} className="flex items-center justify-between gap-3">
                <span className="text-body">
                  {row.symbol} · {row.side}
                </span>
                <span className="text-faint">
                  {money(row.notional)} · fee {fmt(row.fee, 4)}
                </span>
              </li>
            ))}
            {!trades.data?.items.length ? (
              <li className="text-muted">Trader này không nằm trong nhóm full trade-history.</li>
            ) : null}
          </ul>
        </section>

        <section className="rounded-2xl border border-line bg-panel p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">Transfers</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {(transfers.data?.items ?? []).map((row) => (
              <li key={`${row.time}-${row.amount}-${row.type}`} className="flex items-center justify-between gap-3">
                <span className="text-body">
                  {row.type} · {row.coin}
                </span>
                <span className={row.type?.includes("WITHDRAW") ? "text-danger" : "text-accent"}>
                  {money(row.amount)}
                </span>
              </li>
            ))}
            {!transfers.data?.items.length ? (
              <li className="text-muted">Không có transfer.</li>
            ) : null}
          </ul>
        </section>
      </div>

      <p className="border-t border-line pt-4 text-xs text-faint">{data.disclaimer}</p>
    </div>
  );
}
