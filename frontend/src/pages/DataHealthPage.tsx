import { useQuery } from "@tanstack/react-query";

import { getCollectorStatus } from "../lib/api";

const TIER_LABELS: Record<string, string> = {
  excluded: "Excluded",
  watch: "C — Watch",
  qualified_upper: "B — Qualified",
  high_upper: "A — High",
};

const LAYER_LABELS: Record<string, string> = {
  L0: "L0 — Universe scan",
  L2: "L2 — Performance",
  L3: "L3 — Detail + positions + transfers",
  L4: "L4 — Full trades",
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("vi-VN");
}

export default function DataHealthPage() {
  const query = useQuery({
    queryKey: ["collector-status"],
    queryFn: getCollectorStatus,
    refetchInterval: 30_000,
  });

  if (query.isLoading) {
    return <div className="h-40 animate-pulse rounded-2xl bg-panel" />;
  }

  if (query.isError || !query.data) {
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/5 p-6">
        <h1 className="text-lg font-semibold text-danger">Không tải được Data Health</h1>
        <p className="mt-2 text-sm text-muted">
          {query.error instanceof Error ? query.error.message : "Lỗi không xác định"}
        </p>
      </div>
    );
  }

  const data = query.data;
  const tiers = ["excluded", "watch", "qualified_upper", "high_upper"];
  const total = Object.values(data.tiers).reduce((sum, value) => sum + value, 0);
  const watchTotal =
    (data.tiers.watch ?? 0) +
    (data.tiers.qualified_upper ?? 0) +
    (data.tiers.high_upper ?? 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Data Health</h1>
          <p className="mt-2 text-muted">
            Trạng thái collector 2 tầng, độ phủ universe và lần chạy gần nhất.
          </p>
        </div>
        <span
          className={`rounded-full border px-3 py-1 text-xs uppercase ${
            data.enabled
              ? "border-emerald-500/40 bg-emerald-500/10 text-accent"
              : "border-red-500/40 bg-red-500/10 text-danger"
          }`}
        >
          {data.enabled ? "Collector đang bật" : "Kill switch đang bật"}
        </span>
      </div>

      <section>
        <div className="mb-3 flex items-end justify-between">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">
            Universe theo tier
          </h2>
          <p className="text-sm text-muted">
            Tổng {total.toLocaleString("vi-VN")} · Watch {watchTotal.toLocaleString("vi-VN")}
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {tiers.map((tier) => (
            <div key={tier} className="rounded-xl border border-line bg-panel p-4">
              <p className="text-xs uppercase tracking-wide text-faint">
                {TIER_LABELS[tier] ?? tier}
              </p>
              <p className="mt-2 text-2xl font-semibold">
                {(data.tiers[tier] ?? 0).toLocaleString("vi-VN")}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-line bg-panel p-5">
        <h2 className="text-sm font-medium uppercase tracking-wide text-faint">
          Lần chạy gần nhất
        </h2>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-faint">
              <tr>
                <th className="pb-2">Tầng</th>
                <th className="pb-2">Trạng thái</th>
                <th className="pb-2">Xong lúc</th>
                <th className="pb-2 text-right">Request</th>
                <th className="pb-2 text-right">Items</th>
                <th className="pb-2 text-right">Lỗi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {Object.entries(LAYER_LABELS).map(([layer, label]) => {
                const run = data.latest_runs[layer];
                return (
                  <tr key={layer}>
                    <td className="py-2 text-body">{label}</td>
                    <td className="py-2">
                      {run ? (
                        <span
                          className={
                            run.status === "success" ? "text-accent" : "text-warn"
                          }
                        >
                          {run.status}
                        </span>
                      ) : (
                        <span className="text-faint">chưa chạy</span>
                      )}
                    </td>
                    <td className="py-2 text-muted">{formatDate(run?.finished_at ?? null)}</td>
                    <td className="py-2 text-right text-muted">{run?.requests ?? 0}</td>
                    <td className="py-2 text-right text-muted">{run?.items_ok ?? 0}</td>
                    <td className="py-2 text-right text-muted">{run?.error_count ?? 0}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-2xl border border-line bg-panel p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">
            Raw archive
          </h2>
          <p className="mt-3 text-2xl font-semibold">
            {data.raw_archive.files.toLocaleString("vi-VN")} file
          </p>
          <p className="text-sm text-muted">{formatBytes(data.raw_archive.bytes)}</p>
          <p className="mt-2 text-xs text-faint">
            Nén sau 7 ngày, giữ 90 ngày, không commit vào git.
          </p>
        </section>

        <section className="rounded-2xl border border-line bg-panel p-5">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">
            Job thủ công
          </h2>
          {data.jobs.length === 0 ? (
            <p className="mt-3 text-sm text-muted">Chưa có job nào trong phiên này.</p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm">
              {data.jobs
                .slice()
                .reverse()
                .slice(0, 5)
                .map((job) => (
                  <li key={job.id} className="flex items-center justify-between gap-3">
                    <span className="text-body">
                      {job.kind} · {job.status}
                    </span>
                    <span className="text-xs text-faint">{formatDate(job.started_at)}</span>
                  </li>
                ))}
            </ul>
          )}
        </section>
      </div>

      <p className="border-t border-line pt-4 text-xs text-faint">
        Cập nhật lúc {formatDate(data.generated_at)} · tự làm mới mỗi 30 giây.
      </p>
    </div>
  );
}
