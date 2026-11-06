import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getTrader } from "../lib/api";
import type { Metric } from "../types/trader";

const REASON_LABELS: Record<string, string> = {
  runtime_lt_30: "Runtime < 30 ngày",
  no_trade_7d: "Không giao dịch 7 ngày",
  roi_le_0: "ROI ≤ 0",
  pnl_le_0: "PnL ≤ 0",
  winrate_lt_40: "WinRate < 40%",
  mdd_gt_40: "MDD > 40%",
  aum_lt_5000: "AUM < 5.000",
  aum_lt_1000: "AUM < 1.000",
  aum_lt_10000: "AUM < 10.000",
  no_slots: "Hết slot copy",
};

const FLAG_LABELS: Record<string, string> = {
  missing_sharpe: "Thiếu Sharpe",
  missing_mdd: "Thiếu MDD",
  no_copiers: "Không có copier",
  low_sample: "Mẫu giao dịch nhỏ",
  excluded: "Bị loại khỏi shortlist",
  derived_unavailable: "Chỉ số derived chưa có",
};

const TIER_STYLES: Record<string, string> = {
  high: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
  qualified: "border-teal-500/40 bg-teal-500/10 text-teal-300",
  watch: "border-sky-500/40 bg-sky-500/10 text-sky-300",
  excluded: "border-amber-500/40 bg-amber-500/10 text-amber-300",
  unknown: "border-slate-700 bg-slate-800 text-slate-300",
};

function formatValue(metric: Metric): string {
  if (metric.value === null) return "N/A";
  const value = metric.value;
  if (metric.unit === "%") return `${value.toFixed(2)}%`;
  if (metric.unit === "USDT") {
    return value.toLocaleString("vi-VN", { maximumFractionDigits: 0 });
  }
  if (metric.unit === "x") return `${value.toFixed(2)}x`;
  if (metric.unit === "người") return `${value}`;
  return value.toFixed(2);
}

function MetricCard({ metric }: { metric: Metric }) {
  const isZeroCopy = metric.key === "copy_aum" && metric.value === 0;
  const display = isZeroCopy ? "0" : formatValue(metric);
  return (
    <div
      className="rounded-xl border border-slate-800 bg-slate-900/60 p-4"
      title={`${metric.label} — nguồn: ${metric.source}${
        metric.window ? ` · cửa sổ: ${metric.window}` : ""
      }${metric.note ? ` · ${metric.note}` : ""}`}
    >
      <p className="text-xs uppercase tracking-wide text-slate-500">{metric.label}</p>
      <p className="mt-2 text-2xl font-semibold">
        {display}
        {metric.unit && metric.value !== null ? (
          <span className="ml-1 text-sm font-normal text-slate-400">{metric.unit}</span>
        ) : null}
      </p>
      <p className="mt-1 text-xs text-slate-500">
        {isZeroCopy ? "Không có copier" : metric.note ?? metric.source}
        {metric.window ? ` · ${metric.window}` : ""}
      </p>
    </div>
  );
}

export default function TraderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const query = useQuery({
    queryKey: ["trader", id],
    queryFn: () => getTrader(id!),
    enabled: Boolean(id),
    retry: 0,
  });

  if (query.isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-28 animate-pulse rounded-2xl bg-slate-900" />
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          {Array.from({ length: 10 }).map((_, index) => (
            <div key={index} className="h-24 animate-pulse rounded-xl bg-slate-900" />
          ))}
        </div>
      </div>
    );
  }

  if (query.isError || !query.data) {
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/5 p-6">
        <h1 className="text-lg font-semibold text-red-300">Không tải được trader</h1>
        <p className="mt-2 text-sm text-slate-400">
          {query.error instanceof Error ? query.error.message : "Lỗi không xác định"}
        </p>
        <Link to="/" className="mt-4 inline-block text-sm text-emerald-400">
          ← Quay lại danh sách demo
        </Link>
      </div>
    );
  }

  const data = query.data;
  const tierClass = TIER_STYLES[data.tier] ?? TIER_STYLES.unknown;
  const missing = [
    data.flags.includes("missing_sharpe") ? "Sharpe: thiếu dữ liệu" : null,
    data.flags.includes("missing_mdd") ? "MDD: thiếu dữ liệu" : null,
    data.flags.includes("no_copiers") ? "Copy AUM = 0: không có copier" : null,
    "Profit Factor / Avg Holding: cần position-history ở Phase 3",
    "Open positions: Binance không cung cấp",
    "Per-copier: Binance không cung cấp",
    "Funding: không có trong trade-history",
  ].filter(Boolean) as string[];

  return (
    <div className="space-y-6">
      <Link to="/" className="text-sm text-slate-400 hover:text-slate-200">
        ← Danh sách demo
      </Link>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold">
                {data.trader.nickname ?? data.trader.id}
              </h1>
              <span className={`rounded-full border px-2.5 py-0.5 text-xs uppercase ${tierClass}`}>
                {data.tier}
              </span>
              <span className="rounded-full border border-slate-700 px-2.5 py-0.5 text-xs text-slate-400">
                {data.trader.portfolio_type ?? "N/A"}
              </span>
              <span className="rounded-full border border-slate-700 px-2.5 py-0.5 text-xs text-slate-400">
                {data.trader.status ?? "N/A"}
              </span>
            </div>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              {data.trader.description ?? "Không có mô tả"}
            </p>
            <p className="mt-2 font-mono text-xs text-slate-500">{data.trader.id}</p>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-slate-500">Độ tin cậy</p>
            <p className="text-2xl font-semibold">{Math.round(data.confidence * 100)}%</p>
            <p className="text-xs text-slate-500">
              {data.provenance.source ?? "N/A"} · {data.provenance.window}
            </p>
          </div>
        </div>

        {data.tier === "excluded" ? (
          <div className="mt-5 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
            <p className="text-sm font-medium text-amber-200">Trader bị loại khỏi shortlist</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {data.reasons.map((reason) => (
                <span
                  key={reason}
                  className="rounded-full border border-amber-500/30 px-2.5 py-1 text-xs text-amber-200"
                >
                  {REASON_LABELS[reason] ?? reason}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        {data.trader.runtime_days !== null && data.trader.runtime_days < 30 ? (
          <p className="mt-4 text-sm text-amber-300">
            Portfolio mới: {data.trader.runtime_days.toFixed(2)} ngày — chưa đủ lịch sử.
          </p>
        ) : null}
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-500">
          10 chỉ số cốt lõi
        </h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          {data.metrics.map((metric) => (
            <MetricCard key={metric.key} metric={metric} />
          ))}
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-3">
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-slate-500">
            Risk flags
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {data.flags.map((flag) => (
              <span
                key={flag}
                className="rounded-full border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-slate-300"
              >
                {FLAG_LABELS[flag] ?? flag}
              </span>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-slate-500">
            What&apos;s missing
          </h2>
          <ul className="mt-3 space-y-1.5 text-sm text-slate-400">
            {missing.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-slate-500">
            Nguồn dữ liệu
          </h2>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Source</dt>
              <dd>{data.provenance.source ?? "N/A"}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Window</dt>
              <dd>{data.provenance.window}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Published</dt>
              <dd>{data.provenance.published ? "Có" : "Không"}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Thu thập</dt>
              <dd className="text-right text-xs">
                {data.provenance.collected_at
                  ? new Date(data.provenance.collected_at).toLocaleString("vi-VN")
                  : "N/A"}
              </dd>
            </div>
          </dl>
        </section>
      </div>

      <p className="border-t border-slate-800 pt-4 text-xs text-slate-500">{data.disclaimer}</p>
    </div>
  );
}
