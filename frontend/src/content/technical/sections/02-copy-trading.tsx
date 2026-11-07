import { Callout, Source } from "../ui";

export default function CopyTradingSection() {
  return (
    <div className="space-y-4">
      <p className="text-body">
        Copy trading cho phép tài khoản copier sao chép lệnh của lead trader. Kết quả giữa lead và
        copier không giống hệt nhau do trễ, trượt giá, phí và chênh lệch vốn.
      </p>

      <h3 id="copy-co-che" className="scroll-mt-24 text-base font-semibold text-strong">
        Cơ chế copy
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>
          <strong>Fixed ratio</strong>: copy theo tỷ lệ vốn.
        </li>
        <li>
          <strong>Fixed amount</strong>: copy số tiền cố định mỗi lệnh.
        </li>
        <li>Lead mở/đóng vị thế → hệ thống copy tạo lệnh tương ứng.</li>
      </ul>

      <h3 id="copy-khac-biet" className="scroll-mt-24 text-base font-semibold text-strong">
        Vì sao kết quả khác nhau
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Độ trễ giữa lệnh lead và lệnh copy.</li>
        <li>Trượt giá do thanh khoản.</li>
        <li>Phí giao dịch và funding.</li>
        <li>Đòn bẩy/ký quỹ khác nhau.</li>
        <li>Lead thay đổi chiến lược.</li>
      </ul>

      <Callout tone="danger" title="Rủi ro mất vốn">
        <p>
          Copy trading có thể mất một phần hoặc toàn bộ vốn. Đòn bẩy cao làm tăng rủi ro thanh lý.
          MDD thấp không có nghĩa là không thể lỗ sâu trong một vị thế.
        </p>
      </Callout>

      <h3 id="copy-du-lieu" className="scroll-mt-24 text-base font-semibold text-strong">
        Dữ liệu Binance có và không có
      </h3>
      <p className="text-sm text-body">
        Có ROI, PnL, MDD, Sharpe, WinRate, AUM, Copy AUM, position/trade/transfer history. Không có
        vị thế đang mở, PnL từng copier, funding, slippage, giá thanh lý hoặc lý do vào/ra lệnh.
      </p>

      <Source>docs/kehoach/02-data-contract-binance.md, docs/huong-dan-nguoi-moi.md</Source>
    </div>
  );
}
