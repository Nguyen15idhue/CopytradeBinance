import { ScoringPipelineDiagram } from "../../../components/docs/TechIllustrations";
import { Source, Table } from "../ui";

export default function ScoringSection() {
  return (
    <div className="space-y-4">
      <p className="text-body">
        Score là điểm tổng hợp tương đối theo cohort và cấu hình. Score không phải khuyến nghị đầu tư
        và không được dùng để che dữ liệu thiếu.
      </p>

      <h3 id="scoring-nhom" className="scroll-mt-24 text-base font-semibold text-strong">
        Bảy nhóm và 19 component
      </h3>
      <Table head={["Nhóm", "Component"]}>
        <tr>
          <td className="px-3 py-2 text-body">Quản trị rủi ro</td>
          <td className="px-3 py-2 text-muted">MDD, Calmar, max leverage, worst position ROI</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Độ ổn định</td>
          <td className="px-3 py-2 text-muted">Positive days, ROI stability</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Khả năng sinh lời</td>
          <td className="px-3 py-2 text-muted">ROI 90D, excess return, PnL scale</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Chất lượng giao dịch</td>
          <td className="px-3 py-2 text-muted">Profit factor, payoff, WinRate order</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Hiệu quả copy</td>
          <td className="px-3 py-2 text-muted">Copier PnL, copy AUM ratio, copiers</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Hiệu quả vốn</td>
          <td className="px-3 py-2 text-muted">PnL/AUM, AUM</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Độ tin cậy dữ liệu</td>
          <td className="px-3 py-2 text-muted">Confidence, sample size</td>
        </tr>
      </Table>

      <ScoringPipelineDiagram />

      <h3 id="scoring-trong-so" className="scroll-mt-24 text-base font-semibold text-strong">
        Trọng số mặc định
      </h3>
      <p className="text-sm text-body">
        Quản trị rủi ro 20 · Độ ổn định 20 · Khả năng sinh lời 20 · Chất lượng giao dịch 15 · Hiệu
        quả copy 10 · Độ tin cậy dữ liệu 10 · Hiệu quả vốn 5.
      </p>

      <h3 id="scoring-chuan-hoa" className="scroll-mt-24 text-base font-semibold text-strong">
        Chuẩn hoá
      </h3>
      <p className="text-sm text-body">
        Percentile rank trong cohort, winsorization để giảm outlier. Missing component không bị coi
        là 0; bị loại khỏi trọng số hoặc ghi missing. Score cuối là weighted average của các nhóm có
        mặt.
      </p>

      <h3 id="scoring-hard-filter" className="scroll-mt-24 text-base font-semibold text-strong">
        Hard filters
      </h3>
      <Table head={["Mã", "Điều kiện"]}>
        <tr>
          <td className="px-3 py-2 text-body">HF01</td>
          <td className="px-3 py-2 text-muted">Status khác ACTIVE</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">HF02</td>
          <td className="px-3 py-2 text-muted">Tier excluded</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">HF03</td>
          <td className="px-3 py-2 text-muted">Runtime &lt; 30 ngày</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">HF04</td>
          <td className="px-3 py-2 text-muted">Không đủ tổng số lệnh theo tier</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">HF05</td>
          <td className="px-3 py-2 text-muted">Dữ liệu cũ &gt; 150 phút</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">HF06</td>
          <td className="px-3 py-2 text-muted">Confidence &lt; 0,5</td>
        </tr>
      </Table>

      <h3 id="scoring-band" className="scroll-mt-24 text-base font-semibold text-strong">
        Band
      </h3>
      <p className="text-sm text-body">
        ≥ 85 Xuất sắc · ≥ 70 Tốt · ≥ 55 Trung bình · ≥ 40 Yếu · &lt; 40 Rủi ro cao.
      </p>
      <p className="text-sm text-body">
        Band không quyết định board Low Risk. Risk V2 có veto riêng; score cao vẫn có thể bị risk
        high nếu Sharpe âm và bị cấm khỏi Low Risk.
      </p>

      <h3 id="scoring-version" className="scroll-mt-24 text-base font-semibold text-strong">
        Config version
      </h3>
      <p className="text-sm text-body">
        Đổi trọng số tạo version mới. Score cũ giữ nguyên; version active được rebuild. Rollback
        cũng rebuild. Ranking đọc <code>config_version</code> để tránh trộn version.
      </p>

      <Source>
        backend/app/services/scoring.py, backend/app/services/scoring_service.py,
        docs/kehoach/03-bo-chi-so-va-scoring.md
      </Source>
    </div>
  );
}
