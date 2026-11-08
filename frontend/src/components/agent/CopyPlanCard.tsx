import { useState } from "react";
import type { ReactNode } from "react";

import type { AgentCopyPlan, CopyPlanField } from "../../types/agent";

const SOURCE_LABEL: Record<string, string> = {
  published: "Binance",
  derived: "Suy ra",
  computed: "Tính toán",
  platform: "Nền tảng",
  user: "Bạn nhập",
  default: "Mặc định",
  missing: "Thiếu",
};

const STATUS_LABEL: Record<string, string> = {
  ok: "Có dữ liệu",
  defaulted: "Mặc định",
  missing: "Thiếu",
  needs_choice: "Cần chọn",
  blocked: "Không hợp lệ",
  infeasible: "Không khả thi",
  user_choice: "Tùy chọn",
  inapplicable: "Không áp dụng",
};

const MODE_LABEL: Record<string, string> = {
  fixed_ratio: "Tỉ lệ cố định",
  fixed_amount: "Số tiền cố định",
};

const FIELD_LABEL: Record<string, string> = {
  copy_amount_usd: "Số tiền sao chép",
  cost_per_order_usd: "Chi phí mỗi lệnh",
  max_cost_per_order_pct: "Chi phí tối đa mỗi lệnh",
  total_stop_loss_usd: "Tổng cắt lỗ",
  take_profit_pct: "Chốt lời",
  stop_loss_pct: "Cắt lỗ",
  max_slippage_pct: "Trượt giá tối đa",
  copy_existing_positions: "Sao chép vị thế hiện có",
  better_entry_price: "Sao chép giá vào lệnh tốt hơn",
  close_all_at_take_profit: "Đóng tất cả tại giá chốt",
  auto_invest: "Đầu tư tự động",
};

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function formatValue(value: unknown, unit?: string | null): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Bật" : "Tắt";
  if (typeof value === "number") {
    const base = value.toLocaleString("vi-VN", { maximumFractionDigits: 2 });
    return unit ? `${base} ${unit}` : base;
  }
  return String(value);
}

function statusTone(status: string): string {
  if (status === "missing" || status === "blocked" || status === "infeasible") {
    return "border-warn/40 bg-warn/10 text-warn";
  }
  if (status === "needs_choice" || status === "user_choice") {
    return "border-line bg-app text-muted";
  }
  return "border-line bg-app text-faint";
}

function Badge({ label, tone }: { label: string; tone: string }) {
  return (
    <span className={`rounded border px-1.5 py-0.5 text-[10px] ${tone}`}>{label}</span>
  );
}

function FieldRow({ label, field }: { label: string; field: CopyPlanField }) {
  const source = SOURCE_LABEL[field.source] ?? field.source;
  const status = STATUS_LABEL[field.status] ?? field.status;
  const value = formatValue(field.value, field.unit);
  const range =
    isNumber(field.min) && isNumber(field.max)
      ? `${formatValue(field.min, field.unit)} – ${formatValue(field.max, field.unit)}`
      : null;
  return (
    <div className="rounded-lg border border-line bg-panel px-2.5 py-2">
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs text-muted">{label}</span>
        <div className="flex shrink-0 gap-1">
          <Badge label={source} tone="border-line bg-app text-faint" />
          <Badge label={status} tone={statusTone(field.status)} />
        </div>
      </div>
      <p className="mt-1 text-sm font-medium text-strong">{value}</p>
      {range ? <p className="mt-0.5 text-[11px] text-faint">Biên: {range}</p> : null}
      {field.note ? <p className="mt-0.5 text-[11px] text-faint">{field.note}</p> : null}
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-1.5">
      <h4 className="text-[11px] font-semibold uppercase tracking-wide text-faint">
        {title}
      </h4>
      {children}
    </section>
  );
}

export default function CopyPlanCard({ plan }: { plan: AgentCopyPlan }) {
  const [copied, setCopied] = useState(false);
  const canCopy = plan.can_copy;
  const badge =
    canCopy === true
      ? { label: "Đủ điều kiện", tone: "border-accent/40 bg-accent/10 text-accent" }
      : canCopy === false
        ? { label: "Chưa phù hợp", tone: "border-warn/40 bg-warn/10 text-warn" }
        : { label: "Chưa đủ dữ liệu", tone: "border-line bg-app text-muted" };
  const mode = String(plan.copy_mode.value ?? "");
  const modeLabel = MODE_LABEL[mode] ?? "Cần chọn";
  const top = Array.isArray(plan.symbols.top)
    ? (plan.symbols.top as Array<{ symbol?: string; share_pct?: number }>)
    : [];
  const tradfi = Array.isArray(plan.symbols.tradfi)
    ? (plan.symbols.tradfi as string[])
    : [];

  async function copyJson() {
    try {
      await navigator.clipboard.writeText(JSON.stringify(plan, null, 2));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="mt-2 rounded-xl border border-line bg-app/40 p-3 text-left">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-strong">Cấu hình tham chiếu</p>
          <p className="text-[11px] text-faint">
            Trader {plan.trader_id} · plan v{plan.version}
            {plan.limits_version ? ` · ${plan.limits_version}` : ""}
          </p>
        </div>
        <Badge label={badge.label} tone={badge.tone} />
      </div>

      <div className="mt-3 space-y-3">
        <Section title="Bắt buộc">
          <div className="grid gap-1.5 sm:grid-cols-2">
            <div className="rounded-lg border border-line bg-panel px-2.5 py-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs text-muted">Loại sao chép</span>
                <Badge label={modeLabel} tone={statusTone(plan.copy_mode.status)} />
              </div>
              <p className="mt-1 text-sm font-medium text-strong">{modeLabel}</p>
              {plan.copy_mode.note ? (
                <p className="mt-0.5 text-[11px] text-faint">{String(plan.copy_mode.note)}</p>
              ) : null}
            </div>
            <FieldRow label={FIELD_LABEL.copy_amount_usd} field={plan.copy_amount_usd} />
            <FieldRow label={FIELD_LABEL.cost_per_order_usd} field={plan.cost_per_order_usd} />
            <FieldRow
              label={FIELD_LABEL.max_cost_per_order_pct}
              field={plan.max_cost_per_order_pct}
            />
          </div>
        </Section>

        <Section title="Ký hiệu">
          <div className="rounded-lg border border-line bg-panel px-2.5 py-2">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-muted">Phạm vi</span>
              <Badge label={plan.symbols.status} tone={statusTone(plan.symbols.status)} />
            </div>
            <p className="mt-1 text-sm text-strong">
              {plan.symbols.value
                ? formatValue(plan.symbols.value)
                : plan.symbols.mode === "all"
                  ? "Toàn bộ symbol"
                  : "Mặc định Binance"}
            </p>
            {top.length > 0 ? (
              <div className="mt-1.5 flex flex-wrap gap-1">
                {top.map((item) => (
                  <span
                    key={String(item.symbol)}
                    className="rounded bg-elevated px-1.5 py-0.5 text-[10px] text-muted"
                  >
                    {item.symbol}
                    {isNumber(item.share_pct) ? ` · ${item.share_pct}%` : ""}
                  </span>
                ))}
              </div>
            ) : null}
            {tradfi.length > 0 ? (
              <p className="mt-1 text-[11px] text-muted">
                TradFi (ước tính): {tradfi.join(", ")}
              </p>
            ) : null}
          </div>
        </Section>

        <Section title="Rủi ro vị thế">
          <div className="grid gap-1.5 sm:grid-cols-3">
            <FieldRow label={FIELD_LABEL.total_stop_loss_usd} field={plan.total_stop_loss_usd} />
            <FieldRow label={FIELD_LABEL.take_profit_pct} field={plan.take_profit_pct} />
            <FieldRow label={FIELD_LABEL.stop_loss_pct} field={plan.stop_loss_pct} />
          </div>
        </Section>

        <Section title="Cài đặt nâng cao">
          <div className="grid gap-1.5 sm:grid-cols-2">
            <FieldRow label={FIELD_LABEL.max_slippage_pct} field={plan.max_slippage_pct} />
            <FieldRow label={FIELD_LABEL.copy_existing_positions} field={plan.copy_existing_positions} />
            <FieldRow label={FIELD_LABEL.better_entry_price} field={plan.better_entry_price} />
            <FieldRow label={FIELD_LABEL.close_all_at_take_profit} field={plan.close_all_at_take_profit} />
            <FieldRow label={FIELD_LABEL.auto_invest} field={plan.auto_invest} />
            <div className="rounded-lg border border-line bg-panel px-2.5 py-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs text-muted">Chế độ ký quỹ</span>
                <Badge label={plan.margin_mode.status} tone={statusTone(plan.margin_mode.status)} />
              </div>
              <p className="mt-1 text-sm font-medium text-strong">
                {plan.margin_mode.value === "copy_lead"
                  ? `Copy lead${plan.margin_mode.lead_mode ? ` (${plan.margin_mode.lead_mode})` : ""}`
                  : "—"}
              </p>
            </div>
            <div className="rounded-lg border border-line bg-panel px-2.5 py-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs text-muted">Đòn bẩy</span>
                <Badge label={plan.leverage.status} tone={statusTone(plan.leverage.status)} />
              </div>
              <p className="mt-1 text-sm font-medium text-strong">
                {plan.leverage.value === "copy_lead" ? "Copy lead" : "—"}
              </p>
              <p className="mt-0.5 text-[11px] text-faint">
                Max {formatValue(plan.leverage.lead_max, "x")} · TB{" "}
                {formatValue(plan.leverage.lead_avg, "x")}
              </p>
            </div>
          </div>
        </Section>

        {plan.warnings.length > 0 ? (
          <Section title="Cảnh báo">
            <ul className="space-y-1 rounded-lg border border-warn/30 bg-warn/5 px-2.5 py-2">
              {plan.warnings.map((item, index) => (
                <li key={index} className="text-[11px] text-warn">
                  • {item}
                </li>
              ))}
            </ul>
          </Section>
        ) : null}

        {plan.missing_fields.length > 0 ? (
          <p className="text-[11px] text-faint">
            Thiếu dữ liệu: {plan.missing_fields.join(", ")}
          </p>
        ) : null}

        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-line pt-2">
          <p className="max-w-[70%] text-[10px] text-faint">
            Cấu hình tham chiếu theo dữ liệu hiện có, không phải lời khuyên đầu tư.
          </p>
          <button
            type="button"
            onClick={copyJson}
            className="rounded border border-line px-2 py-1 text-[11px] text-muted hover:bg-elevated"
          >
            {copied ? "Đã copy JSON" : "Copy JSON"}
          </button>
        </div>
      </div>
    </div>
  );
}
