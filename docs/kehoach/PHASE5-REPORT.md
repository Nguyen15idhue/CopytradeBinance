# PHASE 5 REPORT — AI + Settings + Hardening + Ranking/Help

> Ngày: 07/11/2026 · Phạm vi 5.1–5.6 · Trạng thái: **ĐẠT GATE**

## 1. Gate

| Tiêu chí | Kết quả |
|---|---|
| AI không sửa score/ranking | Integration test so score trước/sau: bằng nhau |
| AI trả JSON hoặc template | 8 unit test: primary OK, invalid → fallback, cả 2 lỗi → template, evidence sai → template |
| Mọi report có evidence | Schema bắt buộc `evidence_ids` + allowlist; live report có 15 evidence |
| Đổi trọng số tạo version mới | 17 version trong DB; rollback active OK |
| API key không lộ | Lưu mã hoá Fernet; response chỉ `configured/masked`; test assert secret không có trong body/DB plaintext |
| Rate limit | Login 5/phút/IP; API 100/phút/user; test request thứ 4 (limit 3) → 429 |
| Backup restore | Dump 65 MB; restore DB tạm **11.185 trader**, alembic `0013_audit_logs` |
| Ranking dùng được | 3 board API + UI; E2E tab render |
| Help đủ nội dung | 8 mục, 5 hình SVG, TOC + search + mobile drawer + print |
| Test | Backend **114 passed** (container); E2E PASS |
| Dependency scan | `pip-audit` 0, `npm audit` 0 |
| Secret scan | `.env` không track; không match pattern secret |

## 2. Số liệu AI (live)

| Chỉ số | Giá trị |
|---|---|
| Thời gian 1 report | 44,3s |
| Model dùng | fallback `nvidia/nemotron-3-ultra-550b-a55b:free` |
| Primary | `nemotron-3.5-super-vl` trả nội dung không phải JSON → fallback |
| Cost | 0 USD (free tier) |
| Tokens | 606 prompt / 1.251 completion |
| Evidence | id, tier, confidence, ROI, MDD, Sharpe, WinRate, orders, leverage, worst ROI, profit factor, payoff, copy AUM ratio, copier PnL, R04 |

Cấu hình `.env` đã đổi do gemma free bị 429:
`AI_MODEL_PRIMARY=nvidia/nemotron-3.5-super-vl:free`,
`AI_MODEL_FALLBACK=nvidia/nemotron-3-ultra-550b-a55b:free`.

## 3. Đã triển khai

```text
models: ai_report.py (ai_reports, ai_usage), audit_log.py
migrations 0012 (ai), 0013 (audit)
services/ai/{schema,prompt,openrouter,service}.py
services/settings_service.py, services/crypto.py
api/v1/{ai,settings,ranking}.py
worker/scheduler.py            đọc collector config mỗi vòng 60s
frontend: AIReportPanel, SettingsPage, RankingPage, HelpPage, OnboardingBanner,
          HelpIllustrations (5 SVG), mobile nav drawer
infra/nginx CSP, backup.sh, prometheus-alerts.yml, docs/deployment.md
```

## 4. Kiểm thử theo bước

| Bước | Test |
|---|---|
| 5.1 | 8 unit OpenRouter/schema/template; 2 integration API (analyze/cached/RBAC/budget/score) |
| 5.2 | 2 unit validation; 2 integration version/preview/rollback/audit/RBAC; E2E preview→save→rollback |
| 5.3 | 4 integration: crypto, key encrypted, metrics/nginx headers, rate limit; backup + restore thật |
| 5.4 | 1 integration contract 3 board + 422 + RBAC + run; E2E Ranking |
| 5.5 | E2E Help (8 mục, ≥4 figure, TOC ≥8, anchor, search, banner persist) |
| 5.6 | Backend 114 passed; build; E2E full; audit; secret scan; check_refs 174/0 |

## 5. Quyết định

- AI key: env là nguồn chính, có thể override mã hoá qua Settings (Fernet derive `JWT_SECRET`).
- Cooldown 24h + dedupe hash; budget ngày 2 USD / tháng 20 USD (free nên chưa chạm).
- `ai_reports` giữ tối đa theo nhu cầu; không tự xóa; cooldown dựa report mới nhất.
- Ranking đọc snapshot; nếu version active chưa có score thì tự rebuild trước khi chụp.
- Đổi scoring version sẽ rebuild score ngay; rollback cũng rebuild.
- Help dùng nội dung tĩnh + SVG, không gọi AI, không lấy số live.

## 6. Vấn đề đã biết

1. Primary `nemotron-3.5-super-vl` không ổn định JSON (reasoning model) → thường dùng fallback.
2. Chart bundle > 500 kB (recharts) — cần code-split ở Phase 6.
3. Nginx cache DNS: recreate backend phải restart nginx (đã ghi nhận).
4. `ai_usage` test cleanup xóa dữ liệu test; live report đã xóa theo fixture test.
5. Ranking snapshot cũ vẫn giữ; UI chỉ hiển thị bản mới nhất.

## 7. Kết luận

Phase 5 đạt gate: AI có kiểm soát, settings version hoá + rollback, hardening cơ bản,
ranking và trang hướng dẫn cho người mới hoạt động. Sẵn sàng Phase 6 — Testing + Deploy + Beta.
