import { Callout, Source } from "../ui";

export default function AiSection() {
  return (
    <div className="space-y-4">
      <p className="text-body">
        AI Report tạo nhận định kỹ thuật bằng tiếng Việt, dựa trên dữ liệu đã chuẩn hóa và có
        evidence. AI không sửa score/ranking.
      </p>

      <h3 id="ai-prompt" className="scroll-mt-24 text-base font-semibold text-strong">
        Prompt v2
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-body">
        <li>Trả lời hoàn toàn bằng tiếng Việt.</li>
        <li>Summary 3–4 câu, có ít nhất 2 chỉ số kèm giá trị.</li>
        <li>Mỗi điểm mạnh/điểm cần lưu ý có chỉ số + giá trị + ý nghĩa/ngưỡng.</li>
        <li>Nêu trade-off và giới hạn dữ liệu.</li>
        <li>Không đưa lời khuyên đầu tư.</li>
      </ul>

      <h3 id="ai-luong" className="scroll-mt-24 text-base font-semibold text-strong">
        Luồng model
      </h3>
      <pre className="overflow-x-auto rounded-lg border border-line bg-app p-3 text-xs text-body">
{`primary → fallback → template`}
      </pre>
      <p className="text-sm text-body">
        Primary lỗi/JSON invalid → fallback. Fallback lỗi → template tất định. Template v2 cũng phân
        tích theo số liệu.
      </p>

      <h3 id="ai-schema" className="scroll-mt-24 text-base font-semibold text-strong">
        Schema và evidence
      </h3>
      <p className="text-sm text-body">
        Field bắt buộc: summary, strengths, weaknesses, risk_flags, missing_data, evidence_ids.
        Evidence phải nằm trong allowlist.
      </p>

      <Callout tone="warn" title="Giới hạn">
        <p>
          Model có thể trả sai/thiếu field. Không đảm bảo phát hiện mọi rủi ro. Không thay thế đọc
          số liệu gốc.
        </p>
      </Callout>

      <h3 id="ai-budget" className="scroll-mt-24 text-base font-semibold text-strong">
        Budget và cooldown
      </h3>
      <p className="text-sm text-body">
        Cooldown 24 giờ/trader. Budget ngày/tháng cấu hình trong Settings. Dedupe theo hash dữ liệu
        đầu vào.
      </p>

      <h3 id="ai-agent" className="scroll-mt-24 text-base font-semibold text-strong">
        AI Agent chat (Phase 6b)
      </h3>
      <p className="text-sm text-body">
        Chat SSE admin-only góc phải dưới. Orchestrator chạy tool loop tối đa 8 bước, timeout 120
        giây, verifier kiểm tra số có evidence và chặn lời khuyên đầu tư. Hội thoại, tool call và
        citation lưu vào bảng agent_sessions/messages/tool_calls/citations.
      </p>

      <Source>backend/app/services/ai/, docs/kehoach/PHASE5-REPORT.md, docs/api.md</Source>
    </div>
  );
}
