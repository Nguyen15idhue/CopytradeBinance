import { Source, Table } from "../ui";

export default function TestingSection() {
  return (
    <div className="space-y-4">
      <h3 id="testing-unit" className="scroll-mt-24 text-base font-semibold text-strong">
        Unit test
      </h3>
      <p className="text-sm text-body">
        Công thức ROI, MDD, Sharpe, WinRate, profit factor; normalize/score; confidence;
        pre-filter/tier; AI schema/template.
      </p>

      <h3 id="testing-integration" className="scroll-mt-24 text-base font-semibold text-strong">
        Integration test
      </h3>
      <p className="text-sm text-body">
        Collector → DB; quant → metric; scoring → score/band; API contract; AI analyze/cached/RBAC/
        budget; settings preview/rollback/audit; rate limit.
      </p>

      <h3 id="testing-e2e" className="scroll-mt-24 text-base font-semibold text-strong">
        E2E
      </h3>
      <Table head={["Luồng", "Nội dung"]}>
        <tr>
          <td className="px-3 py-2 text-body">Auth</td>
          <td className="px-3 py-2 text-muted">Đăng nhập, theme, đăng xuất</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Settings</td>
          <td className="px-3 py-2 text-muted">Preview, save, rollback</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Analytics</td>
          <td className="px-3 py-2 text-muted">Screener, Detail, Compare, Risk, Ranking</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Docs</td>
          <td className="px-3 py-2 text-muted">Technical docs, TOC, search, anchor</td>
        </tr>
      </Table>

      <h3 id="testing-gate" className="scroll-mt-24 text-base font-semibold text-strong">
        Gate
      </h3>
      <p className="text-sm text-body">
        Backend test pass; ruff pass; frontend build pass; E2E pass; check_refs 0 lỗi; không secret,
        không file rác.
      </p>

      <Source>docs/kehoach/06-kiem-thu-van-hanh-bao-mat.md, frontend/scripts/e2e.mjs</Source>
    </div>
  );
}
