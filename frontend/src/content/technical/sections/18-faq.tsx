import { Source } from "../ui";

const FAQ: Array<[string, string]> = [
  ["Vì sao Sharpe hiển thị N/A?", "Binance không công bố hoặc chưa đủ mẫu. Không chấm 0."],
  ["Vì sao MDD chỉ dùng published?", "ChartItems bị pha loãng bởi nạp/rút; tự tính MDD từ chart sẽ sai."],
  ["Vì sao không có vị thế đang mở?", "Binance BAPI không cung cấp."],
  ["Vì sao không có PnL từng copier?", "Binance chỉ trả copier PnL tổng hợp."],
  ["Vì sao fee có thể âm?", "Rebate từ sàn."],
  ["Vì sao tier thay đổi?", "Dữ liệu list thay đổi hoặc bị hạ theo totalOrder."],
  ["Vì sao High (A) vẫn score trung bình?", "Tier chỉ dùng dữ liệu list; score dùng nhiều chỉ số sâu hơn."],
  ["Vì sao Bị loại không hẳn là xấu?", "Có thể mới chạy, hết slot, không giao dịch 7 ngày hoặc thiếu dữ liệu."],
  ["Vì sao AI có lúc dùng template?", "Primary/fallback lỗi hoặc JSON không hợp lệ."],
  ["Vì sao correlation không dùng chia vốn?", "Là ước tính, bị ảnh hưởng nạp/rút, không phải nhân quả."],
];

export default function FaqSection() {
  return (
    <div className="space-y-3">
      {FAQ.map(([question, answer]) => (
        <div key={question} className="rounded-xl border border-line bg-app/40 p-3">
          <p className="text-sm font-semibold text-strong">{question}</p>
          <p className="mt-1 text-sm text-body">{answer}</p>
        </div>
      ))}
      <Source>docs/huong-dan-nguoi-moi.md, docs/kehoach/02-data-contract-binance.md</Source>
    </div>
  );
}
