import { Source, Table } from "../ui";

export default function DataHealthSection() {
  return (
    <div className="space-y-4">
      <h3 id="data-health-tang" className="scroll-mt-24 text-base font-semibold text-strong">
        Các tầng thu thập
      </h3>
      <Table head={["Tầng", "Việc làm"]}>
        <tr>
          <td className="px-3 py-2 text-body">L0</td>
          <td className="px-3 py-2 text-muted">Quét universe</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">L2</td>
          <td className="px-3 py-2 text-muted">Performance 4 cửa sổ</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">L3</td>
          <td className="px-3 py-2 text-muted">Detail + position + transfer</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">L4</td>
          <td className="px-3 py-2 text-muted">Toàn bộ trade history</td>
        </tr>
      </Table>

      <h3 id="data-health-chu-ky" className="scroll-mt-24 text-base font-semibold text-strong">
        Chu kỳ mặc định
      </h3>
      <p className="text-sm text-body">
        Scan 60 phút · performance 6 giờ · detail 12 giờ · trades 24 giờ. Có thể đổi trong Settings;
        worker đọc lại mỗi vòng 60 giây.
      </p>

      <h3 id="data-health-lock" className="scroll-mt-24 text-base font-semibold text-strong">
        Lock và retry
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Redis lock + fallback advisory lock.</li>
        <li>Retry/backoff khi Binance lỗi.</li>
        <li>Cooldown khi bị rate limit.</li>
        <li>Job skip nếu không lấy được lock.</li>
      </ul>

      <h3 id="data-health-kill-switch" className="scroll-mt-24 text-base font-semibold text-strong">
        Kill switch
      </h3>
      <p className="text-sm text-body">
        Dừng collector khẩn cấp. Job mới bị skip. Không xoá dữ liệu đã thu thập.
      </p>

      <h3 id="data-health-freshness" className="scroll-mt-24 text-base font-semibold text-strong">
        Freshness và raw archive
      </h3>
      <p className="text-sm text-body">
        Dữ liệu cũ &gt; 150 phút bị cảnh báo R09/HF05. Raw archive nén sau 7 ngày, giữ 90 ngày,
        không commit vào git.
      </p>

      <Source>
        docs/kehoach/01-pham-vi-va-kien-truc.md, backend/app/services/deep_fetch.py,
        backend/app/services/universe.py, docs/api.md
      </Source>
    </div>
  );
}
