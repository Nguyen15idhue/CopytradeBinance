export const STALE_MINUTES = 150;
export const VERY_STALE_MINUTES = 1440;

export type FreshnessLevel = "ok" | "stale" | "very_stale" | "unknown";

export interface Freshness {
  minutes: number | null;
  level: FreshnessLevel;
  as_of?: string | null;
}

export function freshnessMinutes(value?: Freshness | null): number | null {
  if (!value || value.minutes === null || value.minutes === undefined) return null;
  return value.minutes;
}

export function freshnessText(value?: Freshness | null): string {
  const minutes = freshnessMinutes(value);
  if (minutes === null) return "Chưa rõ độ mới dữ liệu";
  if (minutes < 60) return `Dữ liệu ${Math.round(minutes)} phút trước`;
  if (minutes < 1440) return `Dữ liệu cũ ${(minutes / 60).toFixed(1)} giờ`;
  return `Dữ liệu cũ ${(minutes / 1440).toFixed(1)} ngày`;
}

export function freshnessClass(value?: Freshness | null): string {
  const level = value?.level ?? "unknown";
  if (level === "ok") return "border-emerald-500/40 bg-emerald-500/10 text-accent";
  if (level === "stale") return "border-amber-500/40 bg-amber-500/10 text-warn";
  if (level === "very_stale") return "border-red-500/40 bg-red-500/10 text-danger";
  return "border-line bg-elevated text-faint";
}
