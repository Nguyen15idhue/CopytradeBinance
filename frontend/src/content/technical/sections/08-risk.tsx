import { Callout, Source, Table } from "../ui";

export default function RiskSection() {
  return (
    <div className="space-y-4">
      <Callout tone="warn" title="Nguyên tắc">
        <p>
          Risk event không tự loại trader. Nó tạo cảnh báo, kèm evidence, và tham gia vào
          <code> risk_score</code>/<code>risk_level</code>. Chỉ board <code>low_risk</code> mới có
          điều kiện loại riêng.
        </p>
      </Callout>

      <h3 id="risk-dau-vao" className="scroll-mt-24 text-base font-semibold text-strong">
        Đầu vào
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Published 90D: MDD, Sharpe, totalOrder, copier PnL / lead PnL.</li>
        <li>
          Derived: max leverage, worst ROI, Copy AUM ratio, fee drag, HHI/top share,
          near-liquidation count, profit factor + positions count, Calmar.
        </li>
        <li>Meta: runtime_days, freshness_minutes, confidence.value.</li>
      </ul>

      <h3 id="risk-rules" className="scroll-mt-24 text-base font-semibold text-strong">
        R01–R19
      </h3>
      <Table head={["Mã", "Điều kiện", "Severity"]}>
        <tr>
          <td className="px-3 py-2 text-body">R01</td>
          <td className="px-3 py-2 text-muted">runtime_days &lt; 30</td>
          <td className="px-3 py-2 text-muted">insufficient</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R02</td>
          <td className="px-3 py-2 text-muted">MDD &gt; 20%</td>
          <td className="px-3 py-2 text-muted">high</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R03</td>
          <td className="px-3 py-2 text-muted">MDD &gt; 30%</td>
          <td className="px-3 py-2 text-muted">critical</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R04</td>
          <td className="px-3 py-2 text-muted">max leverage &gt; 10x</td>
          <td className="px-3 py-2 text-muted">high</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R05</td>
          <td className="px-3 py-2 text-muted">max leverage &gt; 20x</td>
          <td className="px-3 py-2 text-muted">critical</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R06</td>
          <td className="px-3 py-2 text-muted">worst position ROI ≤ −80%</td>
          <td className="px-3 py-2 text-muted">critical</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R07</td>
          <td className="px-3 py-2 text-muted">totalOrder &lt; 20</td>
          <td className="px-3 py-2 text-muted">low_sample</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R08</td>
          <td className="px-3 py-2 text-muted">Sharpe null</td>
          <td className="px-3 py-2 text-muted">confidence_penalty</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R09</td>
          <td className="px-3 py-2 text-muted">freshness &gt; 150 phút</td>
          <td className="px-3 py-2 text-muted">medium</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R10</td>
          <td className="px-3 py-2 text-muted">Copier PnL âm, lead PnL dương</td>
          <td className="px-3 py-2 text-muted">high</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R11</td>
          <td className="px-3 py-2 text-muted">Copy AUM ratio &lt; 5%</td>
          <td className="px-3 py-2 text-muted">medium</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R12</td>
          <td className="px-3 py-2 text-muted">fee drag &gt; 20%; fee âm bỏ qua</td>
          <td className="px-3 py-2 text-muted">medium</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R13</td>
          <td className="px-3 py-2 text-muted">HHI &gt; 0.4 hoặc top symbol &gt; 50%</td>
          <td className="px-3 py-2 text-muted">medium</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R14</td>
          <td className="px-3 py-2 text-muted">near-liquidation count ≥ 1</td>
          <td className="px-3 py-2 text-muted">high</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R15</td>
          <td className="px-3 py-2 text-muted">profit factor &lt; 1 khi positions ≥ 5</td>
          <td className="px-3 py-2 text-muted">medium</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R16</td>
          <td className="px-3 py-2 text-muted">Calmar &lt; 0</td>
          <td className="px-3 py-2 text-muted">high</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R17</td>
          <td className="px-3 py-2 text-muted">confidence &lt; 0.5 hoặc freshness null</td>
          <td className="px-3 py-2 text-muted">medium</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R18</td>
          <td className="px-3 py-2 text-muted">Sharpe &lt; 0</td>
          <td className="px-3 py-2 text-muted">high</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R19</td>
          <td className="px-3 py-2 text-muted">0 ≤ Sharpe &lt; 0.5</td>
          <td className="px-3 py-2 text-muted">medium</td>
        </tr>
      </Table>

      <h3 id="risk-evidence" className="scroll-mt-24 text-base font-semibold text-strong">
        Evidence và unknown
      </h3>
      <pre className="overflow-x-auto rounded-lg border border-line bg-app p-3 text-xs text-body">
{`{"field": "mdd_90d", "value": 31.34, "threshold": 30, "rule": "R03"}`}
      </pre>
      <p className="text-sm text-body">
        Field thiếu dữ liệu → ghi vào <code>unknown</code>, không tạo event sai. R15 chỉ xét khi
        positions ≥ 5; mẫu nhỏ → unknown. R12 bỏ qua fee âm (rebate).
      </p>

      <h3 id="risk-score" className="scroll-mt-24 text-base font-semibold text-strong">
        risk_score
      </h3>
      <pre className="overflow-x-auto rounded-lg border border-line bg-app p-3 text-xs text-body">
{`risk_score = 30 × norm(MDD)
           + 20 × norm(Leverage)
           + 15 × norm(Sharpe)
           + 15 × norm(Concentration)
           + 10 × norm(Quality)
           + 10 × norm(Copy)`}
      </pre>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>MDD: 10→0, 15→25, 20→50, 30→80, 40→100.</li>
        <li>Leverage: 3→0, 5→30, 10→70, 20→100.</li>
        <li>Sharpe: ≥1.5→0, ≥1→20, ≥0.5→50, ≥0→75, &lt;0→100, null→70.</li>
        <li>Concentration: max của HHI/top share/worst ROI/fee drag đã chuẩn hoá.</li>
        <li>Quality: max của runtime/orders/freshness/confidence.</li>
        <li>Copy: max của Copy AUM ratio và copier divergence.</li>
      </ul>
      <p className="text-sm text-body">
        Thiếu component → loại khỏi tổng và renormalize trọng số còn lại. Thiếu cả MDD và Leverage
        → <code>risk_score = null</code>.
      </p>

      <h3 id="risk-level" className="scroll-mt-24 text-base font-semibold text-strong">
        Level và veto
      </h3>
      <Table head={["risk_score", "Level"]}>
        <tr>
          <td className="px-3 py-2 text-body">0–20</td>
          <td className="px-3 py-2 text-muted">none</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">21–40</td>
          <td className="px-3 py-2 text-muted">low</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">41–60</td>
          <td className="px-3 py-2 text-muted">medium</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">61–80</td>
          <td className="px-3 py-2 text-muted">high</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">81–100</td>
          <td className="px-3 py-2 text-muted">critical</td>
        </tr>
      </Table>
      <p className="text-sm text-body">
        <code>risk_level = max(event_level, score_level)</code>. Unknown không kéo tụt event level;
        nếu score medium/high/critical thì có thể nâng level. <code>veto_reasons</code> giữ R02, R03,
        R04, R05, R06, R14, R18, R19.
      </p>

      <h3 id="risk-low-risk" className="scroll-mt-24 text-base font-semibold text-strong">
        Low-risk eligibility
      </h3>
      <p className="text-sm text-body">
        Sharpe null hoặc âm → cấm. Sharpe 0–0.5 chỉ qua khi MDD ≤ 15%, leverage ≤ 3x, runtime ≥ 180
        ngày. Board còn yêu cầu runtime ≥ 90, MDD ≤ 20%, leverage ≤ 5x, confidence ≥ 0.8 và Sharpe
        ≥ 0.
      </p>
      <Callout tone="danger" title="Ví dụ">
        <p>
          Score 90 + Sharpe âm → R18 (high), <code>low_risk_eligible = false</code>, không vào board
          Low Risk.
        </p>
      </Callout>

      <h3 id="risk-luu-tru" className="scroll-mt-24 text-base font-semibold text-strong">
        Lưu trữ và API
      </h3>
      <p className="text-sm text-body">
        <code>trader_metrics.risk_level</code>, <code>risk_score</code>, <code>risk_veto</code>{" "}
        (JSONB) + migration <code>0014_risk_v2</code>. API risk trả thêm{" "}
        <code>risk_score</code> và <code>veto_reasons</code>.
      </p>

      <Source>
        backend/app/services/risk_rules.py, backend/app/services/risk_service.py,
        backend/app/services/ranking.py, migration 0014_risk_v2,
        docs/kehoach/RISK-V2-SPEC.md
      </Source>
    </div>
  );
}
