import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { getRiskEvents, getRiskSummary } from "../lib/api";
import { RISK_EVENT_LABELS, SEVERITY_LABELS, label } from "../i18n/vi";

const SEVERITY_STYLES: Record<string, string> = {
  critical: "border-red-500/40 bg-red-500/10 text-danger",
  high: "border-orange-500/40 bg-orange-500/10 text-warn",
  medium: "border-amber-500/40 bg-amber-500/10 text-warn",
  low_sample: "border-sky-500/40 bg-sky-500/10 text-info",
  confidence_penalty: "border-line bg-elevated text-body",
  insufficient: "border-line bg-elevated text-body",
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
        <h1 className="text-3xl font-semibold tracking-tight">Cảnh báo rủi ro</h1>
        <p className="mt-2 text-muted">
          Risk event R01–R11 kèm bằng chứng. Không hiển thị vị thế đang mở vì Binance không cung cấp.
        </p>
      </div>

      {summary.data ? (
        <div className="flex flex-wrap gap-2 text-sm">
          <span className="rounded-full border border-line px-3 py-1 text-body">
            Tổng {summary.data.total}
          </span>
          {Object.entries(summary.data.by_severity).map(([key, value]) => (
            <span key={key} className={`rounded-full border px-3 py-1 ${SEVERITY_STYLES[key] ?? "border-line text-body"}`}>
              {label(SEVERITY_LABELS, key)}: {value}
            </span>
          ))}
        </div>
      ) : null}

      <section className="flex flex-wrap items-end gap-3 rounded-2xl border border-line bg-panel p-4">
        <label className="text-sm text-body">
          Mức độ
          <select
            value={severity}
            onChange={(event) => { setSeverity(event.target.value); setPage(1); }}
            className="mt-1 block rounded-lg border border-line bg-app px-3 py-2 text-strong"
          >
            <option value="">Tất cả</option>
            <option value="critical">{SEVERITY_LABELS.critical}</option>
            <option value="high">{SEVERITY_LABELS.high}</option>
            <option value="medium">{SEVERITY_LABELS.medium}</option>
            <option value="low_sample">{SEVERITY_LABELS.low_sample}</option>
            <option value="confidence_penalty">{SEVERITY_LABELS.confidence_penalty}</option>
          </select>
        </label>
        <label className="text-sm text-body">
          Trạng thái
          <select
            value={status}
            onChange={(event) => { setStatus(event.target.value); setPage(1); }}
            className="mt-1 block rounded-lg border border-line bg-app px-3 py-2 text-strong"
          >
            <option value="">Tất cả</option>
            <option value="open">Đang mở</option>
          </select>
        </label>
        <label className="text-sm text-body">
          ID trader
          <input
            value={trader}
            onChange={(event) => { setTrader(event.target.value); setPage(1); }}
            placeholder="ID portfolio"
            className="mt-1 block w-64 rounded-lg border border-line bg-app px-3 py-2 text-strong"
          />
        </label>
        <button
          type="button"
          onClick={() => { setSeverity(""); setStatus("open"); setTrader(""); setPage(1); }}
          className="rounded-lg border border-line px-3 py-2 text-sm text-body"
        >
          Đặt lại
        </button>
        <span className="ml-auto text-sm text-muted">
          {events.data ? `${events.data.total} cảnh báo` : "Đang tải..."}
        </span>
      </section>

      {events.isLoading ? (
        <div className="h-64 animate-pulse rounded-2xl bg-panel" />
      ) : events.isError ? (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/5 p-5 text-danger">
          Không tải được cảnh báo rủi ro.
        </div>
      ) : !events.data?.items.length ? (
        <div className="rounded-2xl border border-line bg-panel p-8 text-center text-muted">
          Không có cảnh báo rủi ro khớp bộ lọc.
        </div>
      ) : (
        <div className="space-y-2">
          {events.data.items.map((event) => {
            const key = `${event.trader_id}-${event.code}`;
            const isOpen = expanded === key;
            return (
              <article key={key} className="rounded-xl border border-line bg-panel">
                <button
                  type="button"
                  onClick={() => setExpanded(isOpen ? null : key)}
                  className="flex w-full flex-wrap items-center gap-3 px-4 py-3 text-left"
                >
                  <span className={`rounded-full border px-2 py-0.5 text-xs ${SEVERITY_STYLES[event.severity] ?? "border-line text-body"}`}>
                    {event.code} · {label(SEVERITY_LABELS, event.severity)}
                  </span>
                  <span className="text-sm text-strong">
                    {label(RISK_EVENT_LABELS, event.code, event.label)}
                  </span>
                  <Link
                    to={`/traders/${event.trader_id}`}
                    onClick={(clickEvent) => clickEvent.stopPropagation()}
                    className="text-xs text-accent hover:underline"
                  >
                    {event.nickname ?? event.trader_id}
                  </Link>
                  <span className="ml-auto text-xs text-faint">{isOpen ? "▲" : "▼"}</span>
                </button>
                {isOpen ? (
                  <div className="border-t border-line px-4 py-3">
                    <p className="mb-2 text-xs uppercase tracking-wide text-faint">Bằng chứng</p>
                    <pre className="overflow-x-auto rounded-lg bg-app p-3 text-xs text-body">
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
    </div>
  );
}
