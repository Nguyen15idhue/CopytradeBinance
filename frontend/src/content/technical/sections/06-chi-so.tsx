import { Source, Table } from "../ui";

export default function ChiSoSection() {
  return (
    <div className="space-y-4">
      <h3 id="chi-so-phan-tang" className="scroll-mt-24 text-base font-semibold text-strong">
        Phân tầng chỉ số
      </h3>
      <Table head={["Tầng", "Nội dung"]}>
        <tr>
          <td className="px-3 py-2 text-body">T0</td>
          <td className="px-3 py-2 text-muted">Metadata và chất lượng dữ liệu</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">T1</td>
          <td className="px-3 py-2 text-muted">Published metrics từ Binance</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">T2</td>
          <td className="px-3 py-2 text-muted">Derived metrics từ position/trade</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">T3</td>
          <td className="px-3 py-2 text-muted">Dữ liệu không có</td>
        </tr>
      </Table>

      <h3 id="chi-so-published" className="scroll-mt-24 text-base font-semibold text-strong">
        Published
      </h3>
      <p className="text-sm text-body">
        ROI, PnL, MDD, Sharpe, WinRate order, winOrders, totalOrders, copier PnL, AUM, Copy AUM,
        margin balance, số copier, slot, profit sharing, badge, tags.
      </p>

      <h3 id="chi-so-derived" className="scroll-mt-24 text-base font-semibold text-strong">
        Derived
      </h3>
      <p className="text-sm text-body">
        Max leverage, avg leverage, margin mode, thời gian giữ, position win rate, profit factor,
        payoff, best/worst position PnL, worst position ROI, near liquidation count, long/short
        ratio, symbol concentration, total fills.
      </p>

      <h3 id="chi-so-cong-thuc" className="scroll-mt-24 text-base font-semibold text-strong">
        Công thức quan trọng
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>ROI = lợi nhuận / vốn × 100.</li>
        <li>MDD = mức sụt giảm lớn nhất từ đỉnh, dùng published.</li>
        <li>Sharpe = lợi nhuận điều chỉnh biến động; null → N/A.</li>
        <li>WinRate order = winOrders / totalOrders × 100.</li>
        <li>Profit Factor = tổng lãi / |tổng lỗ|; null nếu mẫu &lt; 5 vị thế.</li>
        <li>Payoff = lãi trung bình / |lỗ trung bình|.</li>
        <li>Calmar = ROI / MDD.</li>
        <li>Fee drag = phí / notional.</li>
        <li>Symbol concentration = notional lớn nhất / tổng notional.</li>
      </ul>

      <h3 id="chi-so-winrate" className="scroll-mt-24 text-base font-semibold text-strong">
        WinRate order và position
      </h3>
      <p className="text-sm text-body">
        Order tính trên lệnh đóng; position tính trên vị thế đóng. Hai chỉ số khác nhau, không dùng
        lẫn.
      </p>

      <h3 id="chi-so-low-sample" className="scroll-mt-24 text-base font-semibold text-strong">
        Low sample
      </h3>
      <p className="text-sm text-body">
        Mẫu nhỏ làm kết luận kém tin cậy. Không chấm 0 cho chỉ số thiếu dữ liệu; hiển thị N/A và
        gắn cảnh báo.
      </p>

      <Source>docs/kehoach/03-bo-chi-so-va-scoring.md, backend/app/services/quant/</Source>
    </div>
  );
}
