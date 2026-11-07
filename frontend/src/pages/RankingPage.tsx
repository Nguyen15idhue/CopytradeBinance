import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getRanking, runRanking } from "../lib/api";
import { getStoredUser } from "../lib/auth";

const BOARDS = [
  ["overall", "Overall", "Điểm tổng hợp sau hard filter"],
  ["low_risk", "Low Risk", "Runtime ≥ 90, MDD ≤ 20, leverage ≤ 5, confidence ≥ 0.8"],
  ["consistency", "Consistency", "Xếp theo điểm ổn định, không theo ROI"],
] as const;

const TIER_LABELS: Record<string, string> = {
  high_upper: "High",
  qualified_upper: "Qualified",
  watch: "Watch",
  excluded: "Excluded",
};

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
          <h1 className="text-3xl font-semibold tracking-tight">Ranking</h1>
          <p className="mt-2 text-muted">
            Ba bảng xếp hạng có kiểm soát. Không có bảng “High Return” để tránh chase ROI.
          </p>
        </div>
        {isAdmin ? (
          <button
            type="button"
            onClick={() => run.mutate()}
            disabled={run.isPending}
            className="rounded-lg bg-emerald-500 px-3 py-2 text-sm font-medium text-slate-950 disabled:opacity-50"
          >
            {run.isPending ? "Đang chụp snapshot..." : "Chạy ranking"}
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
          Snapshot:{" "}
          {ranking.data.collected_at
            ? new Date(ranking.data.collected_at).toLocaleString("vi-VN")
            : "chưa có"}{" "}
          · config v{ranking.data.config_version ?? "—"} · {ranking.data.total} trader
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
          <p className="text-body">Chưa có snapshot cho bảng này.</p>
          <p className="mt-2 text-sm text-muted">
            {isAdmin ? "Bấm “Chạy ranking” để tạo snapshot." : "Cần admin chạy ranking."}
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-line bg-panel">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="border-b border-line text-xs uppercase tracking-wide text-faint">
              <tr>
                <th className="px-3 py-3">#</th>
                <th className="px-3 py-3">Trader</th>
                <th className="px-3 py-3">Tier</th>
                <th className="px-3 py-3 text-right">Score</th>
                <th className="px-3 py-3 text-right">Conf</th>
                <th className="px-3 py-3 text-right">ROI 90D</th>
                <th className="px-3 py-3 text-right">MDD</th>
                <th className="px-3 py-3 text-right">Sharpe</th>
                <th className="px-3 py-3">Risk</th>
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
                    {TIER_LABELS[item.tier] ?? item.tier}
                  </td>
                  <td className="px-3 py-2 text-right text-strong">{num(item.score, 1)}</td>
                  <td className="px-3 py-2 text-right text-muted">
                    {item.confidence === null ? "N/A" : `${Math.round(item.confidence * 100)}%`}
                  </td>
                  <td className="px-3 py-2 text-right text-body">{num(item.roi_90d, 2, "%")}</td>
                  <td className="px-3 py-2 text-right text-body">{num(item.mdd_90d, 2, "%")}</td>
                  <td className="px-3 py-2 text-right text-body">{num(item.sharpe)}</td>
                  <td className="px-3 py-2 capitalize text-muted">{item.risk_level ?? "unknown"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
