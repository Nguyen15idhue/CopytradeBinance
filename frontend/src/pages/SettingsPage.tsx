import { useEffect, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getCollectorStatus,
  getSettings,
  getSettingsVersions,
  previewSettings,
  rollbackSettings,
  saveSettings,
} from "../lib/api";
import { getStoredUser } from "../lib/auth";
import type { PreviewImpact, SettingsSnapshot } from "../types/trader";

const TABS = [
  ["scoring", "Scoring"],
  ["risk", "Risk Rules"],
  ["ai", "AI"],
  ["collector", "Data Collection"],
  ["health", "Data Health"],
  ["ranking", "Ranking"],
  ["system", "System"],
] as const;

type Tab = (typeof TABS)[number][0];

const GROUP_LABELS: Record<string, string> = {
  risk_management: "Risk Management",
  consistency: "Consistency",
  profitability: "Profitability",
  trading_quality: "Trading Quality",
  copy_performance: "Copy Performance",
  capital_efficiency: "Capital Efficiency",
  data_reliability: "Data Reliability",
};

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-line bg-panel p-5">
      <h2 className="text-sm font-medium uppercase tracking-wide text-faint">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function NumberInput({
  label,
  value,
  onChange,
  disabled,
  min = 0,
  max = 100,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  disabled: boolean;
  min?: number;
  max?: number;
}) {
  return (
    <label className="text-sm text-body">
      {label}
      <input
        type="number"
        min={min}
        max={max}
        step={1}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-1 w-full rounded-lg border border-line bg-app px-3 py-2 text-strong disabled:opacity-60"
      />
    </label>
  );
}

export default function SettingsPage() {
  const isAdmin = getStoredUser()?.role === "admin";
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("scoring");
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [ai, setAi] = useState<SettingsSnapshot["ai"] | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [collector, setCollector] = useState<SettingsSnapshot["collector"] | null>(null);
  const [preview, setPreview] = useState<PreviewImpact | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const settings = useQuery({ queryKey: ["settings"], queryFn: getSettings });
  const versions = useQuery({ queryKey: ["settings-versions"], queryFn: getSettingsVersions });
  const health = useQuery({
    queryKey: ["collector-status-settings"],
    queryFn: getCollectorStatus,
    enabled: tab === "health",
  });

  useEffect(() => {
    if (!settings.data) return;
    setWeights(settings.data.scoring.weights);
    setAi(settings.data.ai);
    setCollector(settings.data.collector);
  }, [settings.data]);

  async function run(action: () => Promise<unknown>, success: string) {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await action();
      setMessage(success);
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
      await queryClient.invalidateQueries({ queryKey: ["settings-versions"] });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Thao tác thất bại");
    } finally {
      setBusy(false);
    }
  }

  if (settings.isLoading) {
    return <div className="h-48 animate-pulse rounded-2xl bg-elevated" />;
  }
  if (settings.isError || !settings.data || !ai || !collector) {
    return (
      <div className="rounded-2xl border border-danger/30 bg-danger/5 p-5 text-danger">
        Không tải được settings.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Settings</h1>
          <p className="mt-2 text-muted">
            Cấu hình version hoá; thay đổi scoring tạo version mới, rollback được.
          </p>
        </div>
        <span className="rounded-full border border-line px-3 py-1 text-sm text-muted">
          config v{settings.data.scoring.version} · {isAdmin ? "admin" : "viewer (read-only)"}
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {TABS.map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`rounded-lg border px-3 py-1.5 text-sm ${
              tab === key ? "border-accent/40 bg-accent/10 text-accent" : "border-line text-body"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {message ? (
        <p className="rounded-lg border border-accent/30 bg-accent/10 px-3 py-2 text-sm text-accent">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </p>
      ) : null}

      {tab === "scoring" ? (
        <div className="space-y-4">
          <Card title="Trọng số scoring">
            <div className="grid gap-3 md:grid-cols-4">
              {Object.entries(weights).map(([group, weight]) => (
                <NumberInput
                  key={group}
                  label={GROUP_LABELS[group] ?? group}
                  value={weight}
                  disabled={!isAdmin || busy}
                  onChange={(value) => setWeights({ ...weights, [group]: value })}
                />
              ))}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                disabled={!isAdmin || busy}
                onClick={() =>
                  run(async () => setPreview(await previewSettings(weights)), "Đã tính preview")
                }
                className="rounded-lg border border-line px-3 py-2 text-sm text-body disabled:opacity-50"
              >
                Preview impact
              </button>
              <button
                type="button"
                disabled={!isAdmin || busy}
                onClick={() => run(() => saveSettings({ scoring: { weights } }), "Đã tạo version mới")}
                className="rounded-lg bg-emerald-500 px-3 py-2 text-sm font-medium text-slate-950 disabled:opacity-50"
              >
                Lưu version mới
              </button>
            </div>
          </Card>

          {preview ? (
            <Card title="Preview impact">
              <p className="text-sm text-body">
                {preview.traders} trader · {preview.changed_band} đổi band
              </p>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full min-w-[560px] text-left text-sm">
                  <thead className="text-xs uppercase tracking-wide text-faint">
                    <tr>
                      <th className="pb-2">Trader</th>
                      <th className="pb-2 text-right">Score cũ</th>
                      <th className="pb-2 text-right">Score mới</th>
                      <th className="pb-2 text-right">Δ</th>
                      <th className="pb-2">Band</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {preview.top_changes.map((row) => (
                      <tr key={row.id}>
                        <td className="py-2 font-mono text-xs text-body">{row.id}</td>
                        <td className="py-2 text-right text-muted">{row.old_score?.toFixed(1) ?? "—"}</td>
                        <td className="py-2 text-right text-strong">{row.new_score?.toFixed(1) ?? "—"}</td>
                        <td className="py-2 text-right text-body">{row.delta.toFixed(2)}</td>
                        <td className="py-2 text-muted">
                          {row.old_band} → {row.new_band}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          ) : null}

          <Card title="Versions">
            <div className="space-y-2">
              {(versions.data ?? []).map((version) => (
                <div
                  key={version.version}
                  className="flex flex-wrap items-center gap-3 rounded-lg border border-line px-3 py-2 text-sm"
                >
                  <span className="text-strong">v{version.version}</span>
                  {version.is_active ? (
                    <span className="rounded-full border border-accent/40 bg-accent/10 px-2 text-xs text-accent">
                      active
                    </span>
                  ) : null}
                  <span className="text-faint">{new Date(version.created_at).toLocaleString("vi-VN")}</span>
                  {isAdmin && !version.is_active ? (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        run(() => rollbackSettings(version.version), `Đã rollback v${version.version}`)
                      }
                      className="ml-auto rounded border border-line px-2 py-1 text-xs text-body"
                    >
                      Rollback
                    </button>
                  ) : null}
                </div>
              ))}
            </div>
          </Card>
        </div>
      ) : null}

      {tab === "risk" ? (
        <Card title="Risk Rules">
          <p className="text-sm text-body">
            Hard filters thuộc scoring version hiện tại. Risk events R01–R11 không tự loại trader,
            chỉ tạo cảnh báo và ảnh hưởng confidence.
          </p>
          <ul className="mt-3 space-y-1 text-sm text-muted">
            <li>HF01 — status khác ACTIVE: không xếp hạng</li>
            <li>HF02 — tier excluded: không xếp hạng</li>
            <li>HF03 — runtime &lt; 30 ngày: không xếp hạng</li>
            <li>HF04 — totalOrder &lt; 20/50/100 theo tier</li>
            <li>HF05 — dữ liệu cũ &gt; 150 phút</li>
            <li>HF06 — confidence &lt; 0.5</li>
          </ul>
          <pre className="mt-3 overflow-x-auto rounded-lg bg-app p-3 text-xs text-muted">
{JSON.stringify(settings.data.scoring.hard_filters, null, 2)}
          </pre>
        </Card>
      ) : null}

      {tab === "ai" ? (
        <Card title="AI (OpenRouter)">
          <div className="grid gap-3 md:grid-cols-2">
            <label className="text-sm text-body">
              Model chính
              <input
                value={ai.model_primary}
                disabled={!isAdmin || busy}
                onChange={(event) => setAi({ ...ai, model_primary: event.target.value })}
                className="mt-1 w-full rounded-lg border border-line bg-app px-3 py-2 text-strong disabled:opacity-60"
              />
            </label>
            <label className="text-sm text-body">
              Model dự phòng
              <input
                value={ai.model_fallback}
                disabled={!isAdmin || busy}
                onChange={(event) => setAi({ ...ai, model_fallback: event.target.value })}
                className="mt-1 w-full rounded-lg border border-line bg-app px-3 py-2 text-strong disabled:opacity-60"
              />
            </label>
            <NumberInput
              label="Budget tháng (USD)"
              value={ai.monthly_budget_usd}
              min={0}
              max={10000}
              disabled={!isAdmin || busy}
              onChange={(value) => setAi({ ...ai, monthly_budget_usd: value })}
            />
            <NumberInput
              label="Budget ngày (USD)"
              value={ai.daily_budget_usd}
              min={0}
              max={10000}
              disabled={!isAdmin || busy}
              onChange={(value) => setAi({ ...ai, daily_budget_usd: value })}
            />
          </div>
          <p className="mt-3 text-sm text-muted">
            API key: {ai.key_configured ? `đã cấu hình (${ai.key_masked})` : "chưa cấu hình"}
          </p>
          {isAdmin ? (
            <label className="mt-3 block text-sm text-body">
              Đổi API key (để trống nếu giữ nguyên)
              <input
                type="password"
                value={apiKeyInput}
                disabled={busy}
                onChange={(event) => setApiKeyInput(event.target.value)}
                autoComplete="off"
                className="mt-1 w-full rounded-lg border border-line bg-app px-3 py-2 text-strong"
              />
            </label>
          ) : null}
          <label className="mt-3 flex items-center gap-2 text-sm text-body">
            <input
              type="checkbox"
              checked={ai.enabled}
              disabled={!isAdmin || busy}
              onChange={(event) => setAi({ ...ai, enabled: event.target.checked })}
            />
            Bật AI report
          </label>
          <button
            type="button"
            disabled={!isAdmin || busy}
            onClick={() =>
              run(
                () =>
                  saveSettings({
                    ai: {
                      model_primary: ai.model_primary,
                      model_fallback: ai.model_fallback,
                      monthly_budget_usd: ai.monthly_budget_usd,
                      daily_budget_usd: ai.daily_budget_usd,
                      enabled: ai.enabled,
                      ...(apiKeyInput ? { api_key: apiKeyInput } : {}),
                    },
                  }),
                "Đã lưu cấu hình AI",
              )
            }
            className="mt-4 rounded-lg bg-emerald-500 px-3 py-2 text-sm font-medium text-slate-950 disabled:opacity-50"
          >
            Lưu cấu hình AI
          </button>
        </Card>
      ) : null}

      {tab === "collector" ? (
        <Card title="Chu kỳ thu thập">
          <div className="grid gap-3 md:grid-cols-2">
            <NumberInput
              label="Scan (phút)"
              value={collector.scan_interval_min}
              min={5}
              max={1440}
              disabled={!isAdmin || busy}
              onChange={(value) => setCollector({ ...collector, scan_interval_min: value })}
            />
            <NumberInput
              label="Performance (giờ)"
              value={collector.deep_interval_hours_watch}
              min={1}
              max={168}
              disabled={!isAdmin || busy}
              onChange={(value) =>
                setCollector({ ...collector, deep_interval_hours_watch: value })
              }
            />
            <NumberInput
              label="Detail (giờ)"
              value={collector.deep_interval_hours_qualified}
              min={1}
              max={168}
              disabled={!isAdmin || busy}
              onChange={(value) =>
                setCollector({ ...collector, deep_interval_hours_qualified: value })
              }
            />
            <NumberInput
              label="Trades (giờ)"
              value={collector.deep_interval_hours_high}
              min={1}
              max={168}
              disabled={!isAdmin || busy}
              onChange={(value) =>
                setCollector({ ...collector, deep_interval_hours_high: value })
              }
            />
          </div>
          <button
            type="button"
            disabled={!isAdmin || busy}
            onClick={() =>
              run(() => saveSettings({ collector }), "Đã lưu chu kỳ thu thập")
            }
            className="mt-4 rounded-lg bg-emerald-500 px-3 py-2 text-sm font-medium text-slate-950 disabled:opacity-50"
          >
            Lưu chu kỳ
          </button>
          <p className="mt-2 text-xs text-faint">Worker đọc cấu hình mỗi vòng lặp (60s).</p>
        </Card>
      ) : null}

      {tab === "health" ? (
        <Card title="Data Health">
          {health.data ? (
            <div className="space-y-2 text-sm">
              <p className="text-body">
                Collector: {health.data.enabled ? "bật" : "tắt"} · raw archive{" "}
                {health.data.raw_archive.files} file
              </p>
              {Object.entries(health.data.latest_runs).map(([layer, run]) => (
                <p key={layer} className="text-muted">
                  {layer}: {run ? `${run.status} · ${run.items_ok} item` : "chưa chạy"}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted">Đang tải...</p>
          )}
        </Card>
      ) : null}

      {tab === "ranking" ? (
        <Card title="Ranking">
          <p className="text-sm text-body">
            3 bảng Overall / Low Risk / Consistency dùng chung scoring version hiện tại.
            Snapshot được tạo ở trang Ranking.
          </p>
        </Card>
      ) : null}

      {tab === "system" ? (
        <Card title="System">
          <dl className="space-y-2 text-sm">
            {[
              ["App", settings.data.system.app_name],
              ["Môi trường", settings.data.system.app_env],
              ["API prefix", settings.data.system.api_v1_prefix],
              ["Scoring version", String(settings.data.scoring.version)],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between gap-3">
                <dt className="text-faint">{label}</dt>
                <dd className="text-body">{value}</dd>
              </div>
            ))}
          </dl>
        </Card>
      ) : null}
    </div>
  );
}
