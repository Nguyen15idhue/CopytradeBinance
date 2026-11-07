import { Source, Table } from "../ui";

export default function ApiBaoMatSection() {
  return (
    <div className="space-y-4">
      <h3 id="api-auth" className="scroll-mt-24 text-base font-semibold text-strong">
        Auth
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Access token JWT 15 phút.</li>
        <li>Refresh token 7 ngày.</li>
        <li>Mật khẩu hash Argon2id.</li>
        <li>RBAC kiểm tra server-side; <code>require_admin</code>.</li>
      </ul>

      <h3 id="api-response" className="scroll-mt-24 text-base font-semibold text-strong">
        Response wrapper
      </h3>
      <pre className="overflow-x-auto rounded-lg border border-line bg-app p-3 text-xs text-body">
{`{"data": {}, "meta": {"request_id": "...", "generated_at": "..."}, "error": null}`}
      </pre>
      <pre className="overflow-x-auto rounded-lg border border-line bg-app p-3 text-xs text-body">
{`{"data": null, "error": {"code": "TRADER_NOT_FOUND", "message": "Không tìm thấy trader"}}`}
      </pre>

      <h3 id="api-pagination" className="scroll-mt-24 text-base font-semibold text-strong">
        Pagination
      </h3>
      <p className="text-sm text-body">
        Mặc định 50, tối đa 100. Positions/trades tối đa 200.
      </p>

      <h3 id="api-endpoint" className="scroll-mt-24 text-base font-semibold text-strong">
        Nhóm endpoint
      </h3>
      <p className="text-sm text-body">
        Auth · Traders/screener · Compare · Ranking · Risk · AI · Settings · Collector/data health ·
        Universe · Saved views.
      </p>

      <h3 id="api-rate-limit" className="scroll-mt-24 text-base font-semibold text-strong">
        Rate limit
      </h3>
      <Table head={["Phạm vi", "Giới hạn"]}>
        <tr>
          <td className="px-3 py-2 text-body">Login</td>
          <td className="px-3 py-2 text-muted">5/phút/IP</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">API</td>
          <td className="px-3 py-2 text-muted">100/phút/user</td>
        </tr>
        <tr>
          <td className="px-3 py-2 text-body">Vượt ngưỡng</td>
          <td className="px-3 py-2 text-muted">429</td>
        </tr>
      </Table>

      <h3 id="api-security" className="scroll-mt-24 text-base font-semibold text-strong">
        Bảo mật
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>API key AI lưu mã hoá Fernet, derive từ JWT_SECRET.</li>
        <li>Response chỉ trả configured/masked, không trả key.</li>
        <li>CSP và security headers ở Nginx.</li>
        <li>Không commit .env, secret, data.</li>
        <li>Log không chứa token/key.</li>
      </ul>

      <Source>docs/api.md, backend/app/api/, infra/nginx/, docs/deployment.md</Source>
    </div>
  );
}
