import { Source, Table } from "../ui";

export default function RankingSection() {
  return (
    <div className="space-y-4">
      <h3 id="ranking-board" className="scroll-mt-24 text-base font-semibold text-strong">
        Ba bảng
      </h3>
      <Table head={["Board", "Mục đích"]}>
        <tr>
          <td className="px-3 py-2 text-body">Overall</td>
          <td className="px-3 py-2 text-muted">Điểm tổng hợp sau hard filter</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Low Risk</td>
          <td className="px-3 py-2 text-muted">Ưu tiên trader ít rủi ro</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Consistency</td>
          <td className="px-3 py-2 text-muted">Ưu tiên độ ổn định, không chạy theo ROI</td>
        </tr>
      </Table>

      <h3 id="ranking-low-risk" className="scroll-mt-24 text-base font-semibold text-strong">
        Low Risk
      </h3>
      <p className="text-sm text-body">
        Điều kiện board: runtime ≥ 90 ngày, MDD ≤ 20%, max leverage ≤ 5x (hoặc null), confidence ≥
        0.8, Sharpe không null và ≥ 0.
      </p>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Sharpe null → không vào Low Risk.</li>
        <li>Sharpe âm → không vào Low Risk.</li>
        <li>
          Sharpe 0–0.5 chỉ qua khi MDD ≤ 15%, max leverage ≤ 3x, runtime ≥ 180 ngày.
        </li>
      </ul>
      <p className="text-sm text-body">
        <code>risk_rules.eligible_for_low_risk</code> là cùng logic veto; <code>ranking.py</code>{" "}
        kiểm tra thêm các ngưỡng board.
      </p>

      <h3 id="ranking-snapshot" className="scroll-mt-24 text-base font-semibold text-strong">
        Snapshot và config version
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Ranking đọc snapshot mới nhất.</li>
        <li>Mỗi snapshot gắn <code>config_version</code>.</li>
        <li>Không trộn trader/score từ nhiều version.</li>
        <li>Nếu version active chưa có score, hệ thống rebuild trước khi chụp.</li>
      </ul>

      <h3 id="ranking-ui" className="scroll-mt-24 text-base font-semibold text-strong">
        UI
      </h3>
      <p className="text-sm text-body">
        `/ranking` có 3 tab, metadata snapshot, bảng xếp hạng và link Detail. Admin có nút chạy
        ranking. Không có bảng “Lợi nhuận cao” để tránh chase ROI.
      </p>

      <Source>backend/app/api/v1/ranking.py, backend/app/services/ranking.py, docs/api.md</Source>
    </div>
  );
}
