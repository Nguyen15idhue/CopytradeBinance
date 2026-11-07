import { Callout, Source, Table } from "../ui";

export default function TierSection() {
  return (
    <div className="space-y-4">
      <p className="text-body">
        Tier là <strong>nhóm tiềm năng ở tầng danh sách</strong>, dùng để quyết định trader nào được
        lấy dữ liệu sâu và chấm điểm. Tier không phải score cuối cùng và không phải khuyến nghị đầu
        tư.
      </p>

      <Table head={["Mã backend", "UI", "Ý nghĩa"]}>
        <tr>
          <td className="px-3 py-2 font-mono text-xs text-muted">excluded</td>
          <td className="px-3 py-2 text-body">Bị loại</td>
          <td className="px-3 py-2 text-muted">Không đạt điều kiện tối thiểu</td>
        </tr>
        <tr>
          <td className="px-3 py-2 font-mono text-xs text-muted">watch</td>
          <td className="px-3 py-2 text-body">Theo dõi (C)</td>
          <td className="px-3 py-2 text-muted">Đạt điều kiện tối thiểu</td>
        </tr>
        <tr>
          <td className="px-3 py-2 font-mono text-xs text-muted">qualified_upper</td>
          <td className="px-3 py-2 text-body">Đạt (B)</td>
          <td className="px-3 py-2 text-muted">Đạt ngưỡng B ở tầng list</td>
        </tr>
        <tr>
          <td className="px-3 py-2 font-mono text-xs text-muted">high_upper</td>
          <td className="px-3 py-2 text-body">Cao (A)</td>
          <td className="px-3 py-2 text-muted">Đạt ngưỡng A ở tầng list</td>
        </tr>
      </Table>

      <h3 id="tier-dieu-kien" className="scroll-mt-24 text-base font-semibold text-strong">
        Điều kiện từng tier
      </h3>
      <p className="text-sm text-body">
        Bị loại nếu có ít nhất một điều kiện: không giao dịch 7 ngày, runtime &lt; 30 ngày, ROI ≤ 0,
        PnL ≤ 0, WinRate &lt; 40%, MDD &gt; 40%, AUM &lt; 5.000, hết slot copy.
      </p>
      <Table head={["Tiêu chí", "Theo dõi (C)", "Đạt (B)", "Cao (A)"]}>
        <tr>
          <td className="px-3 py-2 text-body">Runtime</td>
          <td className="px-3 py-2 text-muted">≥ 30 ngày</td>
          <td className="px-3 py-2 text-muted">≥ 90 ngày</td>
          <td className="px-3 py-2 text-muted">≥ 180 ngày</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">ROI</td>
          <td className="px-3 py-2 text-muted">&gt; 0</td>
          <td className="px-3 py-2 text-muted">≥ 10%</td>
          <td className="px-3 py-2 text-muted">≥ 20%</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">WinRate</td>
          <td className="px-3 py-2 text-muted">≥ 40%</td>
          <td className="px-3 py-2 text-muted">≥ 45%</td>
          <td className="px-3 py-2 text-muted">≥ 50%</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">MDD</td>
          <td className="px-3 py-2 text-muted">≤ 40%</td>
          <td className="px-3 py-2 text-muted">≤ 30%</td>
          <td className="px-3 py-2 text-muted">≤ 20%</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">AUM</td>
          <td className="px-3 py-2 text-muted">≥ 5.000</td>
          <td className="px-3 py-2 text-muted">≥ 10.000</td>
          <td className="px-3 py-2 text-muted">≥ 20.000</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Sharpe</td>
          <td className="px-3 py-2 text-muted">—</td>
          <td className="px-3 py-2 text-muted">≥ 0,5 hoặc null</td>
          <td className="px-3 py-2 text-muted">≥ 1</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Tổng số lệnh</td>
          <td className="px-3 py-2 text-muted">—</td>
          <td className="px-3 py-2 text-muted">≥ 50</td>
          <td className="px-3 py-2 text-muted">≥ 100</td>
        </tr>
      </Table>

      <h3 id="tier-upper-bound" className="scroll-mt-24 text-base font-semibold text-strong">
        Upper bound và hạ tier
      </h3>
      <Callout tone="info" title="Upper bound">
        <p>
          A/B ban đầu là giới hạn trên ở tầng danh sách. Sau đó hạ theo tổng số lệnh: A → B nếu
          <code> totalOrder &lt; 100</code>; B → C nếu <code>totalOrder &lt; 50</code>.
        </p>
      </Callout>
      <p className="text-sm text-body">
        Vì vậy mã backend có chữ <code>_upper</code>: <code>high_upper</code>,{" "}
        <code>qualified_upper</code>. UI hiển thị gọn là Cao (A) và Đạt (B).
      </p>

      <h3 id="tier-pre-score" className="scroll-mt-24 text-base font-semibold text-strong">
        Pre-score
      </h3>
      <pre className="overflow-x-auto rounded-lg border border-line bg-app p-3 text-xs text-body">
{`pre_score = 0.30 × norm(roi)
          + 0.30 × norm(−mdd)
          + 0.20 × norm(sharpe)
          + 0.10 × norm(winRate)
          + 0.10 × norm(min(runtime/180, 1))`}
      </pre>
      <p className="text-sm text-body">
        Pre-score chỉ dùng để xếp thứ tự deep fetch, không hiển thị như điểm chất lượng.
      </p>

      <h3 id="tier-excluded" className="scroll-mt-24 text-base font-semibold text-strong">
        Vì sao Bị loại không hẳn là xấu
      </h3>
      <p className="text-sm text-body">
        Có thể chỉ vì mới chạy, không giao dịch 7 ngày, hết slot, AUM thấp hoặc thiếu dữ liệu. Luôn
        đọc <code>filter_reasons</code> trước khi kết luận. Tier chỉ là cửa đầu tiên của phễu; score,
        band và risk mới là lớp đánh giá chi tiết hơn.
      </p>

      <Source>backend/app/services/funnel.py, docs/kehoach/03-bo-chi-so-va-scoring.md</Source>
    </div>
  );
}
