# 03 — Kế hoạch AI Agent tích hợp CopytradeBinance

> Trạng thái: kế hoạch, chưa triển khai.
> Phạm vi: agent chat nổi góc phải + search tự nhiên + tool DB/code/docs/web.
> Người dùng: chỉ admin.

## 1. Quyết định đã chốt

| # | Quyết định |
|---|---|
| 1 | Web search dùng **Tavily** (nhanh, nhẹ, trả snippet + citation cho agent). Không có key → tắt web tool, không tự bịa. |
| 2 | Có tool định nghĩa sẵn + **read-only SQL** được query toàn bộ dữ liệu nghiệp vụ hiện tại. |
| 3 | Chỉ **admin** dùng agent. |
| 4 | “An toàn” mặc định = Low Risk + risk_score ≤ 40 + không veto + các ngưỡng Low Risk. |
| 5 | Làm đầy đủ: icon chat góc phải dưới, mở panel chat, hỏi và thực thi được các yêu cầu. |
| 6 | Lưu hội thoại/tool/citation vào DB. |
| 7 | Dùng `AI_MODEL_PRIMARY`; sau này đổi model trong `.env`. |

## 2. Mục tiêu sản phẩm

Người dùng bấm icon chat ở góc phải dưới và hỏi bằng tiếng Việt:

- “Top 10 trader mở copy trading an toàn, ít rủi ro, lợi nhuận tốt.”
- “Phân tích trader 5143921081414022657, vốn tôi 100$, có phù hợp copy không?”
- “Hệ thống tính Sharpe và risk_score thế nào?”
- “So sánh trader A và B.”
- “Tìm trader an toàn, còn slot, vốn tối thiểu ≤ 100$ thay vì lọc thủ công.”
- “Dữ liệu collector có mới không?”

Agent phải:
- trả lời dựa trên dữ liệu thật;
- chỉ rõ nguồn;
- không bịa số;
- không đưa lời khuyên đầu tư;
- nói rõ khi thiếu dữ liệu.

## 3. Kiến trúc tổng thể

```text
Browser
  └── Floating Chat / Screener search
          ↓
  POST /api/v1/agent/chat (SSE)
          ↓
  Agent Orchestrator (admin only)
    ├── Planner + router
    ├── Tool loop (max 8 bước)
    ├── Evidence ledger
    ├── Answer verifier
    └── Answer composer
          ↓
  Tools
    ├── search_traders
    ├── get_trader_profile
    ├── compare_traders
    ├── get_ranking
    ├── get_risk_events
    ├── analyze_portfolio_fit
    ├── sql_query (read-only)
    ├── search_knowledge (code + docs)
    ├── web_search (Tavily)
    └── get_data_health
          ↓
  PostgreSQL (business tables + agent sessions)
  Knowledge index
  Tavily
```

## 4. Tool layer

Mọi tool trả cùng một cấu trúc:

```json
{
  "data": {},
  "meta": {
    "source": "database",
    "as_of": "2026-11-07T18:40:00+07:00",
    "row_ids": ["5143921081414022657"],
    "config_version": 5
  },
  "evidence": [
    {"id": "roi_90d", "label": "ROI 90D", "value": 30.3, "unit": "%"}
  ]
}
```

### 4.1 `search_traders`

Input có cấu trúc, không cho LLM tự viết SQL:

```json
{
  "tier": ["high_upper", "qualified_upper"],
  "risk_level": ["none", "low"],
  "risk_score_max": 40,
  "low_risk_eligible": true,
  "no_veto": true,
  "min_runtime_days": 90,
  "max_mdd_90d": 20,
  "max_leverage": 5,
  "min_sharpe": 0.5,
  "min_confidence": 0.8,
  "min_score": 70,
  "has_slot": true,
  "min_copy_usd_max": null,
  "sort": [{"field": "risk_score", "dir": "asc"}, {"field": "score", "dir": "desc"}],
  "limit": 10
}
```

Output: danh sách trader + metrics + risk + score + evidence.

### 4.2 `get_trader_profile`

Lấy:
- trader, tier, reasons;
- 10 metrics;
- score/band/breakdown/hard_flags;
- risk_level/risk_score/veto/events;
- performance 7/30/90/180D;
- positions/trades/transfers gần nhất;
- data freshness/confidence.

### 4.3 `compare_traders`

- 2–4 trader;
- bảng so sánh;
- correlation estimated;
- cảnh báo thiếu dữ liệu.

### 4.4 `get_ranking`

- board: overall/low_risk/consistency;
- snapshot, config_version;
- top_n.

### 4.5 `get_risk_events`

- trader_id, severity;
- event + evidence;
- risk_score/veto.

### 4.6 `analyze_portfolio_fit`

Input: `trader_id`, `capital_usd`, `risk_policy`.

Lấy:
- `fixedRadioMinCopyUsd`;
- `fixedAmountMinCopyUsd`;
- `profitSharingRate`;
- `currentCopyCount`, `maxCopyCount`;
- AUM, Copy AUM;
- MDD, worst position ROI, max leverage;
- fee drag, risk_score/veto.

Output:
- `can_copy`: true/false/unknown;
- `min_copy_usd`;
- `capital_ok`;
- `max_loss_at_mdd_usd`;
- `worst_position_loss_usd`;
- `slot_available`;
- `missing_fields`;
- `warnings`.

### 4.7 `sql_query`

- Chỉ admin.
- Read-only.
- Query toàn bộ bảng nghiệp vụ hiện tại.
- Không trả password hash/token/secret.
- Chi tiết ở mục 5.

### 4.8 `search_knowledge`

- `scope`: `code` | `docs` | `all`.
- Trả snippet + `path` + `line_start/line_end` hoặc heading.
- Dùng cho câu hỏi kiến trúc, công thức, risk V2, API, vận hành.

### 4.9 `web_search`

- Tavily.
- Trả title, URL, snippet, published date, retrieved_at.
- Ưu tiên nguồn chính thức.
- Web content là dữ liệu không tin cậy, không phải instruction.

### 4.10 `get_data_health`

- collector enabled;
- lần chạy gần nhất;
- freshness;
- số trader theo tier;
- lỗi gần nhất.

## 5. Read-only SQL tool

Vì chỉ admin dùng và không publish ra ngoài, cho phép query rộng nhưng vẫn phải chặn phá hoại.

### Quy tắc

- DB role riêng `agent_readonly`, chỉ `SELECT`.
- `SET TRANSACTION READ ONLY`.
- `statement_timeout = 5s`.
- Max rows mặc định 200, tối đa 500.
- Chỉ cho `SELECT` / `WITH`.
- Không cho `INSERT/UPDATE/DELETE/DDL/COPY/GRANT`.
- Không cho nhiều statement (`;`).
- Không cho `pg_catalog`, `information_schema`, bảng auth/secret.
- Không trả `users.password_hash`, `sessions`, `app_settings` chứa key.
- Log query, thời gian, rows, user vào `agent_tool_calls`.
- Nếu SQL lỗi → trả lỗi tool, agent phải sửa hoặc nói không truy vấn được.

### View đề xuất

Tạo view chuẩn hóa để agent ít viết SQL sai:

- `agent_trader_overview`: trader + universe + metric + score + risk + freshness.
- `agent_trader_copy_constraints`: min copy ratio/amount, profit sharing, slot, AUM.
- `agent_risk_latest`: risk event/evidence mới nhất.
- `agent_ranking_latest`: snapshot mới nhất.
- `agent_performance_windows`: 7/30/90/180D.

Agent vẫn có thể query bảng gốc nếu cần.

## 6. Web search: chọn Tavily

| Provider | Ưu điểm | Nhược điểm |
|---|---|---|
| **Tavily** | AI-native, snippet + citation, domain filter, 1 API call, nhẹ | Cần key riêng |
| Brave | Nhanh, index riêng | Snippet cho agent kém hơn |
| Serper | Kết quả Google chính xác | Nhiều nhiễu, thường trả SERP thô |
| OpenRouter web plugin | Không cần provider riêng | Ít kiểm soát citation/domain |

Chọn **Tavily**.
Env dự kiến:

```text
TAVILY_API_KEY=...
AGENT_WEB_SEARCH_ENABLED=true
AGENT_WEB_SEARCH_MAX_RESULTS=5
```

Nếu không có key:
- web tool tắt;
- agent trả lời “chưa cấu hình web search”;
- không tự bịa nguồn internet.

Cache kết quả web 24h trong DB/Redis để giảm cost/latency.

## 7. Code/docs RAG

### Index

Bảng `knowledge_chunks`:

```text
id, source_type (code/docs), path, line_start, line_end,
heading, content, commit_sha, updated_at, tsv, embedding nullable
```

Giai đoạn đầu:
- full-text search PostgreSQL;
- chunk theo file/heading/function;
- trả snippet + path + line.

Giai đoạn sau:
- embedding nếu cần semantic search;
- vẫn giữ citation path/line.

### Build index

Backend Docker image hiện không chứa `docs/` và source frontend. Cần một trong hai:

1. Build index trong CI từ repo, copy `knowledge_chunks.jsonl` vào image.
2. Mount repo read-only trong môi trường nội bộ và chạy index script.

Đề xuất: build index trong CI, gắn `commit_sha` để tránh lẫn phiên bản.

## 8. Agent loop

```text
Nhận câu hỏi
  ↓
Planner: phân loại ý định + chọn tool
  ↓
Tool call 1 → observation
  ↓
Tool call 2 → observation
  ↓
... tối đa 8 bước
  ↓
Composer: trả lời tiếng Việt
  ↓
Verifier: kiểm tra số/citation/advice
  ↓
Lưu DB + stream kết quả
```

Quy tắc:
- Không có tool result → không khẳng định số liệu.
- Nếu tool trả `unknown` → nói unknown.
- Nếu dữ liệu cũ > 150 phút → cảnh báo.
- Nếu câu hỏi mơ hồ → nêu giả định hoặc hỏi lại 1 lần.
- Không tự gọi tool ghi dữ liệu.

## 9. Chống bịa

### Evidence ledger

Mỗi message có:
- `facts[]`: metric, value, trader_id, source, as_of.
- `citations[]`: DB row, docs path, URL.
- `assumptions[]`.
- `missing_data[]`.

### Verifier

Sau khi model trả lời:
- trích xuất mọi số;
- đối chiếu facts;
- nếu số không có nguồn → sửa/xóa/refuse;
- kiểm tra lời khuyên đầu tư;
- kiểm tra trader_id không bị đổi;
- kiểm tra đơn vị (%/USDT/x).

### Answer contract

```json
{
  "answer": "tiếng Việt",
  "facts": [],
  "citations": [],
  "assumptions": [],
  "missing_data": [],
  "confidence": "high|medium|low",
  "next_actions": []
}
```

UI hiển thị `answer`, bảng facts, citation chips, cảnh báo.

## 10. UI: icon chat góc phải

### Nút nổi

- Fixed bottom-right.
- Icon chat/sparkles.
- Chỉ hiện với admin.
- Có badge trạng thái: idle/streaming/error.
- `aria-label="Mở trợ lý AI"`.

### Panel

Desktop:
- drawer phải, rộng 420–480px, cao gần full.
- Header: “Trợ lý AI”, model đang dùng, nút chat mới, đóng.
- Message list.
- Suggested prompts khi mới mở.
- Input + nút gửi/dừng.
- Tool trace collapsible: “Đã truy vấn 10 trader”, “Đã đọc risk V2”.
- Citation chips.
- Bảng kết quả trader có nút “Mở chi tiết”, “Áp dụng bộ lọc”.

Mobile:
- Full-screen sheet.
- Nút đóng.
- Keyboard-safe input.

Phím tắt:
- `Esc` đóng.
- `Ctrl/Cmd + Enter` gửi.

### Session

- Lưu DB.
- Danh sách session gần đây.
- Đổi tên/xóa.
- Giữ 90 ngày (cấu hình).

## 11. Search tự nhiên trong Screener

Thêm ô:

```text
Mô tả trader bạn muốn tìm...
```

Parser trả filter object, UI hiển thị chips:

- Rủi ro: thấp
- MDD ≤ 20%
- Sharpe ≥ 0.5
- Score ≥ 70
- Còn slot
- Vốn tối thiểu ≤ 100$

Nút `Áp dụng` gọi Screener API hiện tại.
Không thay đổi filter thủ công; chỉ điền sẵn.

## 12. Dữ liệu & migration

### Bảng mới

```text
agent_sessions
  id, user_id, title, model, created_at, updated_at, archived_at

agent_messages
  id, session_id, role, content, facts, citations, assumptions,
  missing_data, tokens, cost_usd, latency_ms, created_at

agent_tool_calls
  id, message_id, tool_name, arguments, result_summary,
  status, duration_ms, error, created_at

agent_citations
  id, message_id, source_type, ref, url, snippet, as_of

agent_feedback
  id, message_id, rating, comment, created_at

knowledge_chunks
  id, source_type, path, line_start, line_end, heading,
  content, commit_sha, tsv, embedding nullable, updated_at
```

### Bổ sung dữ liệu

- `ai_usage` thêm `feature` (`report`/`agent`) hoặc bảng `agent_usage`.
- `trader_metrics.metrics.profile` bổ sung:
  - `min_copy_fixed_ratio_usd`
  - `min_copy_fixed_amount_usd`
  - `profit_sharing_rate`
  - `max_copiers`
  - `total_copiers`
  - `margin_balance`
- Hoặc ưu tiên view `agent_trader_copy_constraints` đọc từ `portfolio_snapshots.raw`.

## 13. API

```text
POST   /api/v1/agent/chat              SSE stream
GET    /api/v1/agent/sessions
GET    /api/v1/agent/sessions/{id}
PATCH  /api/v1/agent/sessions/{id}
DELETE /api/v1/agent/sessions/{id}
POST   /api/v1/agent/search            NL → filters
POST   /api/v1/agent/feedback
GET    /api/v1/agent/health
```

SSE events:

```text
token
tool_call
tool_result
citation
warning
done
error
```

RBAC: `require_admin`.
Rate limit: 20 request/phút/admin, 1 concurrent/session.
Timeout: 120s/request, tool 10s, SQL 5s.

## 14. Model & config

- Agent dùng `AI_MODEL_PRIMARY`.
- Fallback `AI_MODEL_FALLBACK`.
- Resolve qua `get_ai_config` hiện tại: DB override > env.
- Nếu muốn đổi bằng `.env`:
  - để trống override model trong Settings;
  - hoặc thêm hiển thị “model hiệu lực” trong panel.
- Model phải hỗ trợ tool calling.
- Nếu model không hỗ trợ native tool calling:
  - dùng JSON tool protocol (structured output);
  - giảm số tool/lần;
  - log rõ.
- Sau này đổi `.env` sang DeepSeek V4.1 Flash không cần sửa code.

## 15. Ví dụ luồng

### Top 10 an toàn

1. `search_traders` với policy mặc định.
2. Nếu < 10 kết quả → trả đúng số lượng.
3. `get_risk_events` cho các trader top.
4. Composer tạo bảng + lý do.
5. Verifier đối chiếu từng số.
6. Citation DB + as_of.

### Trader + 100$

1. `get_trader_profile`.
2. `sql_query` lấy min copy/profit sharing/slot từ snapshot.
3. `analyze_portfolio_fit`.
4. Nếu min copy > 100 → “không thể copy với 100$”.
5. Nếu đủ → tính MDD tiền, worst position, leverage, phí.
6. Trả lời “phù hợp về mặt kỹ thuật” hoặc “không phù hợp”, kèm cảnh báo.

### Hỏi code

1. `search_knowledge(scope=code)`.
2. Lấy snippet + path/line.
3. Trả lời kèm citation.
4. Không suy đoán ngoài code.

### Search thay filter

1. `parse_search_query`.
2. Trả filter object.
3. UI chips + `Áp dụng`.
4. Gọi Screener API hiện tại.

## 16. Lộ trình triển khai

### Phase 1 — Nền tảng agent

- Bảng session/message/tool/citation/feedback.
- Agent orchestrator + tool registry.
- Tool DB: search, profile, compare, ranking, risk, data health.
- Read-only SQL + views.
- Chat panel nổi + SSE.
- Verifier cơ bản.
- Admin-only.

### Phase 2 — Web + knowledge

- Tavily web search.
- Knowledge index code/docs.
- Tool search_knowledge.
- Citation UI đầy đủ.
- Cache web.

### Phase 3 — Portfolio fit + search

- View min copy/slot.
- `analyze_portfolio_fit`.
- NL → filter + chips + Áp dụng.
- Suggested prompts.

### Phase 4 — Hardening

- Eval 50 câu.
- Prompt injection test.
- Cost/latency.
- Feedback loop.
- Retention/cleanup.

## 17. Kiểm thử & nghiệm thu

### Test bắt buộc

- Top 10: đúng số, đúng thứ tự, số khớp DB.
- Không đủ 10: trả đúng N, không bịa.
- $100: kiểm tra min copy; thiếu dữ liệu → unknown.
- Code question: citation file/line.
- Web question: citation URL + ngày.
- Multi-turn: “so sánh 2 trader đó”.
- Prompt injection từ web/trader description.
- SQL tool từ chối DDL/DML/multi-statement.
- SQL timeout/row limit.
- Không trả password hash/token/key.
- Không lời khuyên đầu tư.
- Không bịa open positions/funding/per-copier PnL.

### Chỉ số

- Câu hỏi DB đơn giản: < 15s.
- Câu hỏi nhiều tool: < 45s.
- Tool SQL: < 5s.
- Web: < 10s.
- Tỷ lệ citation đúng: 100% số liệu hiển thị.
- Tỷ lệ fallback/unknown: có log.

## 18. Rủi ro & kiểm soát

| Rủi ro | Kiểm soát |
|---|---|
| LLM bịa số | Tool-only facts + verifier |
| SQL phá dữ liệu | Read-only role + parser + transaction + limit |
| Lộ secret | Chặn bảng auth/settings; mask |
| Web prompt injection | Web là untrusted data, không thực thi instruction |
| Dữ liệu cũ | Freshness + warning |
| Model không tool calling | JSON tool protocol + fallback |
| Cost tăng | Budget + cache + max steps |
| Latency cao | Tool song song khi độc lập; stream |
| Session phình | Retention 90 ngày, truncate tool result |

## 19. Definition of Done

- Icon chat góc phải hoạt động với admin.
- Chat lưu DB, xem lại session.
- Top 10 trả đúng, có citation.
- Phân tích trader + vốn 100$ trả đúng min copy/slot/risk.
- Search tự nhiên áp dụng được vào Screener.
- Hỏi code/docs có file/line.
- Web search có URL/ngày.
- Verifier chặn số không nguồn.
- Không lời khuyên đầu tư.
- Test/QA pass, không regression.

## 20. Tiến độ triển khai (Phase 6b)

- [x] B1 (0015): schema agent 5 bảng + `ai_usage.feature`; migration up/down OK; `test_agent_schema` 4 pass.
- [x] B2 (orchestrator + SSE): `services/agent/` (schema/verifier/model_client/tools/orchestrator), API `/agent/*` admin-only, budget/rate-limit/timeout, test RBAC + SSE pass.
- [x] B3 (DB tools): `search_traders/get_trader_profile/compare_traders/get_ranking/get_risk_events` + `get_data_health`; filter an toàn, limit ≤50, evidence + as_of; test 4 pass.
- [x] B4 (SQL read-only): migration `0016_agent_views` + `sql_tools.py`; test 4 pass.
- [x] B5 (floating chat UI): `AgentLauncher/Panel`, SSE client, session CRUD; chỉ admin; E2E PASS.
- [x] B6 (QA Phase 1): full backend 145 pass, ruff/build/E2E/check_refs pass.
- [x] B7 (Tavily web search): tool + cache 24h + test pass.
- [x] B8 (knowledge index): bảng `knowledge_chunks` + CLI + tool `search_knowledge`; dry-run OK; test pass.
- [x] B9 (citation + verifier): check đơn vị/trader_id/advice + contract + citation UI nhóm nguồn; test 6 pass; E2E PASS.
- [x] B10 (portfolio fit): `evaluate_fit` + tool `analyze_portfolio_fit`; test 5 pass.
- [x] B11 (NL screener search): parser + endpoint + UI; test + E2E pass.
