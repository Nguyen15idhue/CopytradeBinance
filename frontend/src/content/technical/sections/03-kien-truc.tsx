import { SystemArchitectureDiagram } from "../../../components/docs/TechIllustrations";
import { Source, Table } from "../ui";

export default function KienTrucSection() {
  return (
    <div className="space-y-4">
      <h3 id="kien-truc-tong-the" className="scroll-mt-24 text-base font-semibold text-strong">
        Sơ đồ tổng thể
      </h3>
      <pre className="overflow-x-auto rounded-lg border border-line bg-app p-3 text-xs text-body">
{`Browser
  ↓
Nginx :8090
  ├── /        → frontend React/Vite
  └── /api/v1  → backend FastAPI :8010
                     ├── PostgreSQL :5432
                     ├── Redis :6379
                     └── OpenRouter (AI)
Worker → Binance BAPI → PostgreSQL + raw archive`}
      </pre>

      <SystemArchitectureDiagram />

      <h3 id="kien-truc-frontend" className="scroll-mt-24 text-base font-semibold text-strong">
        Frontend
      </h3>
      <p className="text-sm text-body">
        React 18, TypeScript strict, Vite, Tailwind, TanStack Query. Dữ liệu qua API, không gọi
        fetch rải rác. Theme token dùng chung.
      </p>

      <h3 id="kien-truc-backend" className="scroll-mt-24 text-base font-semibold text-strong">
        Backend
      </h3>
      <p className="text-sm text-body">
        FastAPI async, SQLAlchemy 2 typed model, response wrapper{" "}
        <code>{"{data, meta, error}"}</code>. Logic thuần trong <code>services/</code>, truy vấn DB
        tách khỏi công thức.
      </p>

      <h3 id="kien-truc-du-lieu" className="scroll-mt-24 text-base font-semibold text-strong">
        Nhóm bảng dữ liệu
      </h3>
      <Table head={["Nhóm", "Bảng chính"]}>
        <tr>
          <td className="px-3 py-2 text-body">Auth/config</td>
          <td className="px-3 py-2 text-muted">users, scoring_config, app_settings, audit_logs</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Trader</td>
          <td className="px-3 py-2 text-muted">traders, trader_universe, portfolio_snapshots</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Lịch sử</td>
          <td className="px-3 py-2 text-muted">performance_metrics, positions, trades, transfers</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Phân tích</td>
          <td className="px-3 py-2 text-muted">
            trader_metrics, trader_scores, risk_events, ranking_snapshots
          </td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">AI</td>
          <td className="px-3 py-2 text-muted">ai_reports, ai_usage</td>
        </tr>
      </Table>

      <h3 id="kien-truc-luong" className="scroll-mt-24 text-base font-semibold text-strong">
        Luồng request và collector
      </h3>
      <pre className="overflow-x-auto rounded-lg border border-line bg-app p-3 text-xs text-body">
{`React → /api/v1 → FastAPI → service → DB → response

Scheduler → lock → L0 scan → tier → L2 performance
          → L3 detail/position/transfer → L4 trades`}
      </pre>

      <Source>docs/kehoach/01-pham-vi-va-kien-truc.md, docs/deployment.md, docker-compose.yml</Source>
    </div>
  );
}
