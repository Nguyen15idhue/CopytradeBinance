import { Callout, Source } from "../ui";

export default function CompareSection() {
  return (
    <div className="space-y-4">
      <h3 id="compare-bang" className="scroll-mt-24 text-base font-semibold text-strong">
        So sánh
      </h3>
      <p className="text-sm text-body">
        So sánh 2–4 trader. Bảng gồm tier, score, band, confidence, risk, ROI, MDD, Sharpe, WinRate,
        leverage, profit factor, runtime, copier PnL, Copy AUM. Chart ROI lũy kế từ chartItems.
      </p>

      <h3 id="compare-tuong-quan" className="scroll-mt-24 text-base font-semibold text-strong">
        Tương quan
      </h3>
      <Callout tone="warn" title="Correlation là ước tính">
        <p>
          Tương quan tính từ ROI lũy kế chartItems, sai phân theo ngày, bị pha loãng bởi nạp/rút.
          Cần tối thiểu 30 ngày mẫu. Không dùng để chia vốn hoặc position sizing.
        </p>
      </Callout>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Không phải quan hệ nhân quả.</li>
        <li>Không phản ánh rủi ro đuôi.</li>
        <li>Không thay thế risk review.</li>
      </ul>

      <Source>backend/app/services/compare.py, docs/api.md</Source>
    </div>
  );
}
