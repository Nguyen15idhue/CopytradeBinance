import { Callout, Source, Table } from "../ui";

export default function RiskSection() {
  return (
    <div className="space-y-4">
      <Callout tone="warn" title="Nguyên tắc">
        <p>
          Risk event không tự loại trader. Nó chỉ tạo cảnh báo, kèm evidence và ảnh hưởng confidence.
        </p>
      </Callout>

      <h3 id="risk-rules" className="scroll-mt-24 text-base font-semibold text-strong">
        R01–R11
      </h3>
      <Table head={["Mã", "Điều kiện", "Severity"]}>
        <tr>
          <td className="px-3 py-2 text-body">R01</td>
          <td className="px-3 py-2 text-muted">Runtime &lt; 30 ngày</td>
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
          <td className="px-3 py-2 text-muted">Max leverage &gt; 10x</td>
          <td className="px-3 py-2 text-muted">high</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R05</td>
          <td className="px-3 py-2 text-muted">Max leverage &gt; 20x</td>
          <td className="px-3 py-2 text-muted">critical</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R06</td>
          <td className="px-3 py-2 text-muted">Position ROI ≤ −80%</td>
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
          <td className="px-3 py-2 text-muted">Dữ liệu cũ &gt; 150 phút</td>
          <td className="px-3 py-2 text-muted">medium</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R10</td>
          <td className="px-3 py-2 text-muted">Copier PnL âm, lead dương</td>
          <td className="px-3 py-2 text-muted">high</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">R11</td>
          <td className="px-3 py-2 text-muted">Copy AUM &lt; 5% AUM</td>
          <td className="px-3 py-2 text-muted">medium</td>
        </tr>
      </Table>

      <h3 id="risk-severity" className="scroll-mt-24 text-base font-semibold text-strong">
        Severity và risk level
      </h3>
      <p className="text-sm text-body">
        <code>critical</code> → Nghiêm trọng · <code>high</code> → Cao · <code>medium</code> → Trung
        bình · <code>low_sample</code> → Mẫu nhỏ · <code>confidence_penalty</code> → Trừ điểm tin
        cậy · <code>insufficient</code> → Chưa đủ dữ liệu · <code>none</code> → Không có ·{" "}
        <code>unknown</code> → Chưa rõ.
      </p>

      <h3 id="risk-evidence" className="scroll-mt-24 text-base font-semibold text-strong">
        Evidence
      </h3>
      <pre className="overflow-x-auto rounded-lg border border-line bg-app p-3 text-xs text-body">
{`{"field": "mdd_90d", "value": 31.34, "threshold": 30, "rule": "R03"}`}
      </pre>
      <p className="text-sm text-body">
        Evidence giúp kiểm tra vì sao cảnh báo được tạo. Không dùng risk event như tín hiệu mua/bán.
      </p>

      <Source>backend/app/services/risk_rules.py, docs/kehoach/03-bo-chi-so-va-scoring.md</Source>
    </div>
  );
}
