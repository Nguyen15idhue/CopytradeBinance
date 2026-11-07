import { Callout, Source } from "../ui";

export default function TongQuanSection() {
  return (
    <div className="space-y-4">
      <p className="text-body">
        CopytradeBinance là công cụ <strong>screener &amp; risk analytics</strong> cho copy trading
        Binance Futures. Hệ thống thu thập dữ liệu công khai, tính chỉ số, xếp hạng và hiển thị
        rủi ro để người dùng tự quyết định.
      </p>

      <h3 id="tong-quan-lam-gi" className="scroll-mt-24 text-base font-semibold text-strong">
        Làm gì
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Thu thập list, detail, performance, position, trade, transfer từ Binance.</li>
        <li>Chuẩn hóa published/derived/estimated; gán tier và chấm score.</li>
        <li>Phát risk event, xếp hạng, so sánh và xuất CSV.</li>
        <li>Tạo nhận định AI có evidence, không sửa score/ranking.</li>
      </ul>

      <h3 id="tong-quan-khong-lam" className="scroll-mt-24 text-base font-semibold text-strong">
        Không làm gì
      </h3>
      <Callout tone="warn" title="Không phải công cụ auto-trade">
        <p>
          Không auto-trade, không kết nối API giao dịch của bạn, không paper copy, không đưa lời
          khuyên đầu tư. Hệ thống chỉ hỗ trợ quyết định.
        </p>
      </Callout>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Không hiển thị vị thế đang mở.</li>
        <li>Không có PnL từng copier.</li>
        <li>Không có funding, slippage, giá thanh lý.</li>
      </ul>

      <h3 id="tong-quan-thanh-phan" className="scroll-mt-24 text-base font-semibold text-strong">
        Thành phần
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Frontend React/Vite: Screener, Detail, Compare, Risk, Ranking, Settings, Help.</li>
        <li>FastAPI: API, auth, scoring, risk, AI, settings.</li>
        <li>PostgreSQL, Redis, worker scheduler, Nginx, OpenRouter.</li>
      </ul>

      <h3 id="tong-quan-gioi-han" className="scroll-mt-24 text-base font-semibold text-strong">
        Giới hạn
      </h3>
      <p className="text-sm text-body">
        Dữ liệu công khai có thể thiếu, trễ hoặc thay đổi. Kết quả quá khứ không đảm bảo tương lai.
        Hệ thống không thay thế quyết định của người dùng.
      </p>

      <Source>docs/kehoach/01-pham-vi-va-kien-truc.md, docs/huong-dan-nguoi-moi.md</Source>
    </div>
  );
}
