# AGENTS.md — CopytradeBinance

## 1. Bối cảnh

Binance Copy Trader Screener & Risk Analytics (không auto-trade).
FastAPI async + PostgreSQL 16 + Redis 7 + React/Vite/TS + Tailwind, chạy Docker Compose.
Cổng host: **web 8090**, **backend 8010**. Phase 0 đóng băng; Phase 1–4 xong; Phase 5 đang làm.

## 2. Nguyên tắc bất biến

- Không sửa `phase0/`; không tạo folder theo bước (`phase1/`, `step1/`…).
- Không commit secret, `.env`, `data/`, `node_modules`, `dist`, `graphify-out/`, artifact test.
- Không `down -v`, không xóa dữ liệu thật, không đổi port nếu task không yêu cầu.
- Không bịa số/nguồn. Thiếu dữ liệu → `null` + flag, không đổi thành `0`.
- Không đưa lời khuyên đầu tư; mọi nhận định AI phải có `evidence_ids`.
- Commit từng bước; **chỉ push khi task yêu cầu rõ**. Không force push, không `reset --hard`.

## 3. Backend (Python 3.12, FastAPI)

- Async toàn tuyến; type hint đầy đủ; `ruff` line-length 100 (`E,F,I,B,UP`).
- Cấu hình qua `app/core/config.py` (Pydantic Settings); không hardcode secret/URL.
- SQLAlchemy 2 typed model: `Mapped[...]`, `mapped_column`; import qua `app.models`.
- Migration: đánh số tiếp (`0012_...`), **không sửa migration cũ**; luôn có `downgrade()`.
- Logic thuần đặt trong `services/` (test được không cần DB); truy vấn DB tách khỏi công thức.
- Lỗi API dùng `ApiError(code, message)`, response wrapper `{data, meta, error}`.
- Auth: JWT 15p/7 ngày, Argon2id; RBAC kiểm tra **server-side** (`require_admin`).
- Pagination mặc định 50, tối đa 100 (positions/trades tối đa 200).
- Collector: retry/backoff + cooldown, Redis lock + fallback advisory, kill switch; không crawl trong test.

## 4. Dữ liệu & chỉ số

- Published (Binance) > Derived (tính từ positions/trades) > Estimated (chartItems).
- MDD chỉ dùng published; không tự tính thay thế.
- Sharpe null → `N/A`, không chấm 0. WinRate order và position tách riêng.
- Fee có thể âm (rebate) → giữ dấu. Profit factor null nếu mẫu < 5 vị thế.
- Không hiển thị dữ liệu không có: open positions, per-copier PnL, funding, slippage.
- AI chỉ nhận dữ liệu đã chuẩn hóa; không sửa score/ranking; fallback 1 lần rồi template.

## 5. Frontend (React 18, TS strict, Tailwind)

- Function component + hook; dữ liệu qua TanStack Query, không gọi fetch rải rác.
- Luôn có loading / empty / error; không để `undefined`, `NaN`, `null` lọt UI.
- Chỉ dùng token theme: `bg-app|panel|elevated`, `border-line`, `text-strong|body|muted|faint`,
  `text-accent|info|warn|danger`. Không dùng lại `slate-300/900`. Chi tiết: `docs/ui-theme.md`.
- Chart dùng CSS var (`var(--accent)`, `var(--danger)`, tick `var(--text-faint)`).
- Text UI tiếng Việt có dấu; số dùng `toLocaleString("vi-VN")`; tiền tệ ghi rõ USDT.
- Không `dangerouslySetInnerHTML` với nội dung AI/người dùng.

## 6. Test & kiểm chứng

- Backend: `pytest` phần liên quan mỗi bước; integration cần `RUN_INTEGRATION=1` (container).
- Frontend: `npm run build` (tsc + vite) mỗi bước; E2E Playwright cho luồng chạm UI.
- Full suite + E2E đầy đủ chỉ ở bước QA cuối phase.
- Không mock toàn bộ API; chỉ mock lỗi/timeout/empty. Không phụ thuộc id trader hardcode.
- Test phải xác nhận hành vi (status, shape, null, quyền), không chỉ “chạy không lỗi”.

## 7. Tài liệu & trạng thái

- `docs/kehoach/TASKS.md`: checklist + `→ Bằng chứng:` ngay dưới task.
- `SESSION.md`: quyết định, số liệu, blocker, việc còn lại.
- `docs/api.md`: endpoint/response mới. `README.md`: lệnh/URL mới.
- `KE-HOACH-TONG-THE.md`: chỉ sửa khi có quyết định kiến trúc; nếu sửa, chạy `scripts/check_refs.py` (0 lỗi).
- Báo cáo phase: `docs/kehoach/PHASE<N>-REPORT.md`.

## 8. Git

- Message: `feat(phaseN): x.y <mô tả>`, `fix(phaseN): ...`, `docs: ...`, `test(phaseN): ...`.
- Một bước = một commit. Push fail retry tối đa 2 lần rồi báo lỗi.
- Trước commit: `git add -A`, kiểm tra `git status` không có file rác.

## 9. PowerShell / tiếng Việt

- File `.ps1`: UTF-8 **có BOM**, tiếng Việt đủ dấu.
- Mở đầu: `#requires -Version 5.1`, `Set-StrictMode -Version Latest`, `$ErrorActionPreference = 'Stop'`.
- Thêm `chcp 65001` + `[Console]::OutputEncoding = UTF8`; biến trước `:` dùng `${i}`.
- Sửa file tiếng Việt bằng Python UTF-8/UTF-8-SIG, tránh `Get-Content | Set-Content` gây mojibake.

## 10. Lệnh nhanh

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec -e RUN_INTEGRATION=1 backend pytest -q
.\.venv\Scripts\ruff.exe check backend
cd frontend && npm run build && npm run test:e2e
python scripts/check_refs.py
```

## 11. Definition of Done

Code chạy; test liên quan pass; docs cập nhật; không secret; không regression dữ liệu;
có bằng chứng (log/số đo/screenshot); commit sạch; báo cáo 1–3 dòng kèm hash.
