import { Source, Table } from "../ui";

const TERMS: Array<[string, string]> = [
  ["ROI", "Tỷ suất sinh lời trong cửa sổ 7/30/90/180 ngày"],
  ["PnL", "Lợi nhuận/lỗ tuyệt đối (USDT)"],
  ["MDD", "Mức sụt giảm lớn nhất từ đỉnh, dùng published"],
  ["Sharpe", "Lợi nhuận điều chỉnh biến động; null = N/A"],
  ["WinRate order", "Order thắng / tổng order đóng"],
  ["WinRate position", "Vị thế thắng / tổng vị thế đóng"],
  ["Profit Factor", "Tổng lãi / |tổng lỗ|"],
  ["Payoff", "Lãi trung bình / |lỗ trung bình|"],
  ["AUM", "Tổng tài sản quản lý"],
  ["Copy AUM", "Vốn của copier"],
  ["Leverage", "Đòn bẩy từ position-history"],
  ["Confidence", "Độ tin cậy dữ liệu 0–1"],
  ["Tier", "Nhóm tiềm năng ở tầng danh sách"],
  ["Excluded", "Bị loại khỏi shortlist"],
  ["Low sample", "Mẫu nhỏ, kết luận kém tin cậy"],
  ["N/A", "Không có dữ liệu, không phải 0"],
  ["Evidence", "Bằng chứng của risk event hoặc AI"],
  ["Snapshot", "Bản chụp ranking tại một thời điểm"],
  ["Config version", "Phiên bản cấu hình scoring"],
];

export default function GlossarySection() {
  return (
    <div className="space-y-4">
      <Table head={["Thuật ngữ", "Nghĩa"]}>
        {TERMS.map(([term, definition]) => (
          <tr key={term}>
            <td className="px-3 py-2 font-medium text-body">{term}</td>
            <td className="px-3 py-2 text-muted">{definition}</td>
          </tr>
        ))}
      </Table>
      <Source>docs/huong-dan-nguoi-moi.md, docs/kehoach/03-bo-chi-so-va-scoring.md</Source>
    </div>
  );
}
