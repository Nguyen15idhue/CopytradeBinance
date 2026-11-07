import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getRanking, runRanking } from "../lib/api";
import { getStoredUser } from "../lib/auth";
import { BOARD_LABELS, RISK_LEVEL_LABELS, TIER_LABELS, label } from "../i18n/vi";

const BOARDS = [
  ["overall", BOARD_LABELS.overall, "Điểm tổng hợp sau bộ lọc cứng"],
  ["low_risk", BOARD_LABELS.low_risk, "Số ngày ≥ 90, MDD ≤ 20, đòn bẩy ≤ 5, độ tin cậy ≥ 0,8"],
  ["consistency", BOARD_LABELS.consistency, "Xếp theo điểm ổn định, không theo ROI"],
] as const;

function num(value: number | null, digits = 2, suffix = ""): string {
  return value === null ? "N/A" : `${value.toFixed(digits)}${suffix}`;
}

export default function RankingPage() {
  const isAdmin = getStoredUser()?.role === "admin";
  const queryClient = useQueryClient();
  const [board, setBoard] = useState<string>("overall");

  const ranking = useQuery({
    queryKey: ["ranking", board],
    queryFn: () => getRanking(board),
  });
  const run = useMutation({
    mutationFn: runRanking,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ranking"] }),
  });

  const active = BOARDS.find(([key]) => key === board)!;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Bảng xếp hạng</h1>
          <p className="mt-2 text-muted">
            Ba bảng xếp hạng có kiểm soát. Không có bảng “Lợi nhuận cao” để tránh chạy theo ROI.
          </p>
        </div>
        {isAdmin ? (
          <button
            type="button"
            onClick={() => run.mutate()}
            disabled={run.isPending}
            className="rounded-lg bg-emerald-500 px-3 py-2 text-sm font-medium text-slate-950 disabled:opacity-50"
          >
            {run.isPending ? "Đang tạo bản chụp..." : "Chạy xếp hạng"}
          </button>
        ) : null}
      </div>

      <div className="flex flex-wrap gap-2">
        {BOARDS.map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setBoard(key)}
            className={`rounded-lg border px-3 py-1.5 text-sm ${
              board === key ? "border-accent/40 bg-accent/10 text-accent" : "border-line text-body"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <p className="text-sm text-muted">{active[2]}</p>

      {ranking.data ? (
        <p className="text-xs text-faint">
          Bản chụp:{" "}
          {ranking.data.collected_at
            ? new Date(ranking.data.collected_at).toLocaleString("vi-VN")
            : "chưa có"}{" "}
          · phiên bản cấu hình v{ranking.data.config_version ?? "—"} · {ranking.data.total} trader
        </p>
      ) : null}

      {ranking.isLoading ? (
        <div className="h-64 animate-pulse rounded-2xl bg-elevated" />
      ) : ranking.isError ? (
        <div className="rounded-2xl border border-danger/30 bg-danger/5 p-5 text-danger">
          Không tải được ranking.
        </div>
      ) : !ranking.data?.items.length ? (
        <div className="rounded-2xl border border-line bg-panel p-8 text-center">
          <p className="text-body">Chưa có bản chụp cho bảng này.</p>
          <p className="mt-2 text-sm text-muted">
            {isAdmin ? "Bấm “Chạy xếp hạng” để tạo bản chụp." : "Cần admin chạy xếp hạng."}
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-line bg-panel">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="border-b border-line text-xs uppercase tracking-wide text-faint">
              <tr>
                <th className="px-3 py-3">#</th>
                <th className="px-3 py-3">Trader</th>
                <th className="px-3 py-3">Nhóm</th>
                <th className="px-3 py-3 text-right">Điểm</th>
                <th className="px-3 py-3 text-right">Tin cậy</th>
                <th className="px-3 py-3 text-right">ROI 90D</th>
                <th className="px-3 py-3 text-right">MDD</th>
                <th className="px-3 py-3 text-right">Sharpe</th>
                <th className="px-3 py-3">Rủi ro</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {ranking.data.items.map((item) => (
                <tr key={item.id} className="hover:bg-elevated/60">
                  <td className="px-3 py-2 text-faint">{item.rank}</td>
                  <td className="px-3 py-2">
                    <Link to={`/traders/${item.id}`} className="text-strong hover:text-accent">
                      {item.nickname ?? item.id}
                    </Link>
                  </td>
                  <td className="px-3 py-2 text-muted">
                    {label(TIER_LABELS, item.tier)}
                  </td>
                  <td className="px-3 py-2 text-right text-strong">{num(item.score, 1)}</td>
                  <td className="px-3 py-2 text-right text-muted">
                    {item.confidence === null ? "N/A" : `${Math.round(item.confidence * 100)}%`}
                  </td>
                  <td className="px-3 py-2 text-right text-body">{num(item.roi_90d, 2, "%")}</td>
                  <td className="px-3 py-2 text-right text-body">{num(item.mdd_90d, 2, "%")}</td>
                  <td className="px-3 py-2 text-right text-body">{num(item.sharpe)}</td>
                  <td className="px-3 py-2 text-muted">{label(RISK_LEVEL_LABELS, item.risk_level)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
