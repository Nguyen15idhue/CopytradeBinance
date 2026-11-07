import { Source } from "../ui";

export default function ChangelogSection() {
  return (
    <div className="space-y-4">
      <h3 id="changelog-version" className="scroll-mt-24 text-base font-semibold text-strong">
        Version tài liệu
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>07/11/2026 — Tạo bộ tài liệu kỹ thuật, 20 mục.</li>
        <li>07/11/2026 — Đồng bộ thuật ngữ tiếng Việt và prompt AI v2.</li>
        <li>07/11/2026 — Cập nhật Risk V2: R01–R19, risk_score, veto, Low Risk eligibility.</li>
      </ul>

      <h3 id="changelog-pham-vi" className="scroll-mt-24 text-base font-semibold text-strong">
        Phạm vi
      </h3>
      <p className="text-sm text-body">
        Áp dụng cho Phase 5. Không bao gồm Phase 6 (deploy beta) nếu chưa triển khai.
      </p>

      <h3 id="changelog-nguon" className="scroll-mt-24 text-base font-semibold text-strong">
        Nguồn chính
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>docs/kehoach/01-pham-vi-va-kien-truc.md</li>
        <li>docs/kehoach/02-data-contract-binance.md</li>
        <li>docs/kehoach/03-bo-chi-so-va-scoring.md</li>
        <li>docs/kehoach/06-kiem-thu-van-hanh-bao-mat.md</li>
        <li>docs/api.md, docs/deployment.md</li>
        <li>docs/kehoach/PHASE5-REPORT.md, SESSION.md</li>
      </ul>

      <Source>docs/ky-thuat/README.md</Source>
    </div>
  );
}
