import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { analyzeTrader, getAIReports } from "../lib/api";
import { getStoredUser } from "../lib/auth";
import { MODEL_ROLE_LABELS, label } from "../i18n/vi";
import type { AIReportItem } from "../types/trader";

const ROLE_STYLE: Record<string, string> = {
  primary: "border-accent/40 bg-accent/10 text-accent",
  fallback: "border-warn/40 bg-warn/10 text-warn",
  template: "border-line bg-elevated text-muted",
};

function ReportCard({ report }: { report: AIReportItem }) {
  return (
    <article className="rounded-xl border border-line bg-app/50 p-4">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className={`rounded-full border px-2 py-0.5 uppercase ${ROLE_STYLE[report.model_role] ?? ROLE_STYLE.template}`}>
          {label(MODEL_ROLE_LABELS, report.model_role)}
        </span>
        <span className="text-faint">{report.model_used}</span>
        <span className="text-faint">prompt {report.prompt_version}</span>
        <span className="ml-auto text-faint">
          {report.latency_ms !== null ? `${report.latency_ms}ms · ` : ""}
          {report.cost_usd.toFixed(4)} USD
        </span>
      </div>
      <p className="mt-3 text-xs uppercase tracking-wide text-faint">Đánh giá tổng quan</p>
      <p className="mt-1 text-sm text-body">{report.summary}</p>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-faint">Điểm mạnh có số liệu</p>
          <ul className="mt-1 space-y-1 text-sm text-body">
            {report.strengths.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-faint">Điểm cần lưu ý</p>
          <ul className="mt-1 space-y-1 text-sm text-body">
            {report.weaknesses.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
      </div>
      {report.risk_flags.length ? (
        <div className="mt-3">
          <p className="text-xs uppercase tracking-wide text-faint">Rủi ro đã phát hiện</p>
          <ul className="mt-1 space-y-1 text-sm text-warn">
            {report.risk_flags.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {report.missing_data.length ? (
        <p className="mt-2 text-xs text-warn">
          Dữ liệu còn thiếu: {report.missing_data.join(", ")}
        </p>
      ) : null}
      <div className="mt-2 flex flex-wrap gap-1">
        <span className="text-[10px] uppercase tracking-wide text-faint">Bằng chứng:</span>
        {report.evidence_ids.map((item) => (
          <span key={item} className="rounded border border-line px-1.5 py-0.5 text-[10px] text-muted">
            {item}
          </span>
        ))}
      </div>
      <p className="mt-2 text-[11px] text-faint">
        {new Date(report.created_at).toLocaleString("vi-VN")}
      </p>
    </article>
  );
}

export default function AIReportPanel({ traderId }: { traderId: string }) {
  const user = getStoredUser();
  const isAdmin = user?.role === "admin";
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const reports = useQuery({
    queryKey: ["ai-reports", traderId],
    queryFn: () => getAIReports(traderId),
  });

  const analyze = useMutation({
    mutationFn: () => analyzeTrader(traderId),
    onSuccess: async () => {
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["ai-reports", traderId] });
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : "Không tạo được báo cáo");
    },
  });

  return (
    <section className="rounded-2xl border border-line bg-panel p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">Nhận định AI</h2>
          <p className="mt-1 text-xs text-faint">
            Phân tích dựa trên số liệu, không sửa điểm/xếp hạng. Làm mới sau 24 giờ/trader.
          </p>
        </div>
        {isAdmin ? (
          <button
            type="button"
            onClick={() => analyze.mutate()}
            disabled={analyze.isPending}
            className="rounded-lg bg-emerald-500 px-3 py-1.5 text-sm font-medium text-slate-950 disabled:opacity-50"
          >
            {analyze.isPending ? "Đang phân tích..." : "Phân tích"}
          </button>
        ) : null}
      </div>

      {error ? (
        <p className="mt-3 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </p>
      ) : null}

      <div className="mt-4 space-y-3">
        {reports.isLoading ? (
          <div className="h-24 animate-pulse rounded-xl bg-elevated" />
        ) : reports.data?.items.length ? (
          reports.data.items.slice(0, 3).map((report) => (
            <ReportCard key={report.id} report={report} />
          ))
        ) : (
          <p className="text-sm text-muted">
            Chưa có nhận định AI cho trader này.
            {isAdmin ? " Bấm Phân tích để tạo nhận định đầu tiên." : " Cần admin tạo nhận định."}
          </p>
        )}
      </div>
    </section>
  );
}
