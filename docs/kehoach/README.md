# KẾ HOẠCH THỰC HIỆN — BINANCE COPY TRADER SCREENER & RISK ANALYTICS

> Phiên bản: **v2.1** — bản sửa theo hướng **phễu lọc tiềm năng**  
> Ngày lập: **06/11/2026**  
> Trạng thái: **Kế hoạch thực thi MVP**  
> Tài liệu gốc: `Kế hoạch v1.docx`, `các chỉ số cho copy trade.docx`  
> Kết quả kiểm chứng dữ liệu: xem `02-data-contract-binance.md`

---

## 1. Tóm tắt điều hành

Dự án được tái định vị từ “AI Copy Trading Intelligence” thành:

> **Binance Copy Trader Screener & Risk Analytics**  
> Công cụ sàng lọc, đánh giá và theo dõi rủi ro Lead Trader trên Binance Futures Copy Trading.  
> **Không giao dịch thật. Không auto-copy. Không realtime.**

### Thay đổi cốt lõi so với v2.0

**Không deep-fetch toàn bộ 13.004 trader.**  
Chỉ deep-fetch những trader vượt qua **phễu tiềm năng**:

1. Có giao dịch trong 7 ngày gần nhất.
2. Hoạt động đủ lâu (≥ 30 ngày; qualified ≥ 90; high potential ≥ 180).
3. Có lợi nhuận dương (ROI > 0, PnL > 0).
4. Có mẫu giao dịch tối thiểu (total orders ≥ 20/50/100 theo tầng).
5. WinRate và MDD trong ngưỡng chấp nhận.
6. Còn slot copy (`currentCopyCount < maxCopyCount`).
7. AUM tối thiểu (1k/5k/10k/20k theo preset).

### Phễu dự kiến (dữ liệu 06/11/2026)

| Tầng | Điều kiện chính | PUBLIC | SIGNAL | Tổng | Deep fetch |
|---|---|---:|---:|---:|---|
| **Universe** | Quét list PUBLIC + SIGNAL | 8.976 | 2.154 | **11.130** | Không |
| **C — Watch** | ≥30 ngày, ROI>0, PnL>0, WR≥40, MDD≤40, AUM≥5k, còn slot, có trade 7D | 460 | 57 | **517** | Performance; detail nếu nổi bật |
| **B — Qualified** | ≥90 ngày, ROI≥10, WR≥45, MDD≤30, AUM≥10k, Sharpe≥0.5/null, ≥50 orders | 103 | 10 | **113** | Detail + positions + transfers |
| **A — High** | ≥180 ngày, ROI≥20, WR≥50, MDD≤20, AUM≥20k, Sharpe≥1, ≥100 orders | 13 | 0 | **13** | Full trades + AI |

> Đây là **upper bound** trước khi lọc `totalOrder` và `status=ACTIVE`.  
> Sau performance/detail, shortlist thực tế sẽ nhỏ hơn.  
> **B và A là subset của C**, không cộng dồn. Union deep-fetch = **517**.  
> `PRIVATE` (1.874 trader) **không quét mặc định** vì không mở copy công khai.

### Ý nghĩa vận hành

| Hoạt động | v2.0 | v2.1 |
|---|---|---|
| List scan | 13.004 | **11.130** (PUBLIC + SIGNAL, chỉ 90D) |
| Deep fetch performance | 13.004 | **~517** |
| Deep fetch detail/positions/transfers | 13.004 | **~113–313** |
| Full trade history | 13.004 | **~13–50** |
| Thời gian crawl 1 chu kỳ | 45–60 phút | **5–10 phút** |
| Dung lượng raw | Rất lớn | Giảm 90%+ |

---

## 2. Phạm vi MVP

### Có trong MVP

| # | Màn hình / Module | Mục tiêu |
|---|---|---|
| 1 | **Screener** | Lọc theo tiềm năng, rủi ro, hiệu suất; hiển thị tier |
| 2 | **Trader Detail** | Hồ sơ, 10 chỉ số cốt lõi, score breakdown, risk flags, data confidence |
| 3 | **Compare** | So sánh 2–4 trader, correlation matrix |
| 4 | **Settings & Data Health** | Cấu hình phễu, scoring, risk, AI; trạng thái collector |
| 5 | **AI Report** (phase sau) | Giải thích trader, có evidence, không sửa điểm |
| 6 | **Collector** | Quét list 60 phút; deep fetch shortlist theo tier |
| 7 | **Quant / Risk / Scoring** | Tính chỉ số, risk events, score có version |
| 8 | **Ranking** | 3 bảng: Overall, Low Risk, Consistency |

### Không có trong MVP

| Chức năng | Lý do |
|---|---|
| Deep fetch toàn bộ trader | Tốn thời gian, phần lớn không có tiềm năng |
| Auto copy / đặt lệnh Binance | Rủi ro pháp lý và tài chính |
| Realtime WebSocket | Không cần; chu kỳ 60 phút |
| Paper Copy | Không đủ dữ liệu để mô phỏng trung thực |
| Per-copier analytics | Không có API public |
| Open positions | Không có API public |
| Funding drag chính xác | Không có funding trong trade-history |
| Copy fill rate / slippage | Cần tài khoản copier |
| Telegram / mobile app | Giữ hệ thống gọn |
| 6 bảng ranking | Giảm còn 3 bảng có ý nghĩa |
| Strategy labels tự động | Chỉ làm heuristic “suspected” |

---

## 3. Quyết định khóa

1. Một website, không mobile app.
2. Một backend FastAPI, modular monolith, không microservices.
3. Một PostgreSQL, không Redis/Kafka/Celery.
4. **List scan 60 phút/lần; deep fetch shortlist theo tier.**
5. AI chỉ giải thích và phản biện; **không được sửa điểm**.
6. Mọi cấu hình nghiệp vụ chỉnh trên web, có **version** và **audit log**.
7. Không Telegram, không thông báo ngoài web.
8. Không giao dịch thật, không auto-copy.
9. **Published metrics trước, derived metrics sau.**
10. **Không hiển thị chỉ số không có dữ liệu.** Thà thiếu còn hơn sai.
11. `null` không bao giờ được coi là `0` trong scoring.
12. Mọi chỉ số phải có **nguồn, cửa sổ thời gian, định nghĩa, độ tin cậy**.
13. **Không deep-fetch trader không có tiềm năng.**
14. **Trader <30 ngày bị loại khỏi phễu chính.** Có thể hiển thị trong “Radar” (chỉ list record, không deep fetch, không xếp hạng) để theo dõi sau.

---

## 4. Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend: React + Vite + TypeScript + Tailwind + ECharts   │
│  Screener · Trader Detail · Compare · Settings/Data Health  │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST /api/v1
┌──────────────────────────▼──────────────────────────────────┐
│  Backend: Python + FastAPI (Modular Monolith)               │
│  API · Collector · Quant · Risk · Scoring · Ranking · AI    │
└───────────────┬──────────────────────────────┬──────────────┘
                │                              │
        ┌───────▼────────┐            ┌────────▼────────┐
        │ PostgreSQL     │            │ Binance BAPI    │
        │ Raw + Derived  │            │ (internal API)  │
        └───────┬────────┘            └─────────────────┘
                │
        ┌───────▼────────┐
        │ JSONL Archive  │  append-only, resume được
        └────────────────┘
```

Chi tiết: `01-pham-vi-va-kien-truc.md`

---

## 5. Cấu trúc tài liệu

| File | Nội dung | Đối tượng đọc |
|---|---|---|
| `README.md` | Tóm tắt, phạm vi, quyết định khóa, phễu | Tất cả |
| `01-pham-vi-va-kien-truc.md` | Kiến trúc, module, database, API | Backend / DevOps |
| `02-data-contract-binance.md` | Endpoint, field, giới hạn, data quality, phễu | Backend / Data |
| `03-bo-chi-so-va-scoring.md` | Định nghĩa chỉ số, công thức, scoring, risk rules | Product / Quant |
| `04-lo-trinh-va-nghiem-thu.md` | 7 phase, thời lượng, acceptance criteria | PM / Dev |
| `05-ui-ux-va-trang.md` | Thiết kế 4 màn hình, empty state, tooltip | Frontend / Design |
| `06-kiem-thu-van-hanh-bao-mat.md` | Test plan, golden dataset, deploy, backup, security | QA / DevOps |
| `07-rui-ro-phap-ly-va-du-phong.md` | Rủi ro BAPI/ToS, phương án dự phòng | Founder / PM |
| `08-nhat-ky-quyet-dinh.md` | Tóm tắt phân tích, quyết định, câu hỏi mở | Tất cả |
| `data-availability-matrix.csv` | Ma trận chỉ số ↔ nguồn dữ liệu | Backend / Data |
| `TASKS.md` | Checklist công việc theo phase | Dev |

---

## 6. Tiêu chí thành công của MVP

### Kỹ thuật

- [ ] Quét list **≥ 99%** trong 11.130 trader PUBLIC + SIGNAL.
- [ ] Pre-filter tạo shortlist **≤ 700 trader**.
- [ ] Deep fetch detail/positions cho **≤ 700 trader**.
- [ ] Full trade history cho **≤ 150 trader**.
- [ ] 1 chu kỳ list scan + deep fetch shortlist hoàn tất **< 15 phút**.
- [ ] Không mất snapshot khi restart.
- [ ] API danh sách shortlist p95 < 1 giây.
- [ ] 100% chỉ số hiển thị có nguồn và cửa sổ thời gian.
- [ ] 0 chỉ số `null` bị hiển thị như `0`.

### Sản phẩm

- [ ] Người dùng lọc được trader theo tier, ROI, MDD, Sharpe, WinRate, Runtime, CopyAum, Leverage trong < 30 giây.
- [ ] Mỗi trader có score breakdown giải thích được vì sao điểm cao/thấp.
- [ ] Có cảnh báo rõ cho: MDD cao, leverage cao, position ROI gần -100%, dữ liệu cũ, mẫu quá ít.
- [ ] Không có trader rủi ro cao đứng đầu chỉ vì ROI lớn.
- [ ] Người dùng hiểu được “vì sao trader này bị loại khỏi shortlist”.

### Chất lượng dữ liệu

- [ ] Chênh lệch MDD tự tính (nếu có) so với MDD công bố ≤ 1% sau khi điều chỉnh dòng tiền.
- [ ] Chênh lệch WinRate công bố và position-level được ghi rõ định nghĩa.
- [ ] Tỷ lệ snapshot lỗi/thiếu < 1%/ngày.
- [ ] Data freshness hiển thị trên mọi màn hình.
- [ ] Pre-filter không loại nhầm trader có `totalOrder` tốt nhưng list field xấu (kiểm tra bằng audit sample).

---

## 7. Ước lượng tổng thể

| Giai đoạn | Thời lượng | Đầu ra |
|---|---|---|
| Phase 0 — Data spike & pre-filter spec | 3–5 ngày | Data contract + tiêu chí phễu + quyết định go/no-go |
| Phase 1 — Foundation + vertical slice | 5–7 ngày | 1 trader chạy end-to-end |
| Phase 2 — Collector 2 tầng + raw storage | 4–6 ngày | List scan 11k + shortlist 517 |
| Phase 3 — Quant + Scoring + Screener | 7–9 ngày | Screener dùng được, có tier |
| Phase 4 — Detail + Compare + Risk | 5–7 ngày | Trang chi tiết, so sánh, risk monitor |
| Phase 5 — AI + Settings + Hardening | 5–7 ngày | AI report, cấu hình web |
| Phase 6 — Testing + Deploy + Beta | 4–6 ngày | MVP chạy VPS |
| **Tổng** | **33–47 ngày** | **7–9 tuần** (1 dev full-time, có buffer) |

Nếu làm part-time: nhân 2. Nếu Phase 0 thất bại: cộng 1–2 tuần cho phương án dự phòng.

Chi tiết: `04-lo-trinh-va-nghiem-thu.md`

---

## 8. Nguyên tắc ra quyết định khi bí

1. **Dữ liệu này có thật, lấy được, đáng tin không?**
   Nếu không → không làm, hoặc ghi rõ “estimated”.
2. **Trader này có tiềm năng thật không?**
   Nếu không đủ dữ liệu hoặc không có tín hiệu → không deep fetch.
3. **Nếu chỉ số này sai, hậu quả là gì?**
   Nếu người dùng có thể mất tiền vì hiểu sai → phải có tooltip, disclaimer, data confidence.

---

## 9. Việc cần làm ngay (tuần này)

1. Chốt **tiêu chí phễu** trong `02-data-contract-binance.md`.
2. Chạy Phase 0 trên **20 trader mỗi tier** (C/B/A), không phải 20 trader ngẫu nhiên.
3. Xác nhận lại các con số 460 / 103 / 13 trên dữ liệu hiện tại.
4. Chốt 20 chỉ số MVP trong `03-bo-chi-so-va-scoring.md`.
5. Dựng skeleton repo theo `01-pham-vi-va-kien-truc.md`.
6. Tạo golden dataset gồm cả trader **bị loại** và trader **tiềm năng**.
7. Chưa viết UI chi tiết trước khi Phase 0 xong.

---

## 10. Disclaimer

Sản phẩm này là công cụ **phân tích dữ liệu công khai**, không phải tư vấn đầu tư, không đảm bảo lợi nhuận, không thực hiện giao dịch. Dữ liệu lấy từ BAPI nội bộ của Binance, có thể thay đổi hoặc bị chặn. Người dùng chịu trách nhiệm với quyết định đầu tư của mình.
