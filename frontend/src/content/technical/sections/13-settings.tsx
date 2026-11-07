import { Source, Table } from "../ui";

export default function SettingsSection() {
  return (
    <div className="space-y-4">
      <h3 id="settings-tab" className="scroll-mt-24 text-base font-semibold text-strong">
        Các tab
      </h3>
      <p className="text-sm text-body">
        Chấm điểm · Quy tắc rủi ro · AI · Thu thập dữ liệu · Sức khỏe dữ liệu · Xếp hạng · Hệ thống.
      </p>

      <h3 id="settings-scoring" className="scroll-mt-24 text-base font-semibold text-strong">
        Scoring
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Đổi trọng số tạo version mới.</li>
        <li>Preview impact hiển thị trader, số đổi band, top thay đổi.</li>
        <li>Score cũ giữ nguyên; version active rebuild.</li>
        <li>Rollback tạo version mới và rebuild.</li>
      </ul>

      <h3 id="settings-hard-filter" className="scroll-mt-24 text-base font-semibold text-strong">
        Hard filters
      </h3>
      <p className="text-sm text-body">
        HF01–HF06 thuộc scoring version. Không sửa trực tiếp score. Có thể xem JSON cấu hình trong
        tab Quy tắc rủi ro.
      </p>

      <h3 id="settings-ai" className="scroll-mt-24 text-base font-semibold text-strong">
        AI
      </h3>
      <p className="text-sm text-body">
        Model chính/dự phòng, budget ngày/tháng, bật/tắt AI report. API key chỉ hiển thị masked;
        override key lưu mã hoá Fernet.
      </p>

      <h3 id="settings-collector" className="scroll-mt-24 text-base font-semibold text-strong">
        Collector
      </h3>
      <p className="text-sm text-body">
        Scan/performance/detail/trades interval. Worker đọc cấu hình mỗi vòng. Lưu chu kỳ có audit.
      </p>

      <h3 id="settings-audit" className="scroll-mt-24 text-base font-semibold text-strong">
        Audit và RBAC
      </h3>
      <Table head={["Vai trò", "Quyền"]}>
        <tr>
          <td className="px-3 py-2 text-body">Admin</td>
          <td className="px-3 py-2 text-muted">Xem và sửa cấu hình</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Viewer</td>
          <td className="px-3 py-2 text-muted">Chỉ xem</td>
        </tr>
      </Table>

      <Source>
        backend/app/services/settings_service.py, backend/app/api/v1/settings.py,
        frontend/src/pages/SettingsPage.tsx, docs/api.md
      </Source>
    </div>
  );
}
