import { Link } from "react-router-dom";

const traders = [
  {
    id: "4520644381136785152",
    name: "Mẫu Đạt",
    tier: "Đạt (B)",
    description: "Trader B từ bộ dữ liệu mẫu Phase 0 — đủ dữ liệu cho vertical slice.",
    className: "border-emerald-500/30 bg-emerald-500/5",
  },
  {
    id: "5296057151807357697",
    name: "Mẫu Bị loại",
    tier: "Bị loại",
    description: "Portfolio mới, runtime < 30 ngày — dùng kiểm tra badge và lý do loại.",
    className: "border-amber-500/30 bg-amber-500/5",
  },
];

export default function DemoHomePage() {
  return (
    <div>
      <div className="max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight">Trader mẫu</h1>
        <p className="mt-2 text-muted">
          Hai trader mẫu Phase 0 dùng để kiểm tra luồng collect → raw → API → UI. Không phải
          dữ liệu thị trường realtime.
        </p>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-2">
        {traders.map((trader) => (
          <Link
            key={trader.id}
            to={`/traders/${trader.id}`}
            className={`rounded-2xl border p-5 transition hover:-translate-y-0.5 hover:border-muted ${trader.className}`}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">{trader.name}</h2>
              <span className="rounded-full border border-line px-2 py-0.5 text-xs uppercase text-body">
                {trader.tier}
              </span>
            </div>
            <p className="mt-3 text-sm text-muted">{trader.description}</p>
            <p className="mt-4 font-mono text-xs text-faint">{trader.id}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
