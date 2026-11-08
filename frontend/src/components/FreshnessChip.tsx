import { freshnessClass, freshnessText, type Freshness } from "../lib/freshness";

export default function FreshnessChip({ value }: { value?: Freshness | null }) {
  return (
    <span
      title={value?.as_of ? `Số liệu tại ${value.as_of}` : ""}
      aria-label="Độ mới dữ liệu"
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs ${freshnessClass(value)}`}
    >
      {freshnessText(value)}
    </span>
  );
}
