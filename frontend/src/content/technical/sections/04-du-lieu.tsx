import { DataPipelineDiagram } from "../../../components/docs/TechIllustrations";
import { Callout, Source, Table } from "../ui";

export default function DuLieuSection() {
  return (
    <div className="space-y-4">
      <h3 id="du-lieu-endpoint" className="scroll-mt-24 text-base font-semibold text-strong">
        Sáu endpoint Binance
      </h3>
      <Table head={["Endpoint", "Dữ liệu chính"]}>
        <tr>
          <td className="px-3 py-2 text-body">List</td>
          <td className="px-3 py-2 text-muted">
            Universe, ROI, PnL, MDD, WinRate, AUM, Sharpe, copier, tier đầu vào
          </td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Detail</td>
          <td className="px-3 py-2 text-muted">AUM, Copy AUM, số copier, slot, leverage, mô tả</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Performance</td>
          <td className="px-3 py-2 text-muted">ROI/PnL/MDD/Sharpe/WinRate/copier PnL theo 7/30/90/180D</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Position</td>
          <td className="px-3 py-2 text-muted">Vị thế đã đóng, leverage, PnL, ROI, thời gian giữ</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Trade</td>
          <td className="px-3 py-2 text-muted">Fill, phí, realized profit</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Transfer</td>
          <td className="px-3 py-2 text-muted">Nạp/rút</td>
        </tr>
      </Table>

      <DataPipelineDiagram />

      <h3 id="du-lieu-nguon" className="scroll-mt-24 text-base font-semibold text-strong">
        Published / Derived / Estimated
      </h3>
      <Table head={["Loại", "Nguồn", "Ví dụ"]}>
        <tr>
          <td className="px-3 py-2 text-body">Published</td>
          <td className="px-3 py-2 text-muted">Binance trả trực tiếp</td>
          <td className="px-3 py-2 text-muted">ROI, PnL, MDD, Sharpe, WinRate</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Derived</td>
          <td className="px-3 py-2 text-muted">Tính từ position/trade</td>
          <td className="px-3 py-2 text-muted">max leverage, profit factor, payoff</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Estimated</td>
          <td className="px-3 py-2 text-muted">Ước tính từ chartItems</td>
          <td className="px-3 py-2 text-muted">drawdown, tương quan</td>
        </tr>
      </Table>

      <Callout tone="warn" title="Quy tắc null">
        <p>
          <code>null</code> nghĩa là không có dữ liệu, không đổi thành 0. Sharpe null hiển thị N/A.
          MDD chỉ dùng published, không tự tính từ chartItems.
        </p>
      </Callout>

      <h3 id="du-lieu-winrate" className="scroll-mt-24 text-base font-semibold text-strong">
        WinRate order và position
      </h3>
      <p className="text-sm text-body">
        WinRate order = winOrders / totalOrder. WinRate position = vị thế thắng / tổng vị thế đóng.
        Hai chỉ số khác nhau, không trộn.
      </p>

      <h3 id="du-lieu-confidence" className="scroll-mt-24 text-base font-semibold text-strong">
        Data confidence
      </h3>
      <p className="text-sm text-body">
        Confidence 0–1 phản ánh coverage, history, freshness, continuity. Confidence thấp không có
        nghĩa trader xấu; nghĩa là kết luận kém chắc chắn.
      </p>

      <Source>docs/kehoach/02-data-contract-binance.md, docs/kehoach/03-bo-chi-so-va-scoring.md</Source>
    </div>
  );
}
