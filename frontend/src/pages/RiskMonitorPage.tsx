import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { getRiskEvents, getRiskSummary } from "../lib/api";

const SEVERITY_STYLES: Record<string, string> = {
  critical: "border-red-500/40 bg-red-500/10 text-red-300",
  high: "border-orange-500/40 bg-orange-500/10 text-orange-300",
  medium: "border-amber-500/40 bg-amber-500/10 text-amber-300",
  low_sample: "border-sky-500/40 bg-sky-500/10 text-sky-300",
  confidence_penalty: "border-slate-600 bg-slate-800 text-slate-300",
  insufficient: "border-slate-600 bg-slate-800 text-slate-300",
};

export default function RiskMonitorPage() {
  const [params] = useSearchParams();
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("open");
  const [trader, setTrader] = useState(params.get("trader") ?? "");
  const [page, setPage] = useState(1);
  const [expanded, setExpanded] = useState<string | null>(null);

  const summary = useQuery({ queryKey: ["risk-summary"], queryFn: getRiskSummary });
  const events = useQuery({
    queryKey: ["risk-events", severity, status, trader, page],
    queryFn: () =>
      getRiskEvents({
        severity: severity || undefined,
        status: status || undefined,
        trader: trader || undefined,
        page,
        page_size: 50,
      }),
  });

  const totalPages = events.data ? Math.max(1, Math.ceil(events.data.total / events.data.page_size)) : 1;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Risk Monitor</h1>
        <p className="mt-2 text-slate-400">
          Risk event R01–R11 kèm evidence. Không hiển thị open positions vì Binance không cung cấp.
        </p>
      </div>

      {summary.data ? (
        <div className="flex flex-wrap gap-2 text-sm">
          <span className="rounded-full border border-slate-700 px-3 py-1 text-slate-300">
            Tổng {summary.data.total}
          </span>
          {Object.entries(summary.data.by_severity).map(([key, value]) => (
            <span key={key} className={`rounded-full border px-3 py-1 ${SEVERITY_STYLES[key] ?? "border-slate-700 text-slate-300"}`}>
              {key}: {value}
            </span>
          ))}
        </div>
      ) : null}

      <section className="flex flex-wrap items-end gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <label className="text-sm text-slate-300">
          Severity
          <select
            value={severity}
            onChange={(event) => { setSeverity(event.target.value); setPage(1); }}
            className="mt-1 block rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          >
            <option value="">Tất cả</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low_sample">Low sample</option>
            <option value="confidence_penalty">Confidence penalty</option>
          </select>
        </label>
        <label className="text-sm text-slate-300">
          Status
          <select
            value={status}
            onChange={(event) => { setStatus(event.target.value); setPage(1); }}
            className="mt-1 block rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          >
            <option value="">Tất cả</option>
            <option value="open">Open</option>
          </select>
        </label>
        <label className="text-sm text-slate-300">
          Trader ID
          <input
            value={trader}
            onChange={(event) => { setTrader(event.target.value); setPage(1); }}
            placeholder="portfolio id"
            className="mt-1 block w-64 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          />
        </label>
        <button
          type="button"
          onClick={() => { setSeverity(""); setStatus("open"); setTrader(""); setPage(1); }}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300"
        >
          Reset
        </button>
        <span className="ml-auto text-sm text-slate-400">
          {events.data ? `${events.data.total} event` : "Đang tải..."}
        </span>
      </section>

      {events.isLoading ? (
        <div className="h-64 animate-pulse rounded-2xl bg-slate-900" />
      ) : events.isError ? (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/5 p-5 text-red-300">
          Không tải được risk events.
        </div>
      ) : !events.data?.items.length ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-center text-slate-400">
          Không có risk event khớp bộ lọc.
        </div>
      ) : (
        <div className="space-y-2">
          {events.data.items.map((event) => {
            const key = `${event.trader_id}-${event.code}`;
            const isOpen = expanded === key;
            return (
              <article key={key} className="rounded-xl border border-slate-800 bg-slate-900/60">
                <button
                  type="button"
                  onClick={() => setExpanded(isOpen ? null : key)}
                  className="flex w-full flex-wrap items-center gap-3 px-4 py-3 text-left"
                >
                  <span className={`rounded-full border px-2 py-0.5 text-xs ${SEVERITY_STYLES[event.severity] ?? "border-slate-700 text-slate-300"}`}>
                    {event.code} · {event.severity}
                  </span>
                  <span className="text-sm text-slate-200">{event.label}</span>
                  <Link
                    to={`/traders/${event.trader_id}`}
                    onClick={(clickEvent) => clickEvent.stopPropagation()}
                    className="text-xs text-emerald-400 hover:underline"
                  >
                    {event.nickname ?? event.trader_id}
                  </Link>
                  <span className="ml-auto text-xs text-slate-500">{isOpen ? "▲" : "▼"}</span>
                </button>
                {isOpen ? (
                  <div className="border-t border-slate-800 px-4 py-3">
                    <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Evidence</p>
                    <pre className="overflow-x-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-300">
{JSON.stringify(event.evidence, null, 2)}
                    </pre>
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      )}

      {events.data && events.data.total > events.data.page_size ? (
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
    </div>
  );
}
