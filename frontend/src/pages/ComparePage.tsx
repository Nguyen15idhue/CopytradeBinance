import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getCompare, getScreener } from "../lib/api";

const COLORS = ["var(--accent)", "var(--info)", "var(--warn)", "var(--danger)"];

const ROWS: Array<[string, (item: Record<string, unknown>) => string]> = [
  ["Tier", (item) => String(item.tier ?? "—")],
  ["Score", (item) => number(item.score)],
  ["Band", (item) => String(item.band ?? "—")],
  ["Confidence", (item) => (item.confidence === null ? "N/A" : `${Math.round(Number(item.confidence) * 100)}%`)],
  ["Risk", (item) => String(item.risk_level ?? "unknown")],
  ["ROI 90D", (item) => percent(item.roi_90d)],
  ["MDD 90D", (item) => percent(item.mdd_90d)],
  ["Sharpe", (item) => number(item.sharpe)],
  ["WinRate", (item) => percent(item.win_rate_order)],
  ["Max leverage", (item) => (item.max_leverage === null ? "N/A" : `${number(item.max_leverage)}x`)],
  ["Profit factor", (item) => number(item.profit_factor)],
  ["Runtime", (item) => (item.runtime_days === null ? "N/A" : `${number(item.runtime_days, 0)} ngày`)],
  ["Copier PnL", (item) => number(item.copier_pnl_90d)],
  ["Copy AUM", (item) => money(item.copy_aum)],
  ["Top symbol", (item) => String(item.top_symbol ?? "—")],
];

function number(value: unknown, digits = 2): string {
  const parsed = Number(value);
  if (value === null || value === undefined || Number.isNaN(parsed)) return "N/A";
  return parsed.toFixed(digits);
}

function percent(value: unknown): string {
  const parsed = Number(value);
  if (value === null || value === undefined || Number.isNaN(parsed)) return "N/A";
  return `${parsed.toFixed(2)}%`;
}

function money(value: unknown): string {
  const parsed = Number(value);
  if (value === null || value === undefined || Number.isNaN(parsed)) return "N/A";
  return parsed.toLocaleString("vi-VN", { maximumFractionDigits: 0 });
}

export default function ComparePage() {
  const [params, setParams] = useSearchParams();
  const initial = (params.get("ids") ?? "").split(",").filter(Boolean).slice(0, 4);
  const [ids, setIds] = useState<string[]>(initial);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const next = new URLSearchParams(params);
    if (ids.length) next.set("ids", ids.join(","));
    else next.delete("ids");
    setParams(next, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ids]);

  const searchResults = useQuery({
    queryKey: ["compare-search", search],
    queryFn: () => getScreener({ q: search, page_size: 6, sort_by: "score", sort_dir: "desc" }),
    enabled: search.trim().length > 0,
  });

  const compare = useQuery({
    queryKey: ["compare", ids],
    queryFn: () => getCompare(ids),
    enabled: ids.length >= 2,
    retry: 0,
  });

  const chart = useMemo(() => {
    if (!compare.data) return [];
    type Point = Record<string, number | string>;
    const byDate = new Map<number, Point>();
    for (const item of compare.data.items) {
      for (const point of compare.data.series[item.id] ?? []) {
        const row =
          byDate.get(point.date_time) ?? {
            date: new Date(point.date_time).toLocaleDateString("vi-VN"),
          };
        row[item.id] = point.value;
        byDate.set(point.date_time, row);
      }
    }
    return [...byDate.entries()].sort((a, b) => a[0] - b[0]).map(([, row]) => row);
  }, [compare.data]);

  function toggle(id: string) {
    setIds((current) => {
      if (current.includes(id)) return current.filter((value) => value !== id);
      if (current.length >= 4) return current;
      return [...current, id];
    });
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Compare</h1>
        <p className="mt-2 text-muted">So sánh 2–4 trader. Tối đa 4.</p>
      </div>

      <section className="rounded-2xl border border-line bg-panel p-4">
        <div className="flex flex-wrap items-center gap-2">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Tìm trader để thêm..."
            className="w-64 rounded-lg border border-line bg-app px-3 py-2 text-strong"
          />
          {searchResults.data?.items.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => toggle(item.id)}
              disabled={ids.length >= 4 && !ids.includes(item.id)}
              className={`rounded-full border px-3 py-1 text-sm ${
                ids.includes(item.id)
                  ? "border-emerald-500/50 bg-emerald-500/10 text-accent"
                  : "border-line text-body"
              } disabled:opacity-40`}
            >
              {item.nickname ?? item.id}
            </button>
          ))}
          <span className="ml-auto text-xs text-faint">{ids.length}/4 đã chọn</span>
        </div>
        {ids.length ? (
          <div className="mt-3 flex flex-wrap gap-2 border-t border-line pt-3">
            {ids.map((id, index) => (
              <span
                key={id}
                className="flex items-center gap-2 rounded-full border border-line px-3 py-1 text-xs text-body"
              >
                <span className="h-2 w-2 rounded-full" style={{ background: COLORS[index % COLORS.length] }} />
                {id}
                <button type="button" onClick={() => toggle(id)} className="text-faint hover:text-danger">
                  ×
                </button>
              </span>
            ))}
          </div>
        ) : null}
      </section>

      {ids.length < 2 ? (
        <div className="rounded-2xl border border-line bg-panel p-8 text-center text-muted">
          Chọn ít nhất 2 trader để so sánh.
        </div>
      ) : compare.isLoading ? (
        <div className="h-64 animate-pulse rounded-2xl bg-panel" />
      ) : compare.isError || !compare.data ? (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/5 p-5 text-danger">
          Không tải được compare: {compare.error instanceof Error ? compare.error.message : "lỗi"}
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-2xl border border-line bg-panel">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b border-line text-xs uppercase tracking-wide text-faint">
                <tr>
                  <th className="px-3 py-3">Chỉ số</th>
                  {compare.data.items.map((item, index) => (
                    <th key={item.id} className="px-3 py-3">
                      <Link to={`/traders/${item.id}`} className="hover:text-accent">
                        <span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: COLORS[index % COLORS.length] }} />
                        {item.nickname ?? item.id.slice(0, 8)}
                      </Link>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {ROWS.map(([label, render]) => (
                  <tr key={label}>
                    <td className="px-3 py-2 text-faint">{label}</td>
                    {compare.data!.items.map((item) => (
                      <td key={item.id} className="px-3 py-2 text-strong">
                        {render(item as unknown as Record<string, unknown>)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <section className="rounded-2xl border border-line bg-panel p-5">
            <h2 className="text-sm font-medium uppercase tracking-wide text-faint">ROI lũy kế</h2>
            <p className="mt-1 text-xs text-faint">chartItems từ Binance, bị pha loãng bởi nạp/rút.</p>
            <div className="mt-3 h-64">
              {chart.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chart}>
                    <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fill: "var(--text-faint)", fontSize: 11 }} minTickGap={40} />
                    <YAxis tick={{ fill: "var(--text-faint)", fontSize: 11 }} width={50} />
                    <Tooltip contentStyle={{ background: "var(--panel)", border: "1px solid var(--line)", color: "var(--text-body)" }} />
                    {compare.data.items.map((item, index) => (
                      <Line
                        key={item.id}
                        type="monotone"
                        dataKey={item.id}
                        stroke={COLORS[index % COLORS.length]}
                        dot={false}
                        name={item.nickname ?? item.id.slice(0, 8)}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-sm text-muted">Không có chuỗi chartItems để vẽ.</p>
              )}
            </div>
          </section>

          <section className="rounded-2xl border border-line bg-panel p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-medium uppercase tracking-wide text-faint">Correlation</h2>
              <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-xs text-warn">
                estimated
              </span>
            </div>
            <p className="mt-1 text-xs text-faint">{compare.data.correlation.disclaimer}</p>
            <div className="mt-3 overflow-x-auto">
              <table className="text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-faint">
                  <tr>
                    <th className="px-3 py-2"></th>
                    {compare.data.correlation.ids.map((id) => (
                      <th key={id} className="px-3 py-2 font-mono text-[10px]">
                        {id.slice(0, 8)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {compare.data.correlation.matrix.map((row, rowIndex) => (
                    <tr key={compare.data!.correlation.ids[rowIndex]}>
                      <td className="px-3 py-2 font-mono text-[10px] text-faint">
                        {compare.data!.correlation.ids[rowIndex].slice(0, 8)}
                      </td>
                      {row.map((value, columnIndex) => (
                        <td
                          key={`${rowIndex}-${columnIndex}`}
                          className={`px-3 py-2 ${
                            value === null
                              ? "text-faint"
                              : value > 0.7
                                ? "text-danger"
                                : value > 0.3
                                  ? "text-warn"
                                  : "text-accent"
                          }`}
                        >
                          {value === null ? "N/A" : value.toFixed(2)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-2 text-xs text-faint">
              Mẫu chung: {compare.data.correlation.sample_days} ngày (cần ≥ 30 để tính).
            </p>
          </section>
        </>
      )}
    </div>
  );
}
