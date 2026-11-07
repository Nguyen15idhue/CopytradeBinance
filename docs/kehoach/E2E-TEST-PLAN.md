# E2E TEST PLAN — Playwright (Phase 6)

> Mục tiêu: chứng minh hệ thống hoạt động với **các use case thực tế** của admin/viewer,
> trên dữ liệu thật đã thu thập, ở desktop + mobile, có kiểm tra lỗi mạng và theme.

## 1. Nguyên tắc

- Test trên **stack đang chạy** (`docker compose up`), không mock toàn bộ API.
- Chỉ mock khi cần kiểm tra lỗi: 401/403/404/409/429/500, timeout, empty.
- Không xóa/sửa dữ liệu trader thật. Chỉ tạo/xóa **saved view** và user test.
- Mỗi test độc lập, tự lấy id qua API; không hardcode id trader (trừ fixture 404).
- Mọi test phải pass **3 lần liên tiếp** mới tính ổn định.
- Không commit artifact (trace/video/report).

## 2. Stack & cấu hình

| Thành phần | Chọn |
|---|---|
| Runner | `@playwright/test` (thay script `e2e.mjs` hiện tại) |
| Browser | Chromium (system Chrome qua `channel` hoặc `executablePath`) |
| Projects | `desktop-1440`, `desktop-1280`, `mobile-390` |
| Base URL | `E2E_BASE_URL` (mặc định `http://localhost:8090`) |
| Auth | `storageState` cho admin và viewer, tạo 1 lần trong global setup |
| Retries | 1 (local), 0 khi chạy gate 3 lần |
| Artifact | trace on-first-retry, video retain-on-failure, screenshot only-on-failure |
| Timeout | test 30s, expect 5s, navigation 15s |
| Report | HTML + JUnit XML (CI), lưu ngoài repo |
| Tag | `@smoke` (PR), `@full` (nightly/gate) |

## 3. Dữ liệu test

- Lấy trader chất lượng cao: `GET /api/v1/traders?page_size=1` (sort score).
- Lấy trader excluded: `GET /api/v1/traders?tier=excluded&page_size=1`.
- Lấy 2–4 id cho compare từ danh sách trên.
- Saved view dùng tên `e2e-<timestamp>`, xóa trong `afterEach`.
- Khi cần empty state: filter `q=__khong_ton_tai__`.
- Khi cần 404: id `khong-ton-tai`.

## 4. Ma trận use case

### 4.1. Auth & phiên (P0)

| ID | Use case | Role | Kỳ vọng |
|---|---|---|---|
| A01 | Login đúng | admin | Vào `/`, thấy email + role |
| A02 | Login sai | — | Hiện lỗi, không lưu token, vẫn ở `/login` |
| A03 | Rate limit login lần 6 | — | Hiện thông báo 429, không crash |
| A04 | Logout | admin | Về `/login`, token bị xóa, back không vào được `/` |
| A05 | Deep link khi chưa login | — | `/screener` → redirect `/login` |
| A06 | Token hết hạn/401 | admin | API 401 → xóa session, UI yêu cầu đăng nhập lại |
| A07 | Viewer login | viewer | Không thấy hành động admin; API admin trả 403 |
| A08 | Refresh token rotate | admin | Refresh cũ bị 401, cặp mới dùng được (API-level) |

### 4.2. Screener (P0)

| ID | Use case | Kỳ vọng |
|---|---|---|
| S01 | Tải mặc định | Bảng có dòng, sort score desc, count khớp API |
| S02 | Search nickname có kết quả | Chỉ dòng khớp |
| S03 | Search không tồn tại | Empty state + gợi ý bỏ filter |
| S04 | Filter từng tier (High/Qualified/Watch/Excluded) | Đúng tier, count đổi |
| S05 | Include excluded | Hiện excluded + `filter_reasons` |
| S06 | ROI min/max | Mọi dòng thoả |
| S07 | MDD ≤ 15 | Mọi dòng mdd ≤ 15 |
| S08 | Sharpe/WinRate/Runtime/Orders/Leverage | Mọi dòng thoả |
| S09 | Sort từng cột asc/desc | Thứ tự đúng |
| S10 | Phân trang | Trang 2 khác trang 1, tổng trang đúng |
| S11 | Saved view: lưu → reload → áp dụng | Filter khôi phục đúng |
| S12 | Saved view: xóa | Biến mất khỏi danh sách |
| S13 | Export CSV | Tải file, header đúng, số dòng = page size |
| S14 | Breakdown drawer | Mở/đóng, có 7 nhóm, có missing/hard flags |
| S15 | Reset filter | Về mặc định |
| S16 | Click trader | Sang `/traders/:id` |

### 4.3. Trader Detail (P0)

| ID | Use case | Kỳ vọng |
|---|---|---|
| D01 | Trader qualified | Header + 10 card + score/confidence/risk |
| D02 | Tooltip nguồn | ≥ 10 phần tử có title chứa “nguồn” |
| D03 | Chart ROI/drawdown/PnL | Render SVG/canvas, không console error |
| D04 | Drawdown disclaimer | Có chữ “estimated” |
| D05 | Score breakdown | 7 nhóm, tổng contribution hiển thị |
| D06 | Risk flags | Chip + mở được Risk Monitor |
| D07 | Positions/trades/transfers | Bảng/list hoặc empty state rõ ràng |
| D08 | Trader excluded | Banner + reasons; null hiển thị N/A |
| D09 | Trader 404 | Panel lỗi, không trắng trang |
| D10 | API 500 khi tải | Panel lỗi + nút quay lại |
| D11 | Copy AUM = 0 | Ghi “Không có copier”, không N/A |

### 4.4. Compare (P1)

| ID | Use case | Kỳ vọng |
|---|---|---|
| C01 | Chọn 2 trader | Bảng + chart + correlation |
| C02 | Chọn 4 trader | Không vỡ layout 1280/1440 |
| C03 | Cố chọn thứ 5 | Bị chặn, hiện “tối đa 4” |
| C04 | Deep link `?ids=` | Load đúng danh sách |
| C05 | `?ids=` 1 hoặc >4 | Thông báo cần 2–4 |
| C06 | Xóa chip | URL + dữ liệu cập nhật |
| C07 | Correlation | Có “estimated”, sample_days |
| C08 | Id không tồn tại | Không crash, báo thiếu dữ liệu |

### 4.5. Risk Monitor (P1)

| ID | Use case | Kỳ vọng |
|---|---|---|
| R01 | Summary | Tổng + đếm severity khớp API |
| R02 | Filter severity | Chỉ event đúng severity |
| R03 | Filter trader (từ Detail) | Prefill + đúng trader |
| R04 | Mở evidence | JSON evidence hiển thị |
| R05 | Pagination | Chuyển trang đúng |
| R06 | Filter không có kết quả | Empty state |
| R07 | Open positions | Không hiển thị giả; có ghi chú |

### 4.6. Ranking + Help (Phase 5 — P1)

| ID | Use case | Kỳ vọng |
|---|---|---|
| K01 | 3 tab ranking | Overall/Low Risk/Consistency render |
| K02 | Metadata snapshot | Thời điểm + config version |
| K03 | Click trader | Sang Detail |
| K04 | Chưa có snapshot | Empty state |
| H01 | Mở `/help` | Đủ 8 mục, mục lục hoạt động |
| H02 | Search nội bộ | Lọc đúng mục |
| H03 | Banner “Mới bắt đầu?” | Dismiss, reload không hiện lại |
| H04 | Print/PDF | CSS in ẩn header/footer |

### 4.7. Theme, responsive, accessibility (P1)

| ID | Use case | Kỳ vọng |
|---|---|---|
| T01 | Sáng → reload | Giữ light, nền sáng |
| T02 | Tối → reload | Giữ dark |
| T03 | Hệ thống + emulateMedia | Theo OS |
| T04 | Chart đổi màu | Không mất đường/không vô hình |
| T05 | Mobile 390 | Không tràn ngang, sidebar xử lý đúng (drawer/hidden) |
| T06 | Keyboard tab | Đến được input, toggle, link; focus thấy được |
| T07 | Zoom 200% | Không che nút chính |

### 4.8. Lỗi mạng & dữ liệu (P1)

| ID | Use case | Kỳ vọng |
|---|---|---|
| N01 | 401 toàn cục | Về login, không loop |
| N02 | 500 list | Error state, không trắng |
| N03 | Timeout list | Error state + retry |
| N04 | 429 login | Thông báo thân thiện |
| N05 | Empty DB | Screener/Data Health empty rõ ràng |
| N06 | Null metric | N/A, không 0/NaN |
| N07 | Dữ liệu stale | Cảnh báo freshness nếu có |

### 4.9. Cross-cutting (P0)

| ID | Kiểm tra |
|---|---|
| X01 | Không console error trên mọi trang |
| X02 | Không chuỗi `undefined`/`NaN`/`null` hiển thị |
| X03 | Không trả API key/secret trong response/localStorage |
| X04 | Text tiếng Việt có dấu hiển thị đúng |
| X05 | Mọi trang có loading/empty/error state |
| X06 | Không request 4xx ngoài dự kiến trong luồng happy path |

## 5. Mock & error injection

- `page.route('**/api/v1/traders*', route => route.fulfill({status: 500}))`.
- 401: override token bằng chuỗi hỏng trong `localStorage`.
- 429: gọi login sai 6 lần (dùng user test) hoặc mock response.
- Empty: filter không tồn tại; hoặc mock `data.items = []`.
- Timeout: `route.abort('timedout')`.

## 6. CI & báo cáo

```bash
# Smoke (PR)
npx playwright test --grep @smoke

# Full (nightly/gate)
npx playwright test --grep @full --repeat-each=1
npx playwright test --grep @full --repeat-each=3   # kiểm tra flaky
```

- Gate: **100% P0 pass**, ≥ 95% P1 pass, 0 flaky sau 3 lần, không console error.
- Lưu `playwright-report/`, `test-results/` ngoài repo; upload artifact CI.
- Mỗi lần fail: gắn trace + video + request log vào báo cáo.

## 7. Known gaps cần xử lý trước khi E2E full pass

| # | Gap | Ảnh hưởng test |
|---|---|---|
| G1 | Sidebar mobile chưa có drawer | T05 phải chốt hành vi (ẩn + menu) |
| G2 | Filter Screener chưa lưu vào URL | Không share được view qua link |
| G3 | Chưa có silent refresh token ở UI | A06 chỉ test được mức “401 → login” |
| G4 | Chưa có banner stale > 150 phút toàn trang | N07 tạm kiểm ở Data Health |
| G5 | Ranking/Help chưa tồn tại | K01–K04/H01–H04 chờ Phase 5 |
| G6 | Chưa có nút admin trên UI | A07 chỉ kiểm qua API/ẩn nav |

## 8. Lệnh chạy hiện tại (trước khi chuyển runner)

```bash
cd frontend
npm run test:e2e   # script e2e.mjs tạm thời
```

Phase 6 sẽ thay bằng `@playwright/test` với cấu trúc `frontend/e2e/*.spec.ts`.
