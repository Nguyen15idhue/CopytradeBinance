import { Source, Table } from "../ui";

export default function VanHanhSection() {
  return (
    <div className="space-y-4">
      <h3 id="van-hanh-service" className="scroll-mt-24 text-base font-semibold text-strong">
        Dịch vụ Docker
      </h3>
      <Table head={["Service", "Vai trò"]}>
        <tr>
          <td className="px-3 py-2 text-body">db</td>
          <td className="px-3 py-2 text-muted">PostgreSQL 16</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">redis</td>
          <td className="px-3 py-2 text-muted">Redis 7</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">backend</td>
          <td className="px-3 py-2 text-muted">FastAPI :8010</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">worker</td>
          <td className="px-3 py-2 text-muted">Scheduler/collector</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">frontend</td>
          <td className="px-3 py-2 text-muted">React/Vite</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">nginx</td>
          <td className="px-3 py-2 text-muted">Reverse proxy :8090</td>
        </tr>
      </Table>

      <h3 id="van-hanh-backup" className="scroll-mt-24 text-base font-semibold text-strong">
        Backup và restore
      </h3>
      <p className="text-sm text-body">
        Backup gồm <code>pg_dump -Fc</code> + <code>.env</code>, giữ 7 ngày trong{" "}
        <code>backups/</code>. Restore vào DB tạm trước, kiểm tra alembic version và số trader, không
        restore đè DB thật khi chưa xác nhận.
      </p>

      <h3 id="van-hanh-monitoring" className="scroll-mt-24 text-base font-semibold text-strong">
        Monitoring
      </h3>
      <p className="text-sm text-body">
        <code>/metrics</code> Prometheus, alert rules trong <code>infra/prometheus-alerts.yml</code>.
        Theo dõi collector stale, lỗi API, job fail, DB size.
      </p>

      <h3 id="van-hanh-su-co" className="scroll-mt-24 text-base font-semibold text-strong">
        Sự cố thường gặp
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Nginx cache DNS sau khi recreate backend → restart nginx.</li>
        <li>Collector bị lock → kiểm tra Redis.</li>
        <li>Dữ liệu cũ → xem Data Health.</li>
        <li>AI 429/JSON lỗi → fallback/template.</li>
      </ul>

      <Source>docs/deployment.md, infra/backup.sh, scripts/backup.ps1, SESSION.md</Source>
    </div>
  );
}
