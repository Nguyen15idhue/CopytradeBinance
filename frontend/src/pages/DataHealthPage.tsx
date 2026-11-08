import { useQuery } from "@tanstack/react-query";

import { getCollectorStatus, runCollectorJob } from "../lib/api";
import { getStoredUser } from "../lib/auth";
import {
  JOB_KIND_LABELS,
  JOB_STATUS_LABELS,
  LAYER_LABELS,
  TIER_LABELS,
  label,
} from "../i18n/vi";

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
  const isAdmin = getStoredUser()?.role === "admin";

  if (query.isLoading) {
    return <div className="h-40 animate-pulse rounded-2xl bg-panel" />;
  }

  if (query.isError || !query.data) {
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/5 p-6">
        <h1 className="text-lg font-semibold text-danger">Không tải được Sức khỏe dữ liệu</h1>
        <p className="mt-2 text-sm text-muted">
          {query.error instanceof Error ? query.error.message : "Lỗi không xác định"}
        </p>
      </div>
    );
  }

  const data = query.data;
  const tiers = ["high_upper", "qualified_upper", "watch", "excluded"];
  const total = Object.values(data.tiers).reduce((sum, value) => sum + value, 0);
  const watchTotal =
    (data.tiers.watch ?? 0) +
    (data.tiers.qualified_upper ?? 0) +
    (data.tiers.high_upper ?? 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Sức khỏe dữ liệu</h1>
          <p className="mt-2 text-muted">
            Trạng thái bộ thu thập 2 tầng, độ phủ universe và lần chạy gần nhất.
          </p>
        </div>
        <span
          className={`rounded-full border px-3 py-1 text-xs uppercase ${
            data.enabled
              ? "border-emerald-500/40 bg-emerald-500/10 text-accent"
              : "border-red-500/40 bg-red-500/10 text-danger"
          }`}
        >
          {data.enabled ? "Bộ thu thập đang bật" : "Công tắc dừng đang bật"}
        </span>
      </div>

      <section>
        <div className="mb-3 flex items-end justify-between">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">
            Universe theo nhóm
          </h2>
          <p className="text-sm text-muted">
            Tổng {total.toLocaleString("vi-VN")} · Theo dõi {watchTotal.toLocaleString("vi-VN")}
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {tiers.map((tier) => (
            <div key={tier} className="rounded-xl border border-line bg-panel p-4">
              <p className="text-xs uppercase tracking-wide text-faint">
                {label(TIER_LABELS, tier)}
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
                <th className="pb-2 text-right">Số request</th>
                <th className="pb-2 text-right">Bản ghi</th>
                <th className="pb-2 text-right">Lỗi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {Object.entries(LAYER_LABELS).map(([layer, layerLabel]) => {
                const run = data.latest_runs[layer];
                return (
                  <tr key={layer}>
                    <td className="py-2 text-body">{layerLabel}</td>
                    <td className="py-2">
                      {run ? (
                        <span
                          className={
                            run.status === "success" ? "text-accent" : "text-warn"
                          }
                        >
                          {label(JOB_STATUS_LABELS, run.status, run.status)}
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
            Lưu trữ dữ liệu thô
          </h2>
          <p className="mt-3 text-2xl font-semibold">
            {data.raw_archive.files.toLocaleString("vi-VN")} tệp
          </p>
          <p className="text-sm text-muted">{formatBytes(data.raw_archive.bytes)}</p>
          <p className="mt-2 text-xs text-faint">
            Nén sau 7 ngày, giữ 90 ngày, không commit vào git.
          </p>
        </section>

        <section className="rounded-2xl border border-line bg-panel p-5">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-sm font-medium uppercase tracking-wide text-faint">
              Job thủ công
            </h2>
            {isAdmin ? (
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={async () => {
                    await runCollectorJob("scan");
                    await query.refetch();
                  }}
                  className="rounded-lg border border-line px-3 py-1.5 text-sm text-body"
                >
                  Chạy scan
                </button>
                <button
                  type="button"
                  onClick={async () => {
                    await runCollectorJob("deep");
                    await query.refetch();
                  }}
                  className="rounded-lg border border-line px-3 py-1.5 text-sm text-body"
                >
                  Chạy deep
                </button>
              </div>
            ) : null}
          </div>
          {data.jobs.length === 0 ? (
            <p className="mt-3 text-sm text-muted">Chưa có job nào.</p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm">
              {data.jobs.slice(0, 10).map((job) => (
                <li key={job.id} className="flex items-center justify-between gap-3">
                  <span className="text-body">
                    {label(JOB_KIND_LABELS, job.kind, job.kind)} ·{" "}
                    {label(JOB_STATUS_LABELS, job.status, job.status)}
                  </span>
                  <span className="text-xs text-faint">
                    {formatDate(job.finished_at ?? job.started_at ?? job.requested_at ?? null)}
                  </span>
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
