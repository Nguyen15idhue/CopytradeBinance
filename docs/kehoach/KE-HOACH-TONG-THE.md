# KẾ HOẠCH TỔNG THỂ A→Z
## Binance Copy Trader Screener & Risk Analytics

> **Phiên bản:** v3.1 — Consolidated Master Plan (tách checklist sang `TASKS.md`)  
> **Ngày lập:** 06/11/2026  
> **Trạng thái:** Phase 0 gần hoàn tất (đã có bằng chứng chạy thật); Phase 1–6 chưa bắt đầu.  
> **Nguồn sự thật:**
> - Hành vi code: `phase0/*.py`
> - Số liệu vận hành: `phase0/data/*`
> - Thiết kế chi tiết: `docs/kehoach/01` → `08`
>
> **Quy ước trạng thái:**
> - `[x]` đã chạy, có artifact/bằng chứng
> - `[~]` có code/dữ liệu một phần, chưa đạt gate
> - `[ ]` chưa làm
> - `[!]` đang bị chặn hoặc cần quyết định
>
> **Cách đọc:** Nếu chỉ đọc một file, đọc file này. Các file `01`–`08` là tài liệu tham chiếu chi tiết. `TASKS.md` là checklist thực thi duy nhất cho Phase 1–6; trạng thái tổng hợp nằm ở mục 1.3 và 2.2.

---

## 0. MỤC LỤC

1. Tóm tắt điều hành
2. Hiện trạng mã nguồn & artifact
3. Quyết định khóa
4. Phạm vi MVP
5. Kiến trúc hệ thống
6. Data contract Binance BAPI
7. Phễu lọc & tiering
8. Bộ chỉ số
9. Scoring, risk rules & ranking
10. Database & storage
11. API v1
12. Collector design
13. UI/UX & màn hình
14. Kiểm thử & QA
15. Deploy, vận hành & bảo mật
16. Rủi ro, pháp lý & phương án dự phòng
17. Lộ trình & checklist công việc
18. Backlog v1.1
19. Việc không làm (non-goals)
20. Câu hỏi mở & quyết định cần chốt
21. Việc cần làm ngay
22. Phụ lục

---

## 1. TÓM TẮT ĐIỀU HÀNH

### 1.1. Sản phẩm là gì

> **Binance Copy Trader Screener & Risk Analytics**  
> Công cụ sàng lọc, đánh giá và theo dõi rủi ro **Lead Trader** trên Binance Futures Copy Trading.

**Không phải:**
- Không giao dịch thật.
- Không auto-copy.
- Không realtime.
- Không tư vấn đầu tư cá nhân hóa.
- Không bán raw data.

### 1.2. Thay đổi cốt lõi so với kế hoạch v1

Không deep-fetch toàn bộ ~13.000 trader. Chỉ deep-fetch trader vượt qua **phễu tiềm năng**:

1. Có giao dịch trong 7 ngày gần nhất.
2. Hoạt động đủ lâu (≥ 30 ngày; Qualified ≥ 90; High ≥ 180).
3. ROI > 0, PnL > 0.
4. Đủ mẫu giao dịch (≥ 20/50/100 order theo tầng).
5. WinRate và MDD trong ngưỡng chấp nhận.
6. Còn slot copy (`currentCopyCount < maxCopyCount`).
7. AUM tối thiểu theo preset (1k/5k/10k).

**Hệ quả vận hành:**

| Hoạt động | Kế hoạch cũ | Kế hoạch hiện tại |
|---|---:|---:|
| List scan | 13.004 | **11.124** (PUBLIC + SIGNAL, chỉ 90D) |
| Deep fetch performance | 13.004 | **~515** |
| Deep fetch detail/positions/transfers | 13.004 | **~109–313** |
| Full trade history | 13.004 | **~13–50** |
| Thời gian crawl 1 chu kỳ | 45–60 phút | **5–15 phút** (mục tiêu) |
| Dung lượng raw | Rất lớn | Giảm 90%+ |

### 1.3. Trạng thái hiện tại — snapshot 06/11/2026

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Phase 0 — Data spike | `[~]` gần xong | `phase0/data/scan_summary.json`, `deep_fetch_summary.json`, `audit_summary.json` |
| Phase 1 — Backend/Frontend foundation | `[ ]` chưa bắt đầu | Chưa có `backend/`, `frontend/`, `docker-compose.yml` |
| Phase 2 — Collector | `[ ]` chưa bắt đầu | Mới có script Phase 0, chưa có adapter production |
| Phase 3 — Quant/Scoring/Screener | `[ ]` chưa bắt đầu | Chưa có backend API/UI |
| Phase 4 — Detail/Compare/Risk | `[ ]` chưa bắt đầu | — |
| Phase 5 — AI/Settings/Hardening | `[ ]` chưa bắt đầu | — |
| Phase 6 — Testing/Deploy/Beta | `[ ]` chưa bắt đầu | — |

### 1.4. Con số cốt lõi từ lần chạy thật

**Universe 90D — 06/11/2026 16:34Z**

| Chỉ số | PUBLIC | SIGNAL | Tổng |
|---|---:|---:|---:|
| Quét được | 8.970 | 2.154 | **11.124** |
| Coverage | 100% | 100% | **100%** |
| Số trang | 299 | 72 | **371** |
| Thời gian scan | 60,5s | 14,45s | **78,03s** |
| Watch (C, gồm B/A) | 457 | 58 | **515** |
| Watch-only (C) | 358 | 48 | **406** |
| Qualified-only (B) | 86 | 10 | **96** |
| High-only (A) | 13 | 0 | **13** |
| Qualified incl. High (B+A) | 99 | 10 | **109** |
| Excluded | 8.513 | 2.096 | **10.609** |
| Union deep-fetch | 457 | 58 | **515** |

**Sample & audit**

| Hạng mục | Kết quả |
|---|---|
| Sample deep fetch | **63 trader**: A=13, B=20, C=20, excluded=10 |
| Deep fetch | 63/63 thành công, **0 endpoint lỗi**, 153,34s, 6 workers |
| Audit excluded | 50/50 thành công, 19,91s |
| False negative theo gate `fn_watch_eligible` | **0/50 = 0%** (gate < 5% → PASS) |
| False negative literal `fn_prompt` | 12/50 = 24% (do loại có chủ đích bởi AUM/MDD/WinRate/runtime, không phải gate) |
| Activity proxy `traded_last_7d` | 60/63 khớp (95,24%), **0 false negative**, 3 false positive |
| Rate limit test | 32 request, **0 rate-limit**, 0 lỗi |
| Endpoint không khả dụng | 6/6 trả **404** |

### 1.5. Năm việc tiếp theo

1. **Đóng Phase 0**: cập nhật `SESSION.md`, chốt `mdd=None` và cohort `pre_score` (mục 20).
2. **Sửa lỗi tổng hợp reason**: `summarize_tiers()` đang đọc sai key `reasons`/`tier_reasons` khiến cột reason trong `tier_summary.csv` bằng 0.
3. **Dọn nền tảng tài liệu**: cập nhật `02-data-contract` (11.124/515/109), sửa `.gitignore` thành `phase0/data/`, init git, thêm `requirements.txt` + pytest cho tiering.
4. **Đo thời gian pipeline đầy đủ** trong Phase 2: performance ~515, detail/positions ~109–313, full trades ~13 (hiện chỉ có ngoại suy trong report).
5. **Dựng Phase 1**: repo backend/frontend, Docker Compose, PostgreSQL, Alembic, auth, seed 2 trader, vertical slice.

---

## 2. HIỆN TRẠNG MÃ NGUỒN & ARTIFACT

### 2.1. Cây thư mục thực tế

```
CopytradeBinance/
├── .gitignore                     # hiện chứa "phase0/" → ignore toàn bộ phase0
├── docs/
│   └── kehoach/
│       ├── README.md
│       ├── 01-pham-vi-va-kien-truc.md
│       ├── 02-data-contract-binance.md
│       ├── 03-bo-chi-so-va-scoring.md
│       ├── 04-lo-trinh-va-nghiem-thu.md
│       ├── 05-ui-ux-va-trang.md
│       ├── 06-kiem-thu-van-hanh-bao-mat.md
│       ├── 07-rui-ro-phap-ly-va-du-phong.md
│       ├── 08-nhat-ky-quyet-dinh.md
│       ├── data-availability-matrix.csv
│       ├── TASKS.md
│       ├── KE-HOACH-TONG-THE.md   # file này
│       ├── Kế hoạch v1.docx
│       └── các chỉ số cho copy trade.docx
│
└── phase0/
    ├── common.py                  # helper: JSON/CSV/JSONL, logging
    ├── fetch.py                   # BAPI client + smoke test + probe
    ├── tiering.py                 # pre-filter, tier, pre_score (pure functions)
    ├── scan_universe.py           # quét 90D PUBLIC + SIGNAL
    ├── sample.py                  # chọn 63 trader stratified
    ├── deep_fetch.py              # detail + performance 4 windows + positions + transfers + trade page 1
    ├── audit_excluded.py          # audit 50 excluded, đo false negative
    ├── activity_check.py          # so proxy traded_last_7d với lastTradeTime
    ├── rate_limit_test.py         # đo concurrency 1/5/10
    ├── indicator_checks.py        # kiểm chứng 7 nhóm chỉ số (MDD/WinRate/Sharpe/AUM...)
    ├── recompute_summary.py       # tính lại tier summary từ JSONL
    ├── PHASE0_REPORT.md           # báo cáo go/no-go + số đo + artifact
    └── data/
        ├── universe_90d.jsonl     # 11.124 dòng, nguồn chính
        ├── universe_tiers.csv
        ├── tier_summary.csv
        ├── scan_summary.json
        ├── sample_manifest.csv / .json
        ├── deep_fetch_status.csv
        ├── deep_fetch_summary.json
        ├── audit_excluded.csv
        ├── audit_summary.json
        ├── activity_check.csv / _summary.json
        ├── rate_limit_test.csv / _summary.json
        ├── indicator_quality.csv / _summary.json
        ├── smoke_summary.json
        ├── unavailable_probe.json
        ├── fetch_log.csv
        └── raw/
            ├── smoke/             # raw 6 endpoint + probes
            ├── A/ B/ C/ excluded/ # 63 bundle
            └── audit/             # 50 bundle detail + performance 90D
```

### 2.2. Trạng thái phase

| Phase | Trạng thái | Ghi chú |
|---|---|---|
| 0 — Data spike & pre-filter | `[~]` ~95% | Đã có report + kiểm chứng; còn bug reason, chốt `mdd=None`/cohort, `.gitignore`/git |
| 1 — Foundation + vertical slice | `[ ]` 0% | Chưa có backend/frontend |
| 2 — Collector 2 tầng + raw storage | `[ ]` 0% | Phase 0 scripts chưa phải production collector |
| 3 — Quant + Scoring + Screener | `[ ]` 0% | — |
| 4 — Detail + Compare + Risk | `[ ]` 0% | — |
| 5 — AI + Settings + Hardening | `[ ]` 0% | — |
| 6 — Testing + Deploy + Beta | `[ ]` 0% | — |

### 2.3. Script & artifact map

| Script | Mục đích | Input | Output chính | Trạng thái |
|---|---|---|---|---|
| `fetch.py smoke` | Kiểm chứng 6 endpoint, page size, base URL | — | `smoke_summary.json`, `raw/smoke/*` | `[x]` |
| `fetch.py probe` | Ghi nhận endpoint không khả dụng | — | `unavailable_probe.json` | `[x]` |
| `scan_universe.py` | Quét universe 90D + pre-filter + pre_score | BAPI | `universe_90d.jsonl`, `tier_summary.csv` | `[x]` |
| `tiering.py` | Logic tier/pre_score thuần | list row | tier/reasons/pre_score | `[x]` |
| `sample.py` | Chọn mẫu stratified 63 trader | `universe_90d.jsonl` | `sample_manifest.csv` | `[x]` |
| `deep_fetch.py` | Deep fetch 63 trader | `sample_manifest.csv` | `raw/{tier}/{id}/*`, `deep_fetch_status.csv` | `[x]` |
| `audit_excluded.py` | Audit 50 excluded | `universe_90d.jsonl` | `audit_excluded.csv`, `audit_summary.json` | `[x]` |
| `activity_check.py` | So proxy hoạt động 7D | manifest + raw detail | `activity_check.csv` | `[x]` |
| `rate_limit_test.py` | Đo rate limit/concurrency | BAPI | `rate_limit_test.csv` | `[x]` |
| `indicator_checks.py` | Kiểm chứng MDD/WinRate/Sharpe/AUM/CopyAum/fee/endpoint | sample raw + universe | `indicator_quality.csv`, `_summary.json` | `[x]` |
| `recompute_summary.py` | Tính lại summary không gọi mạng | JSONL | `tier_summary.csv` | `[~]` có bug reason key |
| Báo cáo Phase 0 (`PHASE0_REPORT.md`) | Báo cáo go/no-go + số đo + artifact | tất cả output Phase 0 | tài liệu quyết định | `[x]` |

### 2.4. Những gì đã chốt từ dữ liệu thật

1. **`performance` dùng `BASE_P`**, không phải `BASE_F`. Gọi `BASE_F` trả 404.
2. **List page size = 30**. Truyền 100 vẫn trả 30.
3. **Trade page size = 200**. Truyền 500 vẫn trả 200.
4. **Position/transfer** dùng page size 50 (khuyến nghị), có thể phân trang đủ.
5. **Universe mặc định = PUBLIC + SIGNAL**. PRIVATE (1.874) không quét mặc định.
6. **`chartItems` luôn có 90 điểm** với 90D trên toàn bộ 11.124 trader.
7. **`chartItems` là ROI lũy kế**, bị pha loãng bởi nạp/rút → **không dùng tính MDD tuyệt đối**.
8. **`positionShow=false` không chặn `position-history`**: 30/63 trader có `positionShow=false` nhưng cả 30 đều có position history.
9. **Không có open positions, per-copier, funding, liquidation, copy fill/slippage** qua BAPI public.
10. **Trader mẫu `5296057151807357697` là SIGNAL**, runtime ~4 ngày, bị loại ở Stage 0 vì `runtime < 30`.
11. **`traded_last_7d` từ `chartItems` không bỏ sót trader đang trade** trên mẫu 63: 0 false negative, nhưng có 3 false positive (giữ lại trader đã ngừng trade).
12. **Pre-filter không loại nhầm trader đủ điều kiện** trên mẫu audit 50: `fn_watch_eligible = 0%`.
13. **Rate limit chưa xuất hiện** ở 32 request với concurrency 1/5/10, nhưng vẫn phải giữ backoff cho mã `11012005`.
14. **Tất cả 63 trader deep fetch đều `ACTIVE`, `isPaused=false`** tại thời điểm fetch.
15. **Deep fetch 63 trader chỉ mất 153s với 6 workers**, trung bình ~14,3s/trader cho 6 endpoint + 4 performance windows.

### 2.5. Sai lệch tài liệu ↔ code/dữ liệu cần sửa

| # | Vấn đề | Tài liệu cũ | Thực tế | Xử lý |
|---|---|---|---|---|
| 1 | Số universe | 11.130 (8.976 + 2.154) | **11.124 (8.970 + 2.154)** tại 16:34Z | Dùng số live; không hardcode |
| 2 | Watch | 517 (460 + 57) | **515 (457 + 58)** | Dùng số live; chênh do list động |
| 3 | Qualified | 113 (103 + 10) | **109 incl. High (99 + 10)** | Dùng số live |
| 4 | High | 13 | **13** | Khớp |
| 5 | Sample size | 70 (20 A) | **63** vì A chỉ có 13 | Gate Phase 0 đổi thành 63 bundle |
| 6 | `positionShow` trader mẫu | `false` | Raw hiện tại **`true`** | Cập nhật `02-data-contract` |
| 7 | Reason columns | Có phân bố | `tier_summary.csv` toàn **0** | Sửa bug key `reasons`/`tier_reasons` |
| 8 | `chart_items_len_90d` trong smoke | Kỳ vọng 90 | Summary ghi `null` dù raw có 90 | Sửa smoke validation |
| 9 | `TASKS.md` | Audit còn `[ ]` | Audit 50 đã chạy xong | Đã chuyển thành checklist thực thi; xem `TASKS.md` |
| 10 | `.gitignore` | Không rõ | Đang ignore **toàn bộ** `phase0/` | Đổi thành `phase0/data/` nếu muốn giữ script |
| 11 | `PHASE0_REPORT.md` / `SESSION.md` | Có trong kế hoạch | Cả hai đã có | Đối chiếu nội dung trước Phase 1 |
| 12 | Backend/Frontend | Có trong kế hoạch | Chưa có thư mục | Phase 1 |

### 2.6. Lỗi/gap kỹ thuật đã biết trong Phase 0

| ID | Mô tả | Ảnh hưởng | Đề xuất |
|---|---|---|---|
| B01 | `summarize_tiers()` đọc `row.get("reasons")`, nhưng row từ `scan_universe` dùng `tier_reasons` sau recompute | Cột reason trong summary = 0 | Đọc fallback `reasons` → `tier_reasons`; test lại |
| B02 | `evaluate_item()` chỉ loại MDD nếu `mdd is not None and mdd > 40` | Trader `mdd=null` có thể lọt Watch | Chốt: null MDD → excluded hay missing? |
| B03 | `pre_score` tính percentile trên combined PUBLIC+SIGNAL | Khác cohort riêng từng type | Chốt cohort; nếu cần, tính riêng rồi merge |
| B04 | `smoke_summary.validation.chart_items_len_90d = null` | Không ảnh hưởng dữ liệu, chỉ báo cáo | Đọc `list_PUBLIC_p1.json` để điền |
| B05 | `.gitignore` ignore cả `phase0/` | Script/evidence không được track nếu init git | Tách data khỏi code |
| B06 | Chưa có test tự động cho `tiering.py` | Rủi ro regression khi sửa ngưỡng | Thêm pytest cho tier/pre_score |
| B07 | Chưa có `requirements.txt` cho Phase 0 | Khó tái lập môi trường | Thêm `requests` + version |
| B08 | ~~Chưa có `PHASE0_REPORT.md`~~ | Đã có `phase0/PHASE0_REPORT.md` + `SESSION.md` | Đã xử lý |

---

## 3. QUYẾT ĐỊNH KHÓA

Các quyết định dưới đây là **bất biến trong MVP**, trừ khi có quyết định mới được ghi vào mục 20.

| ID | Quyết định | Lý do | Hệ quả |
|---|---|---|---|
| D01 | Tái định vị thành **Screener & Risk Analytics** | Không có dữ liệu cho auto-copy/paper copy trung thực | Bỏ auto-trade, paper copy |
| D02 | MVP còn **4 màn hình chính** + AI report | Giảm scope, tăng chất lượng | Screener, Detail, Compare, Settings/Data Health |
| D03 | **Bỏ Paper Copy** khỏi MVP | Mô phỏng tạo cảm giác chính xác giả | Đưa vào backlog v1.1 |
| D04 | **3 bảng ranking** | 6 bảng quá nhiều, dễ chase ROI | Overall, Low Risk, Consistency |
| D05 | **Published metrics trước, derived sau** | Published có ngay; derived cần thời gian | Không block launch |
| D06 | **MDD hiển thị = `performance.mdd`** | Published là định nghĩa chính thức; `chartItems` từng bị tính sai thành 88,67% | Không dùng MDD tự tính để xếp hạng; tự tính chỉ để audit |
| D07 | **Null ≠ 0** | Sharpe null 34,9%; zero rates cao | Renormalize + confidence |
| D08 | **Runtime là hard filter** | Trader 4 ngày lọt bảng 90D | Min 30 ngày |
| D09 | **AUM và Copy AUM tách biệt** | AUM 98% có thể là tiền lead | Hiển thị cả hai |
| D10 | **WinRate order và position tách biệt** | Định nghĩa khác nhau | Ghi rõ nhãn |
| D11 | **AI không sửa điểm** | Tránh hallucination ảnh hưởng ranking | AI chỉ giải thích + evidence |
| D12 | **Adapter pattern** | BAPI có thể đổi/block | Có CSV/Demo fallback |
| D13 | **Không realtime** | Không cần, giảm rủi ro | 60 phút/lần |
| D14 | **Không auto trading** | Rủi ro pháp lý/tài chính | Không lưu API key giao dịch |
| D15 | **Config có version + audit** | Đổi trọng số không được làm sai lịch sử | `scoring_config_versions` |
| D16 | **Timeline 7–9 tuần** | Thực tế hơn 29–47 ngày; phễu giảm crawl | Buffer 20% |
| D17 | **Phễu 3 tầng, không deep-fetch toàn bộ** | 10.600+ trader không có tiềm năng | List scan 11.124; deep fetch ~515; full trades ~13–50 |
| D18 | **Universe = PUBLIC + SIGNAL** | PRIVATE không mở copy công khai | PRIVATE chỉ bật khi nghiên cứu |
| D19 | **List scan chỉ 90D** | Các window khác lấy từ `/performance` | Tiết kiệm request |
| D20 | **`traded_last_7d` là proxy rẻ** | List không có `lastTradeTime` | Deep fetch phải xác nhận lại `lastTradeTime` |
| D21 | **B/A là upper bound** | List không có `totalOrder` | Chỉ chốt sau performance + detail |
| D22 | **Preset mặc định Balanced = 5.000 USDT** | Cân bằng nhiễu/coverage | Broad 1k, Strict 10k |
| D23 | **Deep fetch theo thứ tự A → B → C** | Ưu tiên trader tiềm năng nhất | Excluded chỉ audit |
| D24 | **Sample Phase 0 = 63 trader** | A chỉ có 13, không đủ 20 | Gate dùng 63 bundle |
| D25 | **`positionShow` không quyết định position-history** | 30/63 false nhưng vẫn có history | Luôn gọi position-history cho trader đủ điều kiện |
| D26 | **Không hardcode số lượng trader** | List thay đổi giữa các trang/ngày | Luôn tính live, lưu snapshot |
| D27 | **Phase 0 chỉ lấy trade page 1** | Giới hạn chi phí/scope | Full history chỉ Phase 2+ |
| D28 | **Không hiển thị open positions** | Không có endpoint | Ghi “N/A — Binance không cung cấp” |
| D29 | **Fee có thể âm (rebate)** | Dữ liệu thật cho thấy fee âm | Không coi là lỗi; hiển thị đúng dấu |
| D30 | **Mọi chỉ số phải có nguồn + cửa sổ + độ tin cậy** | Tránh hiểu sai | Tooltip + badge bắt buộc |

---

## 4. PHẠM VI MVP

### 4.1. Trong phạm vi

| # | Module/Màn hình | Mục tiêu |
|---|---|---|
| 1 | **Screener** | Lọc theo tiềm năng, rủi ro, hiệu suất; hiển thị tier |
| 2 | **Trader Detail** | Hồ sơ, 10 chỉ số cốt lõi, score breakdown, risk flags, data confidence |
| 3 | **Compare** | So sánh 2–4 trader, correlation matrix |
| 4 | **Settings & Data Health** | Cấu hình phễu, scoring, risk, AI; trạng thái collector |
| 5 | **AI Report** (phase 5) | Giải thích trader, có evidence, không sửa điểm |
| 6 | **Collector** | Quét list 60 phút; deep fetch shortlist theo tier |
| 7 | **Quant / Risk / Scoring** | Tính chỉ số, risk events, score có version |
| 8 | **Ranking** | 3 bảng: Overall, Low Risk, Consistency |

### 4.2. Ngoài phạm vi

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
| Bán raw data / dùng logo Binance như chứng nhận | Rủi ro pháp lý |

### 4.3. Người dùng & Jobs To Be Done

| Vai trò | Quyền | JTBD |
|---|---|---|
| **Admin** | Cấu hình, chạy collector, AI, scoring, user | “Tôi muốn hệ thống chạy đúng và có thể giải thích vì sao điểm thay đổi.” |
| **Viewer** | Đọc screener/detail/compare/ranking | “Tôi muốn tìm 5–20 trader đáng theo dõi trong < 30 giây và hiểu rủi ro.” |

### 4.4. Tiêu chí thành công MVP

**Kỹ thuật**
- [ ] Quét list ≥ 99% trong 11.124 trader PUBLIC + SIGNAL.
- [ ] Pre-filter tạo shortlist ≤ 700 trader.
- [ ] Deep fetch detail/positions cho ≤ 700 trader.
- [ ] Full trade history cho ≤ 150 trader.
- [ ] 1 chu kỳ list scan + deep fetch shortlist < 15 phút.
- [ ] Không mất snapshot khi restart.
- [ ] API danh sách shortlist p95 < 1 giây.
- [ ] 100% chỉ số hiển thị có nguồn và cửa sổ thời gian.
- [ ] 0 chỉ số `null` bị hiển thị như `0`.

**Sản phẩm**
- [ ] Người dùng lọc được trader theo tier, ROI, MDD, Sharpe, WinRate, Runtime, CopyAum, Leverage trong < 30 giây.
- [ ] Mỗi trader có score breakdown giải thích được vì sao điểm cao/thấp.
- [ ] Có cảnh báo rõ cho: MDD cao, leverage cao, position ROI gần -100%, dữ liệu cũ, mẫu quá ít.
- [ ] Không có trader rủi ro cao đứng đầu chỉ vì ROI lớn.
- [ ] Người dùng hiểu được “vì sao trader này bị loại khỏi shortlist”.

**Chất lượng dữ liệu**
- [ ] Chênh lệch MDD tự tính (nếu có) so với MDD công bố ≤ 1% sau khi điều chỉnh dòng tiền.
- [ ] Chênh lệch WinRate công bố và position-level được ghi rõ định nghĩa.
- [ ] Tỷ lệ snapshot lỗi/thiếu < 1%/ngày.
- [ ] Data freshness hiển thị trên mọi màn hình.
- [ ] Pre-filter không loại nhầm trader có `totalOrder` tốt nhưng list field xấu (audit sample).

---

## 5. KIẾN TRÚC HỆ THỐNG

### 5.1. Sơ đồ logic

```
┌──────────────────────────────────────────────────────────────┐
│                        NGƯỜI DÙNG                            │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS
┌───────────────────────────▼──────────────────────────────────┐
│  Nginx (reverse proxy, TLS, static frontend, rate limit)      │
└───────────────┬──────────────────────────────┬───────────────┘
                │ /api/v1                      │ /*
┌───────────────▼──────────────┐   ┌───────────▼───────────────┐
│  FastAPI Backend             │   │  React SPA (Vite build)   │
│  - API Layer                 │   │  - Screener               │
│  - Services                  │   │  - Trader Detail          │
│  - Scheduler                 │   │  - Compare                │
│  - AI Orchestrator           │   │  - Settings/Data Health   │
└───────┬──────────────┬───────┘   └───────────────────────────┘
        │              │
┌───────▼───────┐  ┌───▼──────────────────────┐
│ PostgreSQL    │  │ Binance BAPI (external)  │
│ raw + derived │  │ 6 endpoint groups        │
└───────┬───────┘  └──────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────┐
│ JSONL Archive (append-only, filesystem/S3-compatible)        │
│ Mỗi trader 1 dòng sau khi crawl xong → resume/idempotent      │
└──────────────────────────────────────────────────────────────┘
```

### 5.2. Stack

| Thành phần | Công nghệ | Ghi chú |
|---|---|---|
| Frontend | React + Vite + TypeScript | SPA |
| UI | Tailwind CSS + shadcn/ui hoặc Radix | Không tự viết design system |
| Chart | ECharts | Equity, drawdown, ROI, distribution |
| Data fetching | TanStack Query | Cache, loading, error, retry |
| Table | TanStack Table | Virtualized cho shortlist ~700; universe 11k khi cần |
| Backend | Python 3.12+ + FastAPI | Async |
| HTTP client | httpx | Async, timeout, retry |
| ORM | SQLAlchemy 2.x | Async session |
| Migration | Alembic | Versioned schema |
| Validation | Pydantic v2 | Request/response + AI JSON |
| Scheduler | APScheduler | 60 phút/lần |
| Database | PostgreSQL 16 | JSONB cho raw |
| Retry | tenacity | Backoff `11012005` |
| Logging | structlog | JSON logs |
| Metrics | prometheus-fastapi-instrumentator | `/metrics` |
| Test | pytest + respx | Unit + contract |
| Deploy | Docker Compose + Nginx | 1 VPS |
| AI | LLM API (OpenAI/Anthropic/khác) | Adapter pattern |

### 5.3. Module backend

| Module | Trách nhiệm | Không làm |
|---|---|---|
| **Collector** | Gọi BAPI, validate, lưu raw, ghi log | Không tính điểm |
| **Universe** | Pre-filter, tier, `pre_score`, quyết định deep fetch | Không chấm score cuối |
| **Quant** | Tính metrics từ raw | Không quyết định ranking |
| **Risk** | Sinh risk events, hard filters | Không sửa score |
| **Scoring** | Tính score theo config version | Không gọi AI |
| **Ranking** | Xếp hạng theo bảng + snapshot | Không tự đổi filter |
| **AI** | Giải thích, phản biện, evidence | Không sửa score |
| **Data Quality** | Confidence, missing, stale, anomaly | Không chặn collector |
| **Settings** | CRUD config, version, audit | Không lưu secret dạng plaintext |

### 5.4. Luồng xử lý

```
[Scheduler 60']
    → Collector.scan_list(PUBLIC + SIGNAL)
    → RawSnapshot (JSONB + JSONL)
    → Universe.prefilter()  → tier + pre_score
    → Collector.deep_fetch(shortlist)
    → Quant.compute()
    → DataQuality.evaluate()
    → Risk.evaluate()
    → Scoring.compute(config_version)
    → Ranking.snapshot()
    → (optional) AI.analyze()
    → API / Frontend
```

Nếu AI lỗi: bỏ qua AI, các bước trước vẫn hoàn tất.

### 5.5. Cấu trúc repository mục tiêu

```
copytrade-binance/
├── AGENTS.md
├── TASKS.md
├── SESSION.md
├── README.md
├── docker-compose.yml
├── .env.example
│
├── docs/
│   └── kehoach/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/            # config, database, security, logging
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/v1/          # traders, universe, ranking, compare, ai, risk, settings, collector, data_quality
│   │   ├── services/
│   │   │   ├── collector/   # base, binance_bapi, csv_import, demo
│   │   │   ├── quant/
│   │   │   ├── risk/
│   │   │   ├── scoring/
│   │   │   ├── ranking/
│   │   │   ├── ai/
│   │   │   └── data_quality/
│   │   ├── repositories/
│   │   └── scheduler/
│   ├── migrations/
│   ├── tests/               # unit, contract, integration, fixtures
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── features/        # screener, trader-detail, compare, settings, ai-report
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│   ├── Dockerfile
│   └── package.json
│
└── infra/
    └── nginx/
        └── nginx.conf
```

---

## 6. DATA CONTRACT — BINANCE COPY TRADING BAPI

> Đây là tài liệu quan trọng nhất của dự án. Mọi chỉ số phải truy được về một field trong tài liệu này.  
> Kết quả kiểm chứng: **06/11/2026**, trader `5296057151807357697` và toàn bộ universe PUBLIC/SIGNAL.

### 6.1. Bản chất nguồn dữ liệu

Đây là **BAPI nội bộ mà web app Binance gọi**, không phải API chính thức trong tài liệu developer của Binance.

- Không cần login, không cần API key, không cần cookie.
- Có thể đổi path, đổi field, chặn IP hoặc rate limit bất kỳ lúc nào.
- ToS của Binance vẫn áp dụng.
- Không được bán lại raw data.
- Nên cache, rate-limit lịch sự, ghi nguồn.

**Hệ quả thiết kế:** Collector phải dùng **Adapter pattern**. Không được để 80% code phụ thuộc trực tiếp vào BAPI.

### 6.2. Base URL & header

```python
BASE_F = "https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade"
BASE_P = "https://www.binance.com/bapi/futures/v1/public/future/copy-trade"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "clienttype": "web",
    "lang": "en",
    "Origin": "https://www.binance.com",
    "Referer": "https://www.binance.com/",
}
```

> **Quan trọng:** `performance` nằm ở `BASE_P` (public), không phải `BASE_F`.  
> Gọi `BASE_F + /lead-portfolio/performance` sẽ trả **404**.

### 6.3. Danh sách endpoint

| # | Tầng | Method | Path | Base | Page size max | Trạng thái |
|---|---|---|---|---|---|---|
| 1 | List | POST | `/home-page/query-list` | `BASE_F` | **30** | `[x]` |
| 2 | Detail | GET | `/lead-portfolio/detail?portfolioId=...` | `BASE_F` | — | `[x]` |
| 3 | Performance | GET | `/lead-portfolio/performance?portfolioId=...&timeRange=90D` | **`BASE_P`** | — | `[x]` |
| 4 | Position history | POST | `/lead-portfolio/position-history` | `BASE_F` | 50 (khuyến nghị) | `[x]` |
| 5 | Trade history | POST | `/lead-portfolio/trade-history` | `BASE_F` | **200** | `[x]` |
| 6 | Transfer history | POST | `/lead-portfolio/transfer-history` | `BASE_F` | 50 (khuyến nghị) | `[x]` |

### 6.4. Endpoint không khả dụng (đã probe 404)

| Path | Method | Kết quả | Ghi chú |
|---|---|---|---|
| `/lead-portfolio/position` | GET | 404 | Không có open positions |
| `/lead-portfolio/positions` | GET | 404 | Không có open positions |
| `/lead-portfolio/current-position` | GET | 404 | Không có open positions |
| `/lead-portfolio/copier-list` | POST | 404 | Không có per-copier |
| `/lead-portfolio/funding-history` | POST | 404 | Không có funding |
| `/lead-portfolio/funding-fee` | GET | 404 | Không có funding |

**Không có dữ liệu cho:** open positions, per-copier PnL, funding fee, liquidation price, margin ratio hiện tại, copy fill rate, copy slippage, lock-up period thực tế.

### 6.5. Endpoint 1 — List trader

**Request**

```http
POST {BASE_F}/home-page/query-list
```

```json
{
  "pageNumber": 1,
  "pageSize": 30,
  "timeRange": "90D",
  "dataType": "ROI",
  "favoriteOnly": false,
  "hideFull": false,
  "nickname": "",
  "order": "DESC",
  "userAsset": 0,
  "portfolioType": "PUBLIC"
}
```

- Collector chạy lần lượt `PUBLIC` và `SIGNAL`.
- Không dùng `ALL` mặc định vì kéo theo 1.874 PRIVATE không mở copy công khai.

**`portfolioType`**

| Giá trị | Ý nghĩa | Số lượng 06/11/2026 |
|---|---|---:|
| `PUBLIC` | Copy portfolio công khai | 8.970 |
| `SIGNAL` | Trading signal provider | 2.154 |
| `PRIVATE` | Portfolio riêng tư | 1.874 |
| `ALL` | Tất cả | 13.004 |

**Response fields (22)**

| Field | Kiểu | Ý nghĩa |
|---|---|---|
| `leadPortfolioId` | string | ID trader |
| `nickname` | string | Tên hiển thị |
| `avatarUrl` | string | Avatar |
| `currentCopyCount` | int | Số copier hiện tại |
| `maxCopyCount` | int | Slot tối đa |
| `roi` | decimal | ROI theo `timeRange` (%) |
| `pnl` | decimal | PnL theo `timeRange` (USDT) |
| `aum` | decimal | Tổng AUM |
| `copyAum` | decimal | Vốn của copier |
| `mdd` | decimal | Max drawdown (%) |
| `winRate` | decimal | Win rate (%) |
| `copierPnl` | decimal | PnL của copier |
| `apiKeyTag` | string/null | Trader dùng API? |
| `tradFiTag` | string/null | Có giao dịch TradFi? |
| `sharpRatio` | decimal/null | Sharpe ratio |
| `chartItems` | array | Chuỗi ROI theo ngày |
| `badgeName` | string/null | Badge |
| `badgeModifyTime` | int/null | Thời điểm badge |
| `badgeCopierCount` | int/null | Copier tại thời điểm badge |
| `portfolioType` | string | PUBLIC/SIGNAL/PRIVATE |
| `startTime` | int | Thời điểm mở portfolio (ms) |
| `aiSummary` | string/null | AI summary của Binance |

**`chartItems`**

```json
[
  { "value": 54.65874945, "dataType": "ROI", "dateTime": 1793750400000 },
  { "value": 6.19121926,  "dataType": "ROI", "dateTime": 1793836800000 }
]
```

- Có **90 điểm** cho `90D`, 180 điểm cho `180D`, v.v.
- Giá trị là **ROI lũy kế từ lúc mở**, không phải daily return.
- Bị **pha loãng bởi nạp/rút**.
- **Không dùng để tính MDD tuyệt đối.**
- Có thể dùng để xem shape, positive days, volatility (sau khi lọc dòng tiền).

### 6.6. Endpoint 2 — Detail

**Request**

```http
GET {BASE_F}/lead-portfolio/detail?portfolioId=5296057151807357697
```

**Response: 67 field**, trader mẫu có 48 non-null / 19 null tại thời điểm kiểm chứng ban đầu.

Các field quan trọng:

| Field | Ví dụ | Ý nghĩa |
|---|---|---|
| `status` | `ACTIVE` | ACTIVE / CLOSED / PAUSED |
| `nickname` | `请填写昵称` | Tên |
| `nicknameTranslate` | `Please enter your nickname.` | Bản dịch |
| `description` | `包亏` | Mô tả |
| `descTranslate` | `Guaranteed loss` | Bản dịch |
| `aumAmount` | `1185600.66504263` | Tổng AUM |
| `copyAum` | `22234.44092838` | Vốn copier |
| `marginBalance` | `1163366.22411425` | Vốn của lead |
| `copierPnl` | `579.37775126` | PnL copier |
| `currentCopyCount` | `59` | Copier hiện tại |
| `maxCopyCount` | `200` | Slot tối đa |
| `totalCopyCount` | `97` | Tổng từng copy |
| `closeLeadCount` | `0` | Số lần đóng |
| `favoriteCount` | `104` | Lượt favorite |
| `profitSharingRate` | `10.00` | % chia lợi nhuận |
| `fixedRadioMinCopyUsd` | `100.00` | Min copy fixed ratio |
| `fixedAmountMinCopyUsd` | `10.00` | Min copy fixed amount |
| `startTime` | `1793628005247` | Thời điểm mở (ms) |
| `lastTradeTime` | `1793901928516` | Lần trade cuối (ms) |
| `positionShow` | `true` (raw mới nhất) | Có hiển thị vị thế? **Không chặn history** |
| `tag` | `["MEDIUM_LEVERAGE"]` | Nhãn |
| `tagItemVos` | `[...]` | Chi tiết nhãn |
| `futuresType` | `UM` | USD-M Futures |
| `initInvestAsset` | `USDT` | Asset |
| `portfolioType` | `SIGNAL` | Loại portfolio |
| `enableTradingSignal` | `true` | Có bật signal |
| `rebateFee` | `0.00000000` | Rebate |
| `isPaused` | `false` | Tạm dừng |
| `unrealizedProfitShareAmount` | `0` | Profit share chưa thực hiện |

**Nhóm field null thường gặp**

| Nhóm | Field | Ghi chú |
|---|---|---|
| Null do ngữ cảnh | `userId`, `copyPortfolioId`, `publicLeadPortfolioId`, `privateLeadPortfolioId` | Chưa login / không copy / loại SIGNAL |
| Null do không áp dụng | `endTime`, `closedTime`, `lockPeriod`, `cooldownDurationHours`, `monthlyReopenLimit`, `monthlyRemaining` | Đang ACTIVE, không lock |
| Null thật sự / đang ẩn | `sharpRatio`, `aiSummary`, `badgeName`, `riskControlMaxCopyCount`, `finalEffectiveMaxCopyCount` | Chưa đủ dữ liệu hoặc không có |

> **Quan trọng:** `positionShow=false` **không chặn** `position-history`. Trên mẫu 63 trader, 30 trader có `positionShow=false` nhưng **cả 30 đều có position history**. Luôn gọi position-history nếu trader đủ điều kiện.

### 6.7. Endpoint 3 — Performance

**Request**

```http
GET {BASE_P}/lead-portfolio/performance?portfolioId=5296057151807357697&timeRange=90D
```

**Response fields (9)**

| Field | Ví dụ | Ý nghĩa |
|---|---|---|
| `timeRange` | `90D` | Cửa sổ |
| `roi` | `59.23318759` | ROI (%) |
| `pnl` | `583369.67249509` | PnL (USDT) |
| `mdd` | `31.338369` | Max drawdown (%) |
| `copierPnl` | `579.37775126` | PnL copier |
| `winRate` | `50.0` | Win rate (%) |
| `winOrders` | `5` | Số order thắng |
| `totalOrder` | `10` | Tổng order đóng |
| `sharpRatio` | `null` | Sharpe |

**Giá trị trader mẫu**

| Window | ROI | PnL | MDD | WinRate | Win/Total | Sharpe |
|---|---:|---:|---:|---:|---:|---|
| 7D | 61,75% | 608.158,76 | 31,34% | 50,00% | 5/10 | null |
| 30D | 61,75% | 608.158,76 | 31,34% | 50,00% | 5/10 | null |
| 90D | 61,75% | 608.158,76 | 31,34% | 50,00% | 5/10 | null |
| 180D | 61,75% | 608.158,76 | 31,34% | 50,00% | 5/10 | null |

> Cả 4 window giống hệt vì portfolio mới mở. Đây là lý do bắt buộc phải có `min_runtime_days`.

**Sharpe null**
- 3.884/11.124 trader (34,9%) có `sharpRatio = null`.
- Nguyên nhân thường gặp: portfolio < 30 ngày, chưa đủ mẫu.
- **Không được chấm điểm 0.** Phải renormalize hoặc giảm confidence.

### 6.8. Endpoint 4 — Position history

**Request**

```http
POST {BASE_F}/lead-portfolio/position-history
```

```json
{ "portfolioId": "5296057151807357697", "pageNumber": 1, "pageSize": 50 }
```

**Response fields (18)**

| Field | Ví dụ | Ý nghĩa |
|---|---|---|
| `positionId` | `1165716580629422080` | ID vị thế |
| `symbol` | `SAMSUNGUSDT` | Cặp |
| `side` | `Long` | Long/Short |
| `leverage` | `10` | Đòn bẩy |
| `isolated` | `Isolated` | Cross/Isolated |
| `opened` | `1793838300000` | Mở (ms) |
| `closed` | `1793901840000` | Đóng (ms) |
| `avgCost` | `...` | Giá vào TB |
| `avgClosePrice` | `...` | Giá đóng TB |
| `closingPnl` | `-204355.63` | PnL đã trừ phí |
| `maxOpenInterest` | `13653` | Size lớn nhất |
| `closedVolume` | `...` | Khối lượng đóng |
| `roi` | `-0.97822256` | ROI trên margin |
| `status` | `All Closed` | Trạng thái |
| `type` | `...` | Loại |
| `index` | `...` | Index |
| `id` | `...` | ID nội bộ |
| `updateTime` | `...` | Cập nhật |

**Giá trị trader mẫu**

| Chỉ số | Giá trị |
|---|---:|
| Số vị thế đóng | 8 |
| Thắng/thua | 5/3 → 62,5% |
| Profit factor | 1,64 |
| Avg win / avg loss | +93.938 / -95.487 |
| Payoff ratio | 0,98 |
| Leverage | max 15x, avg 13,12x |
| Margin mode | 100% Isolated |
| Holding time | avg 26,76h; median 17,02h; max 112,46h |
| Long/Short | 6/2 |
| Best | SNDK +270.852 (+82,9%, 1,8h) |
| Worst | SAMSUNG -204.356 (-97,8%, 10x, 17,7h) |

> **Không có open positions.** `position-history` chỉ trả vị thế đã đóng.

### 6.9. Endpoint 5 — Trade history

**Request**

```http
POST {BASE_F}/lead-portfolio/trade-history
```

```json
{ "portfolioId": "5296057151807357697", "pageNumber": 1, "pageSize": 200 }
```

**Response fields (14)**

| Field | Ví dụ | Ý nghĩa |
|---|---|---|
| `time` | `1793901928000` | Thời điểm fill |
| `symbol` | `SPCXUSDT` | Cặp |
| `side` | `BUY` | BUY/SELL |
| `price` | `123.18` | Giá |
| `fee` | `0.0` | Phí; có thể **âm** (rebate) |
| `feeAsset` | `USDT` | Asset phí |
| `quantity` | `225761.8404` | Notional |
| `quantityAsset` | `USDT` | Asset notional |
| `realizedProfit` | `0.0` | PnL thực hiện |
| `realizedProfitAsset` | `USDT` | Asset |
| `baseAsset` | `SPCX` | Asset cơ sở |
| `qty` | `1832.78` | Khối lượng |
| `positionSide` | `LONG` | LONG/SHORT |
| `activeBuy` | `false` | Taker/maker flag |

**Giá trị trader mẫu**

| Chỉ số | Giá trị |
|---|---:|
| Tổng fill | **5.292** |
| Thời gian | 2026-11-02 14:27 → 2026-11-05 18:05 |
| Fill/ngày | ~1.323 |
| Buy / Sell | 2.506 / 2.786 |
| Notional avg / median / max | 8.724 / 1.166 / 1.435.900 |
| Fees | **-1.797,80** (net rebate) |
| Realized PnL | +190.185,12 |
| Symbol nhiều fill | SPCX 1.593; SNDK 1.426; SAMSUNG 512 |

**Lưu ý phân trang**
- `pageSize` tối đa **200**. Truyền 500 → server trả 200.
- Nếu code kiểu `if len(lst) < 500: break` → chỉ lấy 200/5.292.
- Phải so `len(out) >= total`.
- Không có `trade_id`; phải hash để chống trùng.

### 6.10. Endpoint 6 — Transfer history

**Request**

```http
POST {BASE_F}/lead-portfolio/transfer-history
```

```json
{ "portfolioId": "5296057151807357697", "pageNumber": 1, "pageSize": 50 }
```

**Response fields (6)**

| Field | Ví dụ | Ý nghĩa |
|---|---|---|
| `time` | `1793903160000` | Thời điểm |
| `coin` | `USDT` | Asset |
| `amount` | `100027.17` | Số lượng |
| `from` | `Fiat and Spot` | Từ |
| `to` | `Lead Trading Account` | Đến |
| `transType` | `LEAD_DEPOSIT` | Loại |

`transType`: `LEAD_INVEST`, `LEAD_DEPOSIT`, `LEAD_WITHDRAW`.

**Giá trị trader mẫu**

| Chỉ số | Giá trị |
|---|---:|
| Số lệnh | 17 |
| Tổng nạp/đầu tư | 1.585.897,80 |
| Tổng rút | 1.010.000,00 |
| Net flow | +575.897,80 |

> Dòng tiền là nguyên nhân chính làm `chartItems` sai MDD. Xem mục 6.11.

### 6.11. Bài học dữ liệu bắt buộc

**1) MDD: 88,67% là lỗi công thức, không phải lỗi `chartItems`**

Trader mẫu:

```
2026-11-03: 17,68%
2026-11-04: 54,66%
2026-11-05:  6,19%   ← tụt mạnh
2026-11-06: 61,75%
```

| Cách tính | MDD | Đánh giá |
|---|---:|---|
| Coi `chartItems.value` là mức equity | **88,67%** | ❌ Sai công thức |
| `equity = 1 + value / 100` | **31,3384%** | ✅ Khớp published |
| Binance công bố | **31,338369%** | ✅ Nguồn chuẩn |

Trên 63 trader Phase 0, cách tính đúng khớp published **63/63**, sai số max **4,9 × 10⁻⁷ pp**. MDD cũng **phụ thuộc window**: chỉ 6/63 trader giống nhau ở cả 4 window, chênh tối đa 70,26 pp.

**Quy tắc:** `mdd` hiển thị = `performance.mdd`. Tự tính từ `chartItems` chỉ để audit/sanity-check, không thay thế published.

**2) WinRate theo order ≠ theo position**

| Cách tính | Giá trị |
|---|---:|
| Binance `winRate` | 50,00% (5/10) |
| Position-level | 62,50% (5/8) |

Cả hai đều đúng, nhưng định nghĩa khác nhau. UI phải ghi rõ:
- `WinRate (order)` — nguồn Binance.
- `Position Win Rate` — tính từ position-history.

**3) Null ≠ 0**

Tỷ lệ thực đo trên 11.124 trader:

| Field | Null | Zero | Cách xử lý |
|---|---:|---:|---|
| `sharpRatio` | 34,9% | 0% | Null = thiếu; không chấm 0 |
| `copierPnl` | 0% | 65,4% | Zero = không có copier PnL; không phải lỗi |
| `copyAum` | 0% | 63,3% | Zero = không có vốn copier |
| `currentCopyCount` | 0% | 74,2% | Zero = không có copier |
| `mdd` | 0% | 14,8% | Zero có thể là không drawdown hoặc thiếu dữ liệu |
| `winRate` | 0% | 22,9% | Zero có thể là 0% hoặc chưa có order |
| `aiSummary` | 98,3% | 0% | Gần như không dùng |
| `badgeName` | 99,8% | 0% | Gần như không dùng |

Với `winRate = 0` và `mdd = 0`, phải kiểm tra `totalOrder` từ performance để phân biệt “0% thật” và “không có dữ liệu”.

**4) AUM ≠ chất lượng**

Trader mẫu:
- AUM: 1.185.600,67
- Copy AUM: 22.234,44 (1,9%)
- Margin balance: 1.163.366,22 (98,1% là tiền lead)

Nếu chỉ nhìn AUM, trader này trông rất lớn. Nhưng copier chỉ góp 22k. Phải hiển thị **Copy AUM** và **Copiers** bên cạnh AUM.

**5) Lead PnL ≠ Copier PnL**

- Lead PnL: 608.158,76
- Copier PnL: 579,38

Copier vào muộn, vốn nhỏ, và chỉ có 5/10 order thắng. Không được đánh đồng hai chỉ số.

**6) Fee có thể âm**

Trade history của trader mẫu có tổng fees **-1.797,80** (net rebate). Không được coi fee âm là lỗi dữ liệu; phải hiển thị đúng dấu và ghi chú “rebate”.

**7) Window confusion**

ROI 7D/30D/90D/180D có thể giống hệt nhau với portfolio mới. Luôn ghi rõ cửa sổ và kiểm tra `runtime_days`.

---

## 7. PHỄU LỌC & TIERING

### 7.1. Universe

| Loại | Số lượng | Quét mặc định? | Lý do |
|---|---:|---|---|
| PUBLIC | 8.970 | ✅ Có | Copy portfolio công khai |
| SIGNAL | 2.154 | ✅ Có | Signal provider, có thể copy |
| PRIVATE | 1.874 | ❌ Không | Không mở copy công khai |
| **Tổng universe** | **11.124** | | |

> `PRIVATE` chỉ bật khi có nhu cầu nghiên cứu nội bộ; mặc định không quét.

### 7.2. Preset AUM

| Preset | AUM min | Watch (PUBLIC) | Dùng khi |
|---|---:|---:|---|
| Broad | 1.000 | ~1.021 | Muốn nhiều ứng viên |
| **Balanced (mặc định)** | **5.000** | **457** | Cân bằng |
| Strict | 10.000 | ~314 | Ít nhiễu |

### 7.3. Các stage của phễu

| Stage | Việc | Chi phí | Khối lượng | Output |
|---|---|---|---|---|
| **Stage 0 — List scan** | Quét list PUBLIC + SIGNAL, chỉ 90D | Rẻ | 11.124 trader, 371 trang | `universe_90d.jsonl` |
| **Stage 0.5 — Pre-filter** | Lọc trên field list, tính `pre_score`, gán tier | Rẻ (pure) | 11.124 → 515 Watch | tier + reasons |
| **Stage 1 — Performance** | Gọi `/performance` 4 windows cho Watch | Trung bình | ~515 | `performance_metrics` |
| **Stage 2 — Detail + positions + transfers** | Chỉ Qualified + top Watch | Cao | ~109–313 | detail, positions, transfers |
| **Stage 3 — Full trade history** | Chỉ High + top Qualified | Rất cao | ~13–50 | full trades |
| **Stage 4 — Quant/Scoring/Ranking** | Tính metrics, score, ranking | Nội bộ | Toàn shortlist | derived tables |
| **Stage 5 — AI** | Theo trigger | Tiền | 0–20/ngày | `ai_reports` |

### 7.4. Tiêu chí tier chính xác (theo code `phase0/tiering.py`)

| Tier | Điều kiện | Deep fetch |
|---|---|---|
| **Excluded** | Có ít nhất một lý do loại: không trade 7D, runtime < 30, ROI ≤ 0, PnL ≤ 0, WR < 40, MDD > 40, AUM < preset, hết slot | Không (trừ audit) |
| **C — Watch** | Runtime ≥ 30, ROI > 0, PnL > 0, WR ≥ 40, MDD ≤ 40, AUM ≥ 5k, còn slot, có trade 7D | Performance + detail giới hạn |
| **B — Qualified (upper)** | Watch + Runtime ≥ 90, ROI ≥ 10, WR ≥ 45, MDD ≤ 30, AUM ≥ 10k, Sharpe ≥ 0.5 hoặc null | Detail + positions + transfers |
| **A — High (upper)** | Qualified + Runtime ≥ 180, ROI ≥ 20, WR ≥ 50, MDD ≤ 20, AUM ≥ 20k, Sharpe ≥ 1 (không null) | Full trades + AI |

**Điểm cực kỳ quan trọng:**
- `B` và `A` là **subset của C**, không cộng dồn. Union deep-fetch = **Watch = 515**.
- Ở Stage 0, `totalOrder` **chưa có** trong list. Vì vậy B/A chỉ là **upper bound**. Chỉ sau `/performance` mới biết `totalOrder` và chốt tier thực.
- `A` yêu cầu Sharpe **không null** và ≥ 1. `B` cho phép Sharpe null.
- `mdd = null` hiện **không bị loại** bởi `evaluate_item()` (chỉ loại khi `mdd is not None and mdd > 40`). Đây là điểm cần chốt (xem B02, Q16).

### 7.5. Mapping tên tier giữa code và sản phẩm

| Code (`potential_tier`) | Nhãn sản phẩm | Ý nghĩa |
|---|---|---|
| `excluded` | Excluded | Bị loại, không deep fetch |
| `watch` | C — Watch | Pass pre-filter, chưa chắc đủ B/A |
| `qualified_upper` | B — Qualified (upper bound) | Pass ngưỡng B trên list; chưa lọc `totalOrder` |
| `high_upper` | A — High (upper bound) | Pass ngưỡng A trên list; chưa lọc `totalOrder` |

> Trong `summarize_tiers()`, `watch` (tổng) = `watch` + `qualified_upper` + `high_upper`. Đừng nhầm `watch_only` với `watch` tổng.

### 7.6. Reason codes

| Code | Điều kiện | Field | Ghi chú |
|---|---|---|---|
| `no_trade_7d` | Không có thay đổi ROI trong 8 điểm cuối | `chartItems` | Proxy; có thể false positive |
| `runtime_lt_30` | Runtime < 30 ngày | `startTime` | Hard filter |
| `roi_le_0` | ROI ≤ 0 | `roi` | |
| `pnl_le_0` | PnL ≤ 0 | `pnl` | |
| `winrate_lt_40` | WinRate < 40% | `winRate` | |
| `mdd_gt_40` | MDD > 40% | `mdd` | |
| `aum_lt_5000` | AUM < preset (5k mặc định) | `aum` | Có thể là `aum_lt_1000`/`aum_lt_10000` theo preset |
| `no_slots` | `maxCopyCount <= 0` hoặc `currentCopyCount >= maxCopyCount` | list | |

Một trader có thể có **nhiều reason**. `primary_reason` là reason đầu tiên theo thứ tự kiểm tra.

### 7.7. Pre-score

```python
pre_score = (
    0.30 * norm(roi_90d)
  + 0.30 * norm(-mdd_90d)
  + 0.20 * norm(sharpe_90d, missing=50)
  + 0.10 * norm(win_rate_90d)
  + 0.10 * norm(min(runtime_days / 180, 1))
)
```

Quy tắc:
- `norm()` = percentile rank trong cohort.
- Sharpe null → **50 neutral**, không phải 0.
- `pre_score` **chỉ để xếp thứ tự deep fetch**, không phải score cuối.
- Không hiển thị `pre_score` như điểm chất lượng.
- Hiện code tính percentile trên **combined PUBLIC+SIGNAL**. Cần chốt có tách cohort theo `portfolio_type` hay không (B03/Q15).

**Thực đo:** min 5,60; median 54,34; max 93,93 trên 11.124 trader.

### 7.8. Số liệu thực đo & reconciliation

| Chỉ số | Tài liệu cũ | Live 16:34Z | Chênh |
|---|---:|---:|---:|
| Universe | 11.130 | **11.124** | -6 |
| PUBLIC | 8.976 | **8.970** | -6 |
| SIGNAL | 2.154 | **2.154** | 0 |
| Watch (C) | 517 | **515** | -2 |
| Qualified incl. High | 113 | **109** | -4 |
| High | 13 | **13** | 0 |
| Excluded | ~10.613 | **10.609** | -4 |

> Chênh lệch nhỏ do list thay đổi giữa các lần quét. **Không ép số**; sản phẩm phải tính live và lưu snapshot.

**Phân bố lý do loại (có overlap, không cộng 100%)**

| Reason | Tổng | % / 11.124 | PUBLIC | % / 8.970 |
|---|---:|---:|---:|---:|
| `aum_lt_5000` | 9.102 | 81,8% | 7.320 | 81,6% |
| `roi_le_0` | 6.984 | 62,8% | 5.355 | 59,7% |
| `pnl_le_0` | 6.834 | 61,4% | 5.203 | 58,0% |
| `mdd_gt_40` | 4.264 | 38,3% | 2.996 | 33,4% |
| `winrate_lt_40` | 4.119 | 37,0% | 3.579 | 39,9% |
| `runtime_lt_30` | 2.912 | 26,2% | 2.225 | 24,8% |
| `no_trade_7d` | 1.500 | 13,5% | 1.148 | 12,8% |
| `no_slots` | 7 | 0,1% | 7 | 0,1% |

> Bảng PUBLIC khớp với tài liệu cũ (AUM 81,6%, ROI 59,1% → live 59,7%, PnL 57,5% → 58,0%, WR 39,9%, MDD 33,4%, runtime 24,9% → 24,8%, no trade 12,8%, full slot 0,1%). Chênh nhỏ do snapshot.

### 7.9. Kiểm chứng activity proxy

`traded_last_7d` được tính từ 8 điểm cuối của `chartItems`:

```python
def traded_last_7d(item):
    values = [p["value"] for p in item.get("chartItems", []) if p.get("value") is not None]
    if len(values) < 2:
        return False
    window = values[-8:] if len(values) >= 8 else values
    return (max(window) - min(window)) > 1e-9
```

**Kết quả trên 63 trader:**

| Tier | Checked | Agree | False positive | False negative |
|---|---:|---:|---:|---:|
| A | 13 | 13 | 0 | 0 |
| B | 20 | 20 | 0 | 0 |
| C | 20 | 19 | 1 | 0 |
| Excluded | 10 | 8 | 2 | 0 |
| **Tổng** | **63** | **60 (95,24%)** | **3** | **0** |

**Kết luận:** proxy **không bỏ sót trader đang giao dịch** trên mẫu, nhưng có thể giữ lại trader đã ngừng trade. Vì vậy deep fetch phải xác nhận lại `lastTradeTime` ở tầng detail.

### 7.10. Audit false negative

**Định nghĩa gate:** một trader bị coi là false negative nếu sau khi gọi detail + performance 90D, trader đó thỏa **toàn bộ** điều kiện Watch thực tế:
- ACTIVE, không paused
- runtime ≥ 30
- ROI > 0, PnL > 0
- WinRate ≥ 40, MDD ≤ 40
- AUM ≥ 5.000
- `totalOrder ≥ 20`
- còn slot
- `lastTradeTime` trong 7 ngày

**Kết quả 50 trader excluded:**

| Metric | Count | Rate | Gate |
|---|---:|---:|---|
| `fn_prompt` (định nghĩa literal) | 12 | 24,0% | Không dùng làm gate |
| `fn_watch_eligible` | **0** | **0,0%** | **PASS (< 5%)** |
| `fn_qualified_eligible` | **0** | **0,0%** | PASS |

**Theo primary reason:**

| Reason | Sampled | `fn_prompt` | `fn_watch` | `fn_qualified` |
|---|---:|---:|---:|---:|
| `aum_lt_5000` | 8 | 7 | 0 | 0 |
| `mdd_gt_40` | 8 | 5 | 0 | 0 |
| `no_slots` | 5 | 0 | 0 | 0 |
| `no_trade_7d` | 8 | 0 | 0 | 0 |
| `roi_le_0` | 7 | 0 | 0 | 0 |
| `runtime_lt_30` | 7 | 0 | 0 | 0 |
| `winrate_lt_40` | 7 | 0 | 0 | 0 |

> 12 trader “pass literal prompt” chủ yếu rơi vào AUM/MDD threshold — đây là **loại có chủ đích**, không phải false negative của phễu. Gate Watch = 0%.

### 7.11. Chính sách deep fetch

```
1. A — High Potential      (~13)   → full trades + AI
2. B — Qualified           (~109)  → detail + positions + transfers
3. C — Watch còn lại       (~406)  → performance + detail giới hạn (tối đa 200)
4. Excluded                (~10.609) → chỉ lưu list record, không deep fetch
```

**Giới hạn vận hành đề xuất:**
- Performance: toàn bộ Watch (~515).
- Detail + positions + transfers: Qualified (~109) + top Watch (tối đa 200) = ~109–313.
- Full trade history: High (~13) + top 30–50 Qualified.
- Excluded: chỉ 10 mẫu + 50 audit trong Phase 0; production không deep fetch.

### 7.12. Edge cases & quyết định cần chốt

| # | Case | Hiện tại | Đề xuất |
|---|---|---|---|
| E01 | `mdd = null` | Không bị loại ở Watch | Chốt: loại hay giữ + confidence penalty |
| E02 | `sharpe = null` ở B | Được phép | Giữ; A yêu cầu non-null |
| E03 | `totalOrder` chưa có ở Stage 0 | B/A là upper bound | Chốt tier thực sau performance |
| E04 | `no_trade_7d` false positive | 3/63 | Xác nhận `lastTradeTime` ở detail |
| E05 | `pre_score` cohort | Combined PUBLIC+SIGNAL | Chốt tách theo type nếu muốn công bằng |
| E06 | Ngưỡng PUBLIC vs SIGNAL | Giống nhau | Chốt có khác không (Q11) |
| E07 | Trader <30 ngày ROI rất cao | Bị loại | Có thể hiển thị “Radar” không xếp hạng |
| E08 | List total thay đổi giữa trang | Dedupe, scan 2 pass | Giữ; log partial nếu thiếu >1% |

---

## 8. BỘ CHỈ SỐ

> Mọi chỉ số phải có: **định nghĩa, nguồn, cửa sổ thời gian, độ tin cậy, cách xử lý khi thiếu dữ liệu**.

### 8.1. Phân tầng chỉ số

| Tầng | Tên | Nguồn | Cách dùng |
|---|---|---|---|
| **T0** | Metadata & Quality | detail/list | Hiển thị, filter, confidence |
| **T1** | Published | performance/detail | Hiển thị trực tiếp, scoring |
| **T2** | Derived | position/trade/transfer | Hiển thị kèm nhãn “tính toán” |
| **T3** | Unavailable | — | Hiển thị “N/A”, không ước lượng |

**Quy tắc hiển thị**
- T1: không cần tooltip dài, nhưng phải ghi cửa sổ (30D/90D/180D).
- T2: có badge “Derived” + tooltip công thức.
- T3: hiển thị `N/A` + lý do, không hiển thị 0.
- T0: có badge confidence.

### 8.2. 10 chỉ số cốt lõi trên Trader Detail

| # | Chỉ số | Nguồn | Ghi chú |
|---|---|---|---|
| 1 | ROI 90D | performance | + benchmark delta |
| 2 | MDD 90D | performance | Dùng published; tự tính từ `chartItems` chỉ để audit |
| 3 | Sharpe | performance | `N/A` nếu null |
| 4 | WinRate (order) | performance | kèm win/total |
| 5 | Profit Factor | position-history | derived |
| 6 | Max Leverage | position-history | derived |
| 7 | Avg Holding | position-history | derived |
| 8 | Copier PnL | performance/detail | |
| 9 | Copy AUM | detail | |
| 10 | Copiers | detail | current/max |

### 8.3. T0 — Metadata & Quality

| Chỉ số | Định nghĩa | Nguồn |
|---|---|---|
| `potential_tier` | excluded / watch / qualified / high | phễu |
| `pre_score` | 0–100, chỉ xếp thứ tự deep fetch | phễu |
| `filter_reasons` | Danh sách lý do bị loại | phễu |
| `runtime_days` | (now − startTime) / 86400 | detail.startTime |
| `portfolio_type` | PUBLIC / SIGNAL / PRIVATE | list |
| `status` | ACTIVE / CLOSED / PAUSED | detail |
| `last_trade_age_hours` | (now − lastTradeTime) / 3600 | detail |
| `data_freshness_minutes` | now − collected_at | collector |
| `data_confidence` | 0–1, xem mục 8.7 | tổng hợp |
| `total_orders` | Số order đóng | performance |
| `missing_fields` | Danh sách field null | detail/performance |

### 8.4. T1 — Published metrics

| Chỉ số | Định nghĩa | Cửa sổ | Nguồn |
|---|---|---|---|
| `roi` | ROI (%) | 7/30/90/180D | performance.roi |
| `pnl` | PnL (USDT) | 7/30/90/180D | performance.pnl |
| `mdd` | Max drawdown (%) | 7/30/90/180D | performance.mdd |
| `sharpe` | Sharpe ratio | 7/30/90/180D | performance.sharpRatio |
| `win_rate_order` | winOrders / totalOrder × 100 | 7/30/90/180D | performance |
| `win_orders` | Số order thắng | 7/30/90/180D | performance |
| `total_orders` | Tổng order đóng | 7/30/90/180D | performance |
| `copier_pnl` | PnL của copier | 7/30/90/180D | performance.copierPnl |
| `aum` | Tổng AUM | hiện tại | detail.aumAmount |
| `copy_aum` | Vốn copier | hiện tại | detail.copyAum |
| `margin_balance` | Vốn lead | hiện tại | detail.marginBalance |
| `current_copiers` | Copier hiện tại | hiện tại | detail.currentCopyCount |
| `max_copiers` | Slot tối đa | hiện tại | detail.maxCopyCount |
| `total_copiers` | Tổng từng copy | hiện tại | detail.totalCopyCount |
| `profit_sharing_rate` | % chia lợi nhuận | hiện tại | detail.profitSharingRate |
| `min_copy_fixed_ratio` | Min copy fixed ratio | hiện tại | detail.fixedRadioMinCopyUsd |
| `min_copy_fixed_amount` | Min copy fixed amount | hiện tại | detail.fixedAmountMinCopyUsd |
| `favorite_count` | Lượt favorite | hiện tại | detail.favoriteCount |
| `tags` | Leverage/TradFi/API | hiện tại | detail.tagItemVos |
| `badge` | Badge | hiện tại | detail.badgeName |
| `ai_summary` | AI summary của Binance | hiện tại | detail.aiSummary |

### 8.5. T2 — Derived metrics

| Chỉ số | Công thức | Nguồn | Độ tin cậy |
|---|---|---|---|
| `max_leverage` | max(position.leverage) | position | Cao |
| `avg_leverage` | mean(position.leverage) | position | Cao |
| `margin_mode` | mode(position.isolated) | position | Cao |
| `avg_holding_hours` | mean((closed−opened)/3600) | position | Cao |
| `median_holding_hours` | median(...) | position | Cao |
| `max_holding_hours` | max(...) | position | Cao |
| `position_win_rate` | wins / positions × 100 | position | Cao |
| `profit_factor` | gross_win / abs(gross_loss) | position | Cao |
| `payoff_ratio` | avg_win / abs(avg_loss) | position | Cao |
| `best_position_pnl` | max(closingPnl) | position | Cao |
| `worst_position_pnl` | min(closingPnl) | position | Cao |
| `worst_position_roi` | min(position.roi) × 100 | position | Cao |
| `near_liquidation_count` | count(position.roi ≤ −0.8) | position | Cao |
| `long_short_ratio` | count(Long) / count(Short) | position | Cao |
| `symbol_concentration` | max(symbol notional) / total notional | position/trade | Trung bình |
| `total_fills` | count(trades) | trade | Cao |
| `fills_per_day` | total_fills / active_days | trade | Cao |
| `avg_fill_notional` | mean(trade.quantity) | trade | Cao |
| `max_fill_notional` | max(trade.quantity) | trade | Cao |
| `total_fees` | sum(trade.fee) | trade | Cao |
| `fee_drag_pct` | total_fees / abs(gross_pnl) × 100 | trade | Trung bình |
| `realized_pnl_fills` | sum(trade.realizedProfit) | trade | Cao |
| `net_flow` | deposits − withdrawals | transfer | Cao |
| `copy_aum_ratio` | copy_aum / aum × 100 | detail | Cao |
| `copier_pnl_per_copier` | copier_pnl / max(current_copiers,1) | detail | Trung bình |
| `calmar` | roi_90d / mdd_90d | derived | Trung bình |
| `benchmark_return` | BTC return cùng window | klines | Cao |
| `excess_return` | roi − benchmark_return | derived | Cao |
| `positive_days_pct` | count(daily_return > 0) / days | chartItems | Thấp (flow) |
| `volatility_daily` | std(daily_return) | chartItems | Thấp (flow) |
| `dca_suspected` | ≥3 fill cùng symbol/side + size tăng | trade | Heuristic |
| `martingale_suspected` | size vị thế sau lỗ ≥1.5× vị thế trước, lặp ≥3 | position/trade | Heuristic |
| `open_position_inferred` | net(qty) theo symbol từ trade | trade | Rất thấp |

### 8.6. T3 — Unavailable

| Chỉ số | Lý do |
|---|---|
| Open positions | Không có endpoint |
| Per-copier PnL | Không có endpoint |
| Funding fee | Không có trong trade-history |
| Liquidation price | Cần open positions |
| Margin ratio hiện tại | Cần open positions |
| Copy fill rate | Cần tài khoản copier |
| Copy slippage | Cần tài khoản copier |
| Lock-up period thực tế | Thường null |

### 8.7. Công thức quan trọng

**ROI**

Hiển thị: `performance.roi`.

Nếu tự tính:

```
TWR = Π(1 + r_t) − 1
r_t = (NAV_t − NAV_{t-1} − flow_t) / NAV_{t-1}
```

Không dùng `PnL / balance` đơn giản vì bỏ qua nạp/rút.

**MDD**

Hiển thị: `performance.mdd`.

Nếu tự tính trên equity đã điều chỉnh:

```
peak_t = max(NAV_0..NAV_t)
dd_t   = (peak_t − NAV_t) / peak_t
MDD    = max(dd_t)
```

**Cấm:** tính MDD trực tiếp từ `chartItems` mà không điều chỉnh dòng tiền.

**Sharpe**

Hiển thị: `performance.sharpRatio` nếu khác null.

Nếu tự tính:

```
Sharpe = mean(r_daily − rf_daily) / std(r_daily) × sqrt(365)
```

- `rf` mặc định 0; ghi rõ trong tooltip.
- Tối thiểu **30 daily observations**.
- Nếu < 30 → `null`, không hiển thị số.
- Nếu std = 0 → `null`.

**WinRate**

```
win_rate_order = win_orders / total_orders × 100
position_win_rate = winning_positions / closed_positions × 100
```

- Hiển thị cả hai, ghi rõ nhãn.
- Nếu `total_orders < 20` → badge “low sample”.

**Profit Factor**

```
profit_factor = Σ(positive closingPnl) / abs(Σ(negative closingPnl))
```

- Nếu không có lỗ → `null` hoặc `∞`, không hiển thị ∞.
- Nếu < 5 vị thế → “insufficient sample”.

**Calmar**

```
calmar = roi_90d / mdd_90d
```

- Chỉ tính khi `mdd_90d > 0`.
- Nếu MDD > 100 → cắt hoặc null.

**Fee Drag**

```
fee_drag_pct = total_fees / abs(gross_pnl) × 100
```

- `total_fees` có thể âm (rebate) → fee drag âm = được hoàn phí.
- Nếu `gross_pnl = 0` → null.

**Symbol Concentration**

```
top_symbol_share = notional(symbol lớn nhất) / total_notional × 100
HHI = Σ(share_i²)
```

- HHI > 0.4 → tập trung cao.
- Hiển thị top 3 symbol.

**DCA / Martingale (heuristic)**

- **DCA suspected:** ≥ 3 fill cùng `symbol` + cùng `positionSide` trong 1 vị thế; giá vào TB di chuyển ngược hướng; size tăng dần.
- **Martingale suspected:** sau một vị thế lỗ, notional vị thế tiếp theo ≥ 1.5×; lặp lại ≥ 3 lần; cùng symbol hoặc cùng nhóm.
- Nhãn: `suspected_dca`, `suspected_martingale`. Không khẳng định tuyệt đối.

### 8.8. Data Confidence

```
confidence = 0.40 × coverage
           + 0.30 × history
           + 0.20 × freshness
           + 0.10 × continuity
```

| Thành phần | Cách tính |
|---|---|
| `coverage` | Tỷ lệ field bắt buộc non-null / tổng field bắt buộc |
| `history` | min(runtime_days / 90, 1) |
| `freshness` | 1 nếu ≤ 60 phút; giảm tuyến tính đến 0 ở 24 giờ |
| `continuity` | Tỷ lệ snapshot có mặt trong 7 ngày gần nhất |

**Nhãn**

| Confidence | Nhãn | Hành vi |
|---|---|---|
| ≥ 0.80 | High | Được vào ranking |
| 0.60–0.79 | Medium | Vào ranking, hiển thị badge |
| 0.40–0.59 | Low | Không vào top, hiển thị cảnh báo |
| < 0.40 | Insufficient | Không chấm điểm, chỉ hiển thị hồ sơ |

**Ví dụ trader mẫu:** runtime 4 ngày → `history = 4/90 = 0.044`; Sharpe null → coverage giảm; confidence < 0.4 → không xếp hạng dù ROI 61,75%. Đồng thời bị Excluded ở Stage 0 vì runtime < 30.

### 8.9. Quy tắc missing/null

1. `null` không bao giờ được coi là `0` trong scoring.
2. Missing component → loại khỏi công thức và **renormalize** trọng số.
3. Nếu tất cả component missing → `score = null`.
4. `zero` là giá trị thật (ví dụ copyAum = 0) → hiển thị “không có copier”, không “N/A”.
5. `mdd = 0` cần kiểm tra `totalOrder` để phân biệt “không drawdown” và “thiếu dữ liệu”.
6. `winRate = 0` cần kiểm tra `totalOrder` tương tự.
7. `sharpRatio = null` → `N/A`, không tô đỏ, không chấm 0.

---

## 9. SCORING, RISK RULES & RANKING

### 9.1. Trọng số scoring v1.0

| Nhóm | Trọng số | Thành phần |
|---|---:|---|
| **Risk Management** | 25 | MDD 10, Calmar 5, max leverage 5, worst position ROI 5 |
| **Consistency** | 20 | Positive months/days 8, recovery 6, ROI stability 6 |
| **Profitability** | 15 | ROI 90D 8, excess return vs BTC 4, PnL scale 3 |
| **Trading Quality** | 15 | Profit factor 6, payoff ratio 4, win rate 5 |
| **Copy Performance** | 10 | Copier PnL 4, copy AUM ratio 3, copiers 3 |
| **Capital Efficiency** | 5 | PnL/AUM 3, AUM trend 2 |
| **Data Reliability** | 10 | Confidence 6, sample size 4 |
| **Tổng** | **100** | |

### 9.2. Chuẩn hóa

1. Chia cohort: cùng `portfolio_type` + cùng `time_range`.
2. Winsorize 5–95 percentile.
3. Chuyển sang **percentile rank** trong cohort (0–100).
4. Đảo chiều với chỉ số “càng thấp càng tốt” (MDD, leverage, fee drag).
5. Missing → loại thành phần, **renormalize** trọng số còn lại.
6. Không bao giờ gán 0 cho missing.

```python
def normalize(value, cohort, direction="higher_is_better"):
    if value is None:
        return None
    p = percentile_rank(value, cohort)  # 0..100
    return p if direction == "higher_is_better" else 100 - p

def score(components, weights):
    total_w = sum(w for k, w in weights.items() if components.get(k) is not None)
    if total_w == 0:
        return None
    return sum(components[k] * w for k, w in weights.items()
               if components.get(k) is not None) / total_w
```

### 9.3. Hard filters (tách khỏi score)

| ID | Điều kiện | Hành vi |
|---|---|---|
| HF01 | `status != ACTIVE` | Loại |
| HF02 | `potential_tier = excluded` | Không xếp hạng |
| HF03 | `runtime_days < 30` | Không xếp hạng |
| HF04 | `total_orders < 20` (Watch) / `< 50` (Qualified) / `< 100` (High) | Không xếp hạng tier tương ứng |
| HF05 | `data_freshness > 150 phút` | Loại khỏi top |
| HF06 | `confidence < 0.5` | Không xếp hạng |
| HF07 | `isPaused = true` | Không xếp hạng |
| HF08 | `mdd_90d` null | Không xếp hạng Low Risk |
| HF09 | Low Risk: `runtime < 90` hoặc `mdd > 20` hoặc `max_leverage > 5` | Loại khỏi Low Risk |

### 9.4. Score bands

| Score | Nhãn | Ý nghĩa |
|---|---|---|
| 85–100 | Excellent | Rất tốt, vẫn cần kiểm tra risk flags |
| 70–84 | Good | Tốt |
| 55–69 | Average | Trung bình |
| 40–54 | Weak | Yếu |
| < 40 | High Risk | Rủi ro cao / thiếu dữ liệu |

### 9.5. Score breakdown

API trả:

```json
{
  "score": 72.4,
  "confidence": 0.83,
  "components": {
    "risk_management": { "score": 61.2, "weight": 25, "contribution": 15.3 },
    "consistency":     { "score": 78.0, "weight": 20, "contribution": 15.6 },
    "profitability":   { "score": 85.1, "weight": 15, "contribution": 12.8 },
    "trading_quality": { "score": 70.2, "weight": 15, "contribution": 10.5 },
    "copy_performance":{ "score": 55.0, "weight": 10, "contribution": 5.5 },
    "capital_efficiency": { "score": 60.0, "weight": 5, "contribution": 3.0 },
    "data_reliability":{ "score": 80.0, "weight": 10, "contribution": 8.0 }
  },
  "missing": ["sharpe"],
  "warnings": ["low_sample_copy_pnl"]
}
```

UI hiển thị thanh đóng góp từng thành phần. Đây là cách “giải thích điểm” rẻ và hiệu quả nhất.

### 9.6. Versioning

- Mọi thay đổi trọng số/hard filter tạo `scoring_config_versions` mới.
- Score cũ giữ nguyên theo version cũ.
- `trader_scores` unique `(lead_portfolio_id, config_version, computed_at)`.
- API trả `config_version` trong score response.
- Settings có preview impact + rollback.

### 9.7. Risk rules

| ID | Rule | Ngưỡng | Severity |
|---|---|---|---|
| R01 | Runtime thấp | < 30 ngày | Insufficient |
| R02 | MDD cao | > 20% | High |
| R03 | MDD nghiêm trọng | > 30% | Critical |
| R04 | Leverage cao | max > 10x | High |
| R05 | Leverage rất cao | max > 20x | Critical |
| R06 | Position ROI gần -100% | min ROI ≤ −80% | Critical |
| R07 | Mẫu quá ít | total_orders < 20 | Low sample |
| R08 | Sharpe thiếu | null | Confidence penalty |
| R09 | Dữ liệu cũ | > 150 phút | Medium |
| R10 | Copier PnL âm trong khi lead dương | copier_pnl < 0, pnl > 0 | High |
| R11 | Copy AUM quá nhỏ | copy_aum / aum < 5% | Medium |
| R12 | WinRate 100% với mẫu nhỏ | win_rate = 100, total_orders < 20 | Suspicious |
| R13 | Fee drag cao | > 20% gross PnL | Medium |
| R14 | DCA/Martingale suspected | heuristic | High |
| R15 | ROI anomaly | robust z-score > 3 | High |
| R16 | AUM giảm mạnh | −30% trong 7 ngày | Medium |
| R17 | Nickname mặc định / mô tả trống | metadata | Data quality |

**Nguyên tắc**
- Risk rule **không tự loại** trader khỏi danh sách; chỉ tạo event và ảnh hưởng score/confidence.
- Hard filter mới là thứ loại khỏi ranking.
- Mỗi event phải có `evidence` JSON: field, giá trị, ngưỡng, thời điểm.
- Không dùng AI để tạo risk event.

### 9.8. Ranking boards

| Bảng | Điều kiện | Công thức |
|---|---|---|
| **Overall** | Hard filters cơ bản | Score tổng |
| **Low Risk** | Runtime ≥ 90, MDD ≤ 20, max leverage ≤ 5, confidence ≥ 0.8 | Score + risk weight cao |
| **Consistency** | Runtime ≥ 90, ≥ 3 tháng dữ liệu | Positive months, recovery, stability |

Không làm bảng **High Return** riêng, vì nó khuyến khích chase ROI. ROI cao vẫn có thể lọc/sort trong Screener.

Mỗi lần chụp bảng xếp hạng phải lưu `ranking_snapshots` để vẽ “thay đổi thứ hạng theo thời gian”.

### 9.9. Ví dụ áp dụng: trader `5296057151807357697`

| Chỉ số | Giá trị | Đánh giá |
|---|---:|---|
| Runtime | 4 ngày | ❌ Không đủ |
| ROI 90D | 61,75% | Cao |
| PnL | 608.159 | Cao |
| MDD | 31,34% | ❌ Critical |
| Sharpe | null | ⚠️ Thiếu |
| WinRate (order) | 50% (5/10) | Mẫu nhỏ |
| Copier PnL | 579 | Rất thấp |
| AUM | 1.185.600 | Lớn nhưng 98% là tiền lead |
| Copy AUM | 22.234 | Nhỏ |
| Max leverage | 15x | ❌ High |
| Worst position ROI | −97,8% | ❌ Critical |
| Profit factor | 1,64 | Trung bình |
| Position win rate | 62,5% (5/8) | Mẫu nhỏ |

**Kết luận**
- Bị loại ngay ở Stage 0 vì runtime 4 ngày < 30.
- Không deep fetch trader này trong vận hành bình thường.
- Dữ liệu chỉ dùng làm **audit fixture** để test, không phải shortlist.
- Nếu vẫn hiển thị: badge “Excluded — insufficient history”.
- Risk flags dự kiến: R03, R04, R06, R07, R08, R10, R11.
- Đây là ví dụ điển hình của **ROI cao nhưng không thể kết luận tốt**.

---

## 10. DATABASE & STORAGE

### 10.1. Nhóm bảng

**Danh tính & cấu hình**

```sql
users (
  id uuid pk,
  email text unique not null,
  password_hash text not null,
  role text not null check (role in ('admin','viewer')),
  is_active boolean default true,
  created_at timestamptz,
  last_login_at timestamptz
)

sessions (
  id uuid pk,
  user_id uuid fk,
  refresh_token_hash text,
  expires_at timestamptz,
  revoked_at timestamptz
)

app_settings (
  id uuid pk,
  key text unique not null,
  value jsonb not null,
  version int not null,
  updated_by uuid,
  updated_at timestamptz
)

scoring_config_versions (
  id uuid pk,
  version int unique not null,
  weights jsonb not null,
  normalization jsonb not null,
  hard_filters jsonb not null,
  created_by uuid,
  created_at timestamptz,
  is_active boolean default false
)

audit_logs (
  id bigserial pk,
  user_id uuid,
  action text not null,
  entity text not null,
  entity_id text,
  before jsonb,
  after jsonb,
  created_at timestamptz
)
```

**Trader & snapshot**

```sql
traders (
  lead_portfolio_id text pk,
  nickname text,
  nickname_translate text,
  avatar_url text,
  portfolio_type text,            -- PUBLIC | SIGNAL | PRIVATE
  status text,                    -- ACTIVE | CLOSED | ...
  description text,
  start_time timestamptz,
  last_trade_time timestamptz,
  futures_type text,
  init_invest_asset text,
  created_at timestamptz,
  updated_at timestamptz
)

trader_universe (
  lead_portfolio_id text pk references traders(lead_portfolio_id),
  potential_tier text not null,      -- excluded | watch | qualified | high
  pre_score numeric,
  filter_reasons jsonb,              -- lý do bị loại / thiếu dữ liệu
  last_list_seen_at timestamptz,
  last_performance_fetch_at timestamptz,
  last_detail_fetch_at timestamptz,
  last_positions_fetch_at timestamptz,
  last_trades_fetch_at timestamptz,
  deep_fetch_status text not null default 'pending',
  updated_at timestamptz
)

portfolio_snapshots (
  id bigserial pk,
  lead_portfolio_id text fk,
  collected_at timestamptz not null,
  collected_hour timestamptz not null,  -- truncate hour, dùng cho unique
  source text not null,                 -- bapi | csv | demo
  raw jsonb not null,
  schema_version int not null,
  created_at timestamptz,
  unique (lead_portfolio_id, collected_hour, source)
)
-- partition by range (collected_hour), mỗi tháng 1 partition

performance_metrics (
  id bigserial pk,
  lead_portfolio_id text fk,
  time_range text not null,        -- 7D | 30D | 90D | 180D
  collected_at timestamptz not null,
  roi numeric,
  pnl numeric,
  mdd numeric,
  copier_pnl numeric,
  win_rate numeric,
  win_orders int,
  total_orders int,
  sharpe numeric,
  raw jsonb,
  unique (lead_portfolio_id, time_range, collected_at)
)

trader_metrics_daily (
  id bigserial pk,
  lead_portfolio_id text fk,
  metric_date date not null,
  roi_cumulative numeric,
  source text,
  raw jsonb,
  unique (lead_portfolio_id, metric_date, source)
)
-- lấy từ chartItems; chỉ dùng cho shape, không dùng tính MDD tuyệt đối
```

**Lịch sử giao dịch**

```sql
position_history (
  id bigserial pk,
  lead_portfolio_id text fk,
  position_id text not null,
  symbol text,
  side text,
  leverage numeric,
  isolated text,                  -- Isolated | Cross
  opened_at timestamptz,
  closed_at timestamptz,
  avg_cost numeric,
  avg_close_price numeric,
  closing_pnl numeric,
  max_open_interest numeric,
  closed_volume numeric,
  roi numeric,
  status text,
  raw jsonb,
  unique (lead_portfolio_id, position_id)
)

trade_history (
  id bigserial pk,
  lead_portfolio_id text fk,
  trade_hash text not null,       -- hash vì API không có trade_id
  traded_at timestamptz,
  symbol text,
  side text,
  price numeric,
  fee numeric,
  fee_asset text,
  quantity numeric,
  quantity_asset text,
  realized_profit numeric,
  realized_profit_asset text,
  base_asset text,
  qty numeric,
  position_side text,
  active_buy boolean,
  raw jsonb,
  unique (lead_portfolio_id, trade_hash)
)

transfer_history (
  id bigserial pk,
  lead_portfolio_id text fk,
  transfer_hash text not null,
  transferred_at timestamptz,
  coin text,
  amount numeric,
  from_account text,
  to_account text,
  trans_type text,
  raw jsonb,
  unique (lead_portfolio_id, transfer_hash)
)
```

**Phân tích & vận hành**

```sql
risk_metrics (
  id bigserial pk,
  lead_portfolio_id text fk,
  computed_at timestamptz,
  max_leverage numeric,
  avg_leverage numeric,
  margin_mode text,
  avg_holding_hours numeric,
  max_holding_hours numeric,
  position_win_rate numeric,
  profit_factor numeric,
  payoff_ratio numeric,
  symbol_concentration numeric,
  fee_drag numeric,
  max_position_roi_negative numeric,
  unique (lead_portfolio_id, computed_at)
)

risk_events (
  id bigserial pk,
  lead_portfolio_id text fk,
  rule_id text not null,
  severity text not null,          -- critical | high | medium | low
  status text not null default 'open',
  evidence jsonb not null,
  detected_at timestamptz,
  resolved_at timestamptz
)

trader_scores (
  id bigserial pk,
  lead_portfolio_id text fk,
  config_version int not null,
  score numeric not null,
  component_scores jsonb not null,
  confidence numeric not null,
  computed_at timestamptz,
  unique (lead_portfolio_id, config_version, computed_at)
)

ranking_snapshots (
  id bigserial pk,
  ranking_type text not null,      -- overall | low_risk | consistency
  config_version int not null,
  time_range text not null,
  captured_at timestamptz,
  rows jsonb not null
)

data_quality_flags (
  id bigserial pk,
  lead_portfolio_id text fk,
  flag text not null,              -- stale | insufficient_history | missing_sharpe ...
  severity text,
  details jsonb,
  detected_at timestamptz
)

trader_labels (
  id bigserial pk,
  lead_portfolio_id text fk,
  label text not null,             -- suspicious_dca | high_leverage | tradfi ...
  confidence numeric,
  evidence jsonb,
  detected_at timestamptz
)

ai_reports (
  id uuid pk,
  lead_portfolio_id text fk,
  time_range text,
  model text,
  prompt_version text,
  input_hash text,
  report jsonb not null,
  cost_usd numeric,
  created_at timestamptz
)

ai_usage (
  id bigserial pk,
  report_id uuid,
  provider text,
  model text,
  input_tokens int,
  output_tokens int,
  cost_usd numeric,
  created_at timestamptz
)

benchmark_prices (
  id bigserial pk,
  symbol text not null,            -- BTCUSDT | ETHUSDT
  price_date date not null,
  close numeric not null,
  unique (symbol, price_date)
)

collection_logs (
  id bigserial pk,
  run_id uuid,
  started_at timestamptz,
  finished_at timestamptz,
  status text,                     -- success | partial | failed
  total_traders int,
  fetched int,
  inserted int,
  updated int,
  errors int,
  details jsonb
)
```

### 10.2. Bảng defer (không làm MVP)

- `paper_copy_sessions`
- `paper_copy_equity`
- `ai_agents` (không cần multi-agent)

### 10.3. Index & partition bắt buộc

```sql
CREATE INDEX idx_traders_type_status ON traders(portfolio_type, status);
CREATE INDEX idx_perf_lookup ON performance_metrics(lead_portfolio_id, time_range, collected_at DESC);
CREATE INDEX idx_snap_hour ON portfolio_snapshots(collected_hour DESC);
CREATE INDEX idx_scores_lookup ON trader_scores(config_version, score DESC);
CREATE INDEX idx_positions_trader ON position_history(lead_portfolio_id, closed_at DESC);
CREATE INDEX idx_trades_trader ON trade_history(lead_portfolio_id, traded_at DESC);
```

Partition `portfolio_snapshots` theo tháng.

### 10.4. Chống trùng & resume

- List: dedupe theo `leadPortfolioId`, lưu `collected_hour`.
- Universe: unique `lead_portfolio_id`; lưu `potential_tier`, `pre_score`, `filter_reasons`.
- Deep fetch: trạng thái riêng theo từng tầng (`performance`, `detail`, `positions`, `trades`).
- Detail: unique `(portfolio_id, collected_hour, source)`.
- Position: unique `(portfolio_id, position_id)`.
- Trade: hash `(time, symbol, side, price, qty, fee)` → `trade_hash`.
- Transfer: hash `(time, coin, amount, trans_type)` → `transfer_hash`.
- JSONL: ghi sau mỗi trader; chạy lại chỉ crawl trader chưa có.
- Nếu list total thay đổi giữa các trang: chấp nhận snapshot, dedupe, ghi log `partial` nếu thiếu > 1%.

### 10.5. JSONL archive

- Mỗi trader 1 dòng sau khi crawl xong.
- Append-only, không sửa.
- Có thể rebuild DB từ archive.
- Ghi sau mỗi trader để resume.
- Nén định kỳ (gzip) nếu dung lượng lớn.

### 10.6. Retention đề xuất

| Dữ liệu | Giữ | Ghi chú |
|---|---|---|
| `portfolio_snapshots` | 12 tháng | Partition tháng, archive cũ |
| `performance_metrics` | 24 tháng | Dùng cho history/ranking |
| `position_history` | 24 tháng | Có thể archive trader excluded |
| `trade_history` | 12–24 tháng | Full trades chỉ shortlist |
| `transfer_history` | 24 tháng | Nhỏ |
| `trader_scores` | 24 tháng | Theo config version |
| `ranking_snapshots` | 24 tháng | Vẽ history |
| `ai_reports` | 12 tháng | Có cost tracking |
| `collection_logs` | 12 tháng | Vận hành |
| JSONL archive | 24 tháng | Backup ngoài DB |

> Retention chính xác là câu hỏi mở Q03/Q10; bảng trên là đề xuất mặc định.

---

## 11. API V1

### 11.1. Quy ước

- Tất cả dưới `/api/v1`.
- Response wrapper:

```json
{
  "data": {},
  "meta": { "request_id": "...", "generated_at": "..." },
  "error": null
}
```

- Lỗi:

```json
{
  "data": null,
  "error": { "code": "TRADER_NOT_FOUND", "message": "...", "details": {} }
}
```

- Auth: JWT access 15 phút + refresh 7 ngày, refresh rotate.
- RBAC: admin/viewer.
- Pagination: `page`, `page_size` (max 100).
- Mọi response list trả `total`, `page`, `page_size`, `filter_summary`.

### 11.2. Trader & screener

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/traders` | Danh sách + filter + sort + pagination |
| GET | `/traders/{id}` | Hồ sơ trader |
| GET | `/traders/{id}/performance` | Metrics theo 7D/30D/90D/180D |
| GET | `/traders/{id}/positions` | Position history (paginated) |
| GET | `/traders/{id}/trades` | Trade history (paginated) |
| GET | `/traders/{id}/transfers` | Transfer history |
| GET | `/traders/{id}/risk` | Risk metrics + events + flags |
| GET | `/traders/{id}/score` | Score + breakdown + confidence |

**Query params `/traders`**

```
q, portfolio_type, status,
potential_tier,                  -- excluded | watch | qualified | high
min_pre_score,
min_roi_90d, max_roi_90d,
max_mdd_90d,
min_sharpe, max_sharpe,
min_win_rate, max_win_rate,
min_runtime_days,
min_total_orders,
min_copiers, min_copy_aum,
max_leverage,
risk_level,
include_excluded,                -- false mặc định
sort_by, sort_dir,
page, page_size (max 100)
```

**Endpoint bổ sung**

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/universe/summary` | Số lượng theo tier, lý do loại, lần chạy cuối |
| GET | `/universe/traders` | Danh sách trader trong phễu, kể cả excluded |
| POST | `/universe/recompute` | Tính lại tier/pre_score (admin) |

### 11.3. Ranking & compare

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/ranking?type=overall&time_range=90D` | Bảng xếp hạng |
| POST | `/compare` | So sánh 2–4 trader |
| GET | `/compare/correlation?ids=...` | Correlation matrix |

### 11.4. Dashboard & data health

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/dashboard/overview` | KPIs + chart data |
| GET | `/data-quality/summary` | Coverage, null rates, stale |
| GET | `/data-quality/traders/{id}` | Flags của 1 trader |
| GET | `/collector/status` | Lần chạy cuối, trạng thái |
| POST | `/collector/run-scan` | Chạy scan thủ công (admin) |
| POST | `/collector/run-deep` | Chạy deep fetch thủ công (admin) |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus |

### 11.5. AI & settings

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/ai/analyze/{id}` | Tạo báo cáo (admin) |
| GET | `/ai/reports/{id}` | Danh sách báo cáo |
| GET | `/ai/reports/{id}/{report_id}` | Chi tiết |
| GET | `/settings` | Đọc config |
| PUT | `/settings` | Cập nhật config (admin, tạo version) |
| GET | `/settings/versions` | Lịch sử version |
| POST | `/settings/rollback/{version}` | Rollback (admin) |

### 11.6. Thứ tự implement API

1. `/health` + auth + `/traders/{id}` (Phase 1).
2. `/universe/summary`, `/universe/traders`, `/collector/status` (Phase 2).
3. `/traders` filter/sort/pagination, `/traders/{id}/score`, `/ranking` (Phase 3).
4. `/traders/{id}/performance|positions|trades|transfers|risk`, `/compare` (Phase 4).
5. `/ai/*`, `/settings/*` (Phase 5).

### 11.7. Performance targets

| Endpoint | p95 |
|---|---|
| `GET /traders?page=1&page_size=50` | < 500ms |
| `GET /traders` shortlist ~700 + filter | < 1s |
| `GET /traders/{id}` | < 300ms |
| Dashboard overview | < 1s |
| Screener render 100 rows | < 1s |

---

## 12. COLLECTOR DESIGN

### 12.1. Adapter interface

```python
class DataSourceAdapter(Protocol):
    async def list_traders(self, time_range: str, page: int) -> Page
    async def get_detail(self, portfolio_id: str) -> dict
    async def get_performance(self, portfolio_id: str, time_range: str) -> dict
    async def get_positions(self, portfolio_id: str, page: int) -> Page
    async def get_trades(self, portfolio_id: str, page: int) -> Page
    async def get_transfers(self, portfolio_id: str, page: int) -> Page
```

Implementations:
- `BinanceBapiAdapter` — chính.
- `CsvImportAdapter` — fallback khi BAPI chết.
- `DemoAdapter` — fixture cho test/dev.

### 12.2. Chu kỳ thu thập — phễu nhiều tầng

| Tầng | Việc | Tần suất | Khối lượng |
|---|---|---|---|
| **L0 — Universe scan** | Quét list PUBLIC + SIGNAL, chỉ 90D | 60 phút | 11.124 trader, ~371 trang |
| **L1 — Pre-filter** | Lọc trên field list, tính `pre_score`, gán tier | Sau L0 | ~515 Watch |
| **L2 — Performance** | Gọi `/performance` cho Watch | 2–6 giờ/lần | ~515 |
| **L3 — Detail + positions + transfers** | Chỉ Qualified + Watch nổi bật | 6–24 giờ/lần | ~109–313 |
| **L4 — Full trade history** | Chỉ High + top Qualified | 24 giờ/lần | ~13–50 |
| **L5 — Scoring/ranking** | Tính score, chụp ranking | Sau L2–L4 | Toàn shortlist |
| **L6 — AI report** | Theo trigger | Manual / significant change | 0–20/ngày |

### 12.3. Rate limit & retry

```
- list: 30/page
- trade-history: 200/page
- position-history: 50/page (khuyến nghị)
- transfer-history: 50/page
- concurrency: 6–8
- backoff: 2 → 4 → 8 → 16s
- mã rate limit: 11012005
- timeout: 20s/request
- retry tối đa: 5
```

**Thực đo Phase 0:**
- 32 request với concurrency 1/5/10: **0 rate-limit, 0 lỗi**.
- Median latency: 1 worker ~650–685ms; 5 worker ~1,08–1,35s; 10 worker ~1,53–1,58s.
- Vẫn phải giữ backoff vì BAPI có thể thay đổi.

### 12.4. Scheduler

- APScheduler chạy trong **một process duy nhất**.
- Nếu scale > 1 instance: dùng PostgreSQL advisory lock `pg_try_advisory_lock`.
- Không chạy scheduler trong mỗi uvicorn worker; tách container `scheduler` hoặc `--workers 1`.
- Job lock ghi vào `collection_logs`; job đang chạy thì bỏ qua lần tiếp theo.

### 12.5. Chống trùng & resume

- List: dedupe theo `leadPortfolioId`, lưu `collected_hour`.
- Universe: unique `lead_portfolio_id`; lưu tier/reasons.
- Deep fetch: trạng thái riêng theo tầng.
- Detail: unique `(portfolio_id, collected_hour, source)`.
- Position: unique `(portfolio_id, position_id)`.
- Trade/transfer: hash unique.
- JSONL: ghi sau mỗi trader; chạy lại chỉ crawl trader chưa có.
- Nếu list total thay đổi giữa các trang: dedupe, log partial nếu thiếu > 1%.

### 12.6. Collection logs

Mỗi run ghi:
- `run_id`, start/finish, status.
- `total_traders`, `fetched`, `inserted`, `updated`, `errors`.
- Chi tiết theo tầng: list, prefilter, performance, detail, positions, trades, transfers.
- `pages_requested`, `pages_failed`, `coverage`.
- `details` JSONB chứa lỗi mẫu, endpoint fail, rate-limit count.

### 12.7. Deep fetch selection (pseudo-code)

```python
watch = [t for t in universe if t.tier in ("watch", "qualified_upper", "high_upper")]

# L2: performance cho toàn bộ Watch
for trader in sorted(watch, key=lambda t: (t.tier_rank, -t.pre_score)):
    fetch_performance(trader, ["7D", "30D", "90D", "180D"])

# L3: detail + positions + transfers
qualified = [t for t in watch if t.potential_tier in ("qualified_upper", "high_upper")]
top_watch = [t for t in watch if t.potential_tier == "watch"][:200]
for trader in qualified + top_watch:
    fetch_detail(trader)
    fetch_positions(trader)
    fetch_transfers(trader)

# L4: full trades
high = [t for t in watch if t.potential_tier == "high_upper"]
top_qualified = [t for t in qualified][:50]
for trader in high + top_qualified:
    fetch_all_trades(trader)
```

### 12.8. Kill switch & config

- `collector.enabled = true/false` trong settings.
- `collector.scan_interval_minutes = 60`.
- `collector.deep_interval_hours = 6`.
- `collector.max_detail_per_run = 300`.
- `collector.max_full_trades_per_run = 50`.
- `collector.concurrency = 6`.
- `collector.timeout_seconds = 20`.
- `collector.max_retries = 5`.
- `collector.preset = balanced`.

---

## 13. UI/UX & MÀN HÌNH

> Mục tiêu: người dùng ra quyết định trong **< 30 giây** khi sàng lọc, và hiểu **vì sao** một trader được điểm cao/thấp. Không làm dashboard trang trí. Mỗi pixel phải phục vụ quyết định.

### 13.1. Nguyên tắc thiết kế

1. **Số liệu trước, màu sắc sau.** Không dùng màu để trang trí; chỉ dùng để cảnh báo.
2. **Luôn hiển thị cửa sổ thời gian.** `ROI 90D`, `MDD 90D`, không bao giờ chỉ ghi `ROI`.
3. **Luôn hiển thị nguồn.** `Binance`, `Derived`, `Estimated`.
4. **Không giấu sự thiếu dữ liệu.** `N/A` kèm lý do, không hiển thị `0`.
5. **Một màn hình = một quyết định.** Screener để chọn; Detail để xác nhận; Compare để chốt.
6. **Table là trung tâm.** Không biến mọi thứ thành card.
7. **Empty state phải hữu ích.** Gợi ý bỏ filter, mở rộng thời gian, xem trader mẫu.
8. **Tooltip ngắn, có ví dụ.** Không viết định nghĩa hàn lâm.

### 13.2. Layout tổng thể

```
┌─────────────────────────────────────────────────────────────┐
│ Topbar: Logo · Search · Data freshness · User menu          │
├──────────┬──────────────────────────────────────────────────┤
│ Sidebar  │  Nội dung                                        │
│ Screener │                                                  │
│ Ranking  │                                                  │
│ Compare  │                                                  │
│ Risk     │                                                  │
│ Settings │                                                  │
└──────────┴──────────────────────────────────────────────────┘
```

- Sidebar cố định, có thể thu gọn.
- Topbar luôn hiển thị **Data freshness**: “Cập nhật 12 phút trước”.
- Nếu dữ liệu cũ > 150 phút: banner vàng toàn trang.
- Mobile: sidebar thành drawer; table horizontal scroll; ẩn cột phụ.

### 13.3. Màn hình 1 — Screener

**Mục tiêu:** lọc từ universe 11k xuống shortlist 5–20 ứng viên trong < 30 giây.

**Bố cục**

```
┌─────────────────────────────────────────────────────────────┐
│ Filter bar (sticky)                                         │
│ [Search] [Type] [Runtime] [ROI] [MDD] [Sharpe] [WinRate]    │
│ [Copiers] [CopyAum] [Leverage] [Risk] [Saved views] [Reset] │
├─────────────────────────────────────────────────────────────┤
│ 515 kết quả · Sắp xếp: Score ▼ · [Export CSV] [Compare 3]   │
├─────────────────────────────────────────────────────────────┤
│ ☐ Trader      Score  Conf  ROI90  MDD90  Sharpe  WR   Lev   │
│ ☐ ...                                                       │
└─────────────────────────────────────────────────────────────┘
```

**Cột mặc định**

| Cột | Nội dung | Ghi chú |
|---|---|---|
| ☐ | Chọn để compare | Max 4 |
| Trader | Avatar + nickname + type | Click mở detail |
| Tier | High / Qualified / Watch | Màu theo tier |
| Score | 0–100 + band | Tooltip breakdown |
| Confidence | 0–100% | Badge màu |
| ROI 90D | % | Kèm benchmark delta |
| MDD 90D | % | Đỏ nếu > 20 |
| Sharpe | Số hoặc `N/A` | `N/A` không tô đỏ |
| WinRate | % + win/total | Low sample badge |
| Runtime | Ngày | < 30 → badge “New” |
| Copiers | Số hiện tại | 0 → xám |
| Copy AUM | USDT | |
| Max Leverage | x | Từ position-history |
| Risk | Low/Medium/High/Critical | |
| Freshness | Thời gian | |

**Cột tùy chọn (ẩn mặc định)**
- PnL 90D
- Calmar
- Profit Factor
- Position Win Rate
- Avg Holding
- Fee Drag
- Top Symbol
- Tags
- Last Trade

**Filter**

| Filter | Kiểu | Mặc định |
|---|---|---|
| Search | Text | — |
| Portfolio type | Multi-select | PUBLIC + SIGNAL |
| **Potential tier** | Multi-select | **High + Qualified + Watch** |
| Include excluded | Toggle | Off |
| Runtime | Min/max days | ≥ 30 |
| ROI 90D | Min/max | — |
| MDD 90D | Max | — |
| Sharpe | Min | — |
| WinRate | Min | — |
| Total Orders | Min | 20 |
| Copiers | Min | — |
| Copy AUM | Min | — |
| Max Leverage | Max | — |
| Risk level | Multi-select | — |
| Has Sharpe | Toggle | — |
| Only with copiers | Toggle | — |
| Saved view | Dropdown | — |

**Hành vi quan trọng**
- **Funnel summary** trên đầu bảng: `Universe 11.124 → Watch 515 → Qualified 109 → High 13`.
- **Tier badge** trên mỗi dòng: High / Qualified / Watch / Excluded.
- **Count preview** ngay trên filter: “1.234 trader khớp”.
- Nếu filter trả về 0: gợi ý “Thử bỏ MDD ≤ 15” hoặc “Mở rộng runtime”.
- Sort mặc định: Score DESC.
- Không cho sort mặc định theo ROI.
- Chọn > 4 trader → disable compare, hiển thị “Tối đa 4”.
- Lưu view: tên + filter JSON, chỉ admin/viewer tự lưu.
- Export CSV: chỉ export cột đang hiển thị, kèm metadata filter.

**Empty state**

```
Không có trader khớp bộ lọc.
[ Bỏ filter MDD ] [ Mở rộng runtime lên 30 ngày ] [ Xem trader mẫu ]
```

### 13.4. Màn hình 2 — Trader Detail

**Mục tiêu:** trả lời “Trader này có đáng theo dõi không? Rủi ro lớn nhất là gì? Dữ liệu có đủ tin không?”

**Bố cục**

```
┌─────────────────────────────────────────────────────────────┐
│ Header: Avatar · Nickname · Type · Status · Tags            │
│ Score 72 · Confidence 83% · Risk Medium · [Compare] [AI]    │
├─────────────────────────────────────────────────────────────┤
│ 10 chỉ số cốt lõi (grid 5x2)                                │
├─────────────────────────────────────────────────────────────┤
│ [Equity/ROI] [Drawdown] [Monthly Return]                    │
├─────────────────────────────────────────────────────────────┤
│ Score breakdown · Risk flags · What's missing               │
├─────────────────────────────────────────────────────────────┤
│ Positions · Trades summary · Transfers                      │
└─────────────────────────────────────────────────────────────┘
```

**Header**
- Avatar, nickname, `portfolio_type`.
- Status badge: ACTIVE / PAUSED / CLOSED.
- Tags: `MEDIUM_LEVERAGE`, `TradFi`, `API`.
- Tier: High / Qualified / Watch / Excluded.
- Nếu Excluded: badge + lý do (runtime, ROI, số lệnh, AUM, full slot…).
- Runtime: “Mở 4 ngày trước” + badge “Insufficient history” nếu < 30.
- Score + band.
- Confidence + tooltip.
- Risk level.
- Nút Compare, AI Analyze (chỉ bật cho Qualified/High).

**10 chỉ số cốt lõi**

| # | Chỉ số | Ghi chú |
|---|---|---|
| 1 | ROI 90D | + benchmark delta |
| 2 | MDD 90D | |
| 3 | Sharpe | `N/A` nếu null |
| 4 | WinRate (order) | kèm win/total |
| 5 | Profit Factor | derived |
| 6 | Max Leverage | derived |
| 7 | Avg Holding | derived |
| 8 | Copier PnL | |
| 9 | Copy AUM | |
| 10 | Copiers | |

Mỗi ô có tooltip: định nghĩa + nguồn + cửa sổ.

**Biểu đồ**
1. **ROI vs Benchmark** — ROI 90D và BTC buy&hold.
2. **Drawdown** — chỉ vẽ nếu có dữ liệu; ghi rõ “estimated from published MDD” nếu không có equity.
3. **Monthly Return** — nếu đủ dữ liệu; nếu không, empty state.
4. **Position PnL distribution** — từ position-history.

**Score breakdown**

```
Risk Management   61/100  ███████░░░  15.3/25
Consistency       78/100  █████████░  15.6/20
Profitability     85/100  ██████████  12.8/15
Trading Quality   70/100  ███████░░░  10.5/15
Copy Performance  55/100  █████░░░░░   5.5/10
Capital Efficiency 60/100 ██████░░░░   3.0/5
Data Reliability  80/100  ████████░░   8.0/10
```

Bên cạnh: “Vì sao điểm này thấp?” — text deterministic, không dùng AI.

**Risk flags**

| Severity | Ví dụ |
|---|---|
| Critical | MDD > 30%, position ROI ≤ −80%, leverage > 20x |
| High | MDD > 20%, leverage > 10x, copier PnL âm |
| Medium | Data stale, fee drag cao, copy AUM < 5% |
| Low | Sample nhỏ, Sharpe null |

Mỗi flag mở ra evidence: field, value, threshold, timestamp.

**What’s missing**

Luôn hiển thị panel:

```
Dữ liệu chưa đủ để kết luận:
- Sharpe: chưa đủ 30 ngày
- Open positions: Binance không cung cấp
- Per-copier: Binance không cung cấp
- Funding: không có trong trade-history
```

Đây là điểm tạo niềm tin, không phải điểm yếu.

**Positions**
- Bảng: symbol, side, leverage, margin mode, opened, closed, holding, PnL, ROI.
- Filter symbol/side.
- Badge “Near liquidation” nếu ROI ≤ −80%.
- Không hiển thị open positions.

**Trades summary**
- Tổng fill, fill/day, buy/sell, notional avg/median/max.
- Fees, realized PnL.
- Top symbols.
- DCA/martingale badge nếu suspected.
- Không hiển thị từng fill ở MVP (quá nhiều); có thể tải thêm.

**Transfers**
- Nạp/rút, net flow, timeline.
- Cảnh báo nếu flow lớn làm ROI khó so sánh.

### 13.5. Màn hình 3 — Compare

**Mục tiêu:** chốt 2–4 trader.

**Bố cục**
- Bảng so sánh: 2–4 cột.
- Chart overlay: ROI, drawdown.
- Correlation matrix.
- “Winner by category”: Risk, Consistency, Profitability.
- Cảnh báo nếu compare trader khác `portfolio_type`.

**Bảng**

| Chỉ số | Trader A | Trader B | Trader C |
|---|---:|---:|---:|
| Score | | | |
| Confidence | | | |
| ROI 90D | | | |
| MDD 90D | | | |
| Sharpe | | | |
| WinRate | | | |
| Profit Factor | | | |
| Max Leverage | | | |
| Copy PnL | | | |
| Copy AUM | | | |
| Runtime | | | |
| Risk | | | |

**Correlation**
- Tính từ daily returns (chartItems), sau khi lọc flow.
- Ghi rõ “estimated”.
- Nếu < 30 điểm chung → `N/A`.

### 13.6. Màn hình 4 — Settings & Data Health

**Mục tiêu:** toàn bộ cấu hình chỉnh trên web, không cần SSH.

**Tabs**

| Tab | Nội dung |
|---|---|
| **Data Collection** | Chu kỳ, portfolio type, giới hạn, retry, chạy thủ công |
| **Shortlist / Funnel** | Preset AUM, ngưỡng tier, pre-score, xem excluded, chạy lại phễu |
| **Data Health** | Lần chạy cuối, số trader theo tier, lỗi, stale, null rates |
| **Scoring** | Trọng số, hard filters, version, rollback |
| **Risk Rules** | Ngưỡng, bật/tắt, severity |
| **AI** | Provider, model, temperature, budget, prompt version |
| **Ranking** | Bảng, filter, thời gian |
| **System** | Log, backup, version, health |

**Data Health**

```
Lần chạy cuối: 2026-11-06 16:34 UTC (12 phút trước)
Trạng thái: SUCCESS
Universe: 11.124 / 11.124
Watch: 515 · Qualified: 109 · High: 13
Deep fetch: 109–313 detail · 13–50 full trades
Lỗi: 0 (0.00%)
Null Sharpe: 34,9%
Null AI summary: 98,3%
Stale > 150 phút: 0 trader
```

Nút: `Run now`, `View logs`, `Download report`.

**Scoring**
- Slider/number input cho từng trọng số.
- Tổng phải = 100; nếu không, disable Save.
- “Preview impact”: so sánh top 20 trước/sau.
- Save → tạo version mới + audit log.
- Rollback về version cũ.

### 13.7. Màn hình 5 — AI Report (phase 5)

- Nút “Analyze” trên Trader Detail.
- Report gồm:
  - Tóm tắt 3 câu.
  - Điểm mạnh (có evidence).
  - Điểm yếu (có evidence).
  - Risk flags.
  - “Chưa đủ dữ liệu để kết luận”.
  - Không đưa ra lời khuyên đầu tư.
- Hiển thị model, prompt version, cost, thời gian.
- Không auto chạy mọi trader.
- Cooldown 24h/trader.

### 13.8. Component & style

**Component cần có**
- `MetricCard` — value, label, tooltip, badge, delta.
- `ScoreBadge` — score + band + confidence.
- `RiskBadge` — severity.
- `DataSourceBadge` — Binance / Derived / Estimated.
- `ConfidenceBadge`.
- `EmptyState`.
- `ErrorState`.
- `FilterBar`.
- `DataTable` — sort, virtualize, column visibility.
- `ChartCard` — title, source, timeframe.
- `TooltipInfo`.
- `InsightList` — deterministic insights.

**Màu**

| Ý nghĩa | Màu |
|---|---|
| Tốt | Green |
| Trung bình | Amber |
| Xấu / Critical | Red |
| Thiếu dữ liệu | Gray |
| Derived | Blue outline |

Không dùng đỏ cho `N/A`.

**Typography**
- Số liệu: tabular nums, font mono cho bảng.
- Tiêu đề: semibold.
- Tooltip: 12–13px, tối đa 2 dòng.

### 13.9. Accessibility

- Contrast ≥ 4.5:1.
- Không chỉ dùng màu để biểu đạt; luôn có text/icon.
- Keyboard navigation cho filter/table.
- Focus visible.
- Tooltip truy cập được bằng keyboard.
- Chart có bảng dữ liệu thay thế.

### 13.10. Những thứ không hiển thị

- Không hiển thị “open positions” như thể có dữ liệu.
- Không hiển thị “copy fill rate” hoặc “slippage” giả.
- Không hiển thị MDD tự tính từ `chartItems`.
- Không hiển thị Sharpe 0 khi null.
- Không hiển thị ROI mà không ghi cửa sổ.
- Không hiển thị “AI dự đoán giá”.
- Không hiển thị “nên copy trader này” như một khuyến nghị đầu tư.
- Không hiển thị badge Binance như chứng nhận chất lượng.
- Không hiển thị trader `excluded` trong view mặc định; chỉ hiện khi bật “Include excluded”.
- Không hiển thị `pre_score` như thể là score chất lượng cuối cùng.

### 13.11. Checklist UI trước khi release

- [ ] Mọi chỉ số có tooltip định nghĩa + nguồn.
- [ ] Mọi chỉ số có cửa sổ thời gian.
- [ ] `N/A` không bị hiển thị là 0.
- [ ] Có empty state cho mọi màn hình.
- [ ] Có loading skeleton.
- [ ] Có error state + retry.
- [ ] Có data freshness toàn trang.
- [ ] Có “What’s missing”.
- [ ] Responsive 1280 / 1024 / 768.
- [ ] Không có chart nào không có dữ liệu thật.
- [ ] Không có màu đỏ cho `N/A`.
- [ ] Compare max 4.
- [ ] Filter count preview đúng.

---

## 14. KIỂM THỬ & QA

### 14.1. Test pyramid

| Tầng | Số lượng | Mục tiêu | Công cụ |
|---|---:|---|---|
| Unit | 60–80 | Công thức, normalize, scoring, parser | pytest |
| Contract | 15–25 | Schema endpoint, field, null, cap | pytest + respx |
| Integration | 15–20 | Collector → DB → API | pytest + test DB |
| E2E | 5–10 | Luồng người dùng | Playwright (optional) |
| Data quality | 10–15 | Null, duplicate, stale, anomaly | pytest + SQL |
| Performance | 5 | Shortlist ~700, dashboard | locust/k6 |
| Security | 5–10 | Auth, RBAC, secrets | manual + OWASP checklist |
| Recovery | 5 | Restart, backup, resume | manual script |

### 14.2. Golden dataset — 12 archetype

| # | Archetype | Đặc điểm | Kỳ vọng |
|---|---|---|---|
| 1 | Good low risk | ROI 30%, MDD 8%, Sharpe 1.8, 200 orders | Score cao |
| 2 | High return, high risk | ROI 200%, MDD 60%, lev 20x | Không top |
| 3 | High win rate, big loss | WR 90%, profit factor 0.5 | Không top |
| 4 | Martingale suspected | Size tăng sau lỗ | Risk flag |
| 5 | DCA suspected | Nhiều fill cùng hướng | Risk flag |
| 6 | Profit concentrated | 1 position chiếm 80% PnL | Risk flag |
| 7 | Missing data | Sharpe null, MDD null | Confidence thấp |
| 8 | Stale data | last collection 24h | Không top |
| 9 | ROI anomaly | ROI 7000%, MDD 1% | Flag kiểm tra |
| 10 | Stable | 12 tháng, positive months 75% | Consistency cao |
| 11 | Excluded — new | Runtime 4 ngày, ROI 59% | **Không deep fetch** |
| 12 | Excluded — no slots / no trade | Full slot, không trade 7D | **Không deep fetch** |

### 14.3. Regression fixture — trader thật

`5296057151807357697` — SIGNAL, ~4,1 ngày, ROI 61,75%, MDD 31,34%, Sharpe null, 5.292 fills, 8 positions.

**Kỳ vọng**
- `runtime_days` ~4.
- `roi_90d = 59.23`.
- `mdd_90d = 31.34`.
- `sharpe = null`.
- `win_rate_order = 50`.
- `position_win_rate = 62.5`.
- `profit_factor ~ 1.64`.
- `max_leverage = 15`.
- `worst_position_roi = -97.8`.
- `potential_tier = excluded`.
- `confidence < 0.4`.
- `score = null` hoặc bị loại khỏi ranking.
- Collector **không gọi** detail/position/trade cho trader này trong run bình thường.
- `risk_flags` chứa R03, R04, R06, R07, R08, R10, R11.

> Đây là test quan trọng nhất: hệ thống phải **không** xếp trader này vào top dù ROI 59%.

### 14.4. Unit test bắt buộc

**MDD**

```python
def test_mdd_basic():
    equity = [100, 120, 90, 110, 80]
    assert mdd(equity) == pytest.approx(33.333, rel=1e-3)
```

- MDD = (120 − 80) / 120 = 33.33%.

**Không tính MDD từ chartItems**

```python
def test_mdd_from_chart_items_not_used():
    chart = [54.66, 6.19, 59.23]
    with pytest.raises(ValueError):
        compute_mdd_from_roi_chart(chart)
```

Hoặc nếu vẫn cho phép, phải trả `estimated=True` và cảnh báo.

**Sharpe**
- < 30 observations → `None`.
- std = 0 → `None`.
- annualization đúng.

**Profit factor**
- Không có lỗ → `None`, không `inf`.
- < 5 positions → `low_sample=True`.

**WinRate**
- `total_orders = 0` → `None`, không 0.
- `win_orders > total_orders` → lỗi dữ liệu.

**Normalize & score**
- Missing component → renormalize.
- Tất cả missing → `None`.
- Direction đảo đúng.
- Percentile rank đúng cohort.

**Confidence**
- Runtime 4 ngày → history ~0.044.
- Sharpe null → coverage giảm.
- Freshness 24h → 0.

**Pre-filter & tier**

```python
def test_excluded_new_trader():
    assert tier_of(runtime_days=4, roi=59, pnl=583_000, ...) == "excluded"

def test_excluded_no_trade_7d():
    assert tier_of(traded_last_7d=False, ...) == "excluded"

def test_excluded_negative_roi():
    assert tier_of(roi=-5, ...) == "excluded"

def test_excluded_full_slots():
    assert tier_of(current_copy=200, max_copy=200, ...) == "excluded"

def test_excluded_low_aum():
    assert tier_of(aum=1_000, min_aum=5_000, ...) == "excluded"

def test_watch_valid():
    assert tier_of(runtime=45, roi=12, pnl=1000, wr=50, mdd=25, aum=8000, ...) == "watch"

def test_qualified_thresholds():
    assert tier_of(runtime=100, roi=12, wr=50, mdd=25, aum=15000, sharpe=0.8, orders=60) == "qualified"

def test_high_thresholds():
    assert tier_of(runtime=200, roi=25, wr=55, mdd=15, aum=25000, sharpe=1.2, orders=120) == "high"

def test_pre_score_missing_sharpe_neutral():
    assert pre_score(sharpe=None, ...) uses 50, not 0
```

### 14.5. Contract test

**List**
- `pageSize=30` → trả ≤ 30.
- `pageSize=100` → trả 30.
- `portfolioType=ALL` → có PUBLIC/SIGNAL/PRIVATE.
- `total` > 0.
- Mỗi item có 22 field.
- `chartItems` length = 90 cho 90D.

**Detail**
- `portfolioId` string, không number.
- Trả 67 field.
- `status` thuộc enum.
- Field null không bị parse thành 0.

**Performance**
- Dùng `BASE_P`, không phải `BASE_F`.
- 4 timeRange trả đúng.
- `winOrders <= totalOrder`.
- `sharpRatio` có thể null.

**Position history**
- `positionId` unique.
- `opened < closed`.
- `roi` có thể âm.
- `leverage > 0`.

**Trade history**
- `pageSize=200` → trả ≤ 200.
- `pageSize=500` → trả 200.
- Tổng fetch đủ `total`.
- `fee` có thể âm.
- Không có `trade_id` → hash ổn định.

**Transfer history**
- `transType` thuộc enum.
- `amount > 0`.
- Hash ổn định.

### 14.6. Integration test

**Collector → DB**
- Chạy 1 page list → insert đúng.
- Chạy pre-filter → `trader_universe` có tier + reasons.
- Chạy deep fetch → chỉ trader Watch/Qualified/High.
- Chạy lại → không duplicate.
- Chạy lại giữa chừng → resume.
- Raw JSON lưu nguyên vẹn.

**Quant**
- Từ raw mẫu → metrics đúng.
- Position/trade aggregate đúng.
- Không ghi đè snapshot cũ.

**Scoring**
- Config version 1 → score.
- Đổi config → version 2, score cũ giữ nguyên.
- Hard filter loại đúng.

**API**
- `/traders` filter/sort/pagination.
- `/traders/{id}` trả 404 nếu không có.
- `/compare` max 4.
- `/settings` chỉ admin.

**Frontend**
- Screener load shortlist ~700 → p95 < 1s.
- Filter → count đúng.
- Compare 4 trader → không vỡ.
- Empty state.
- Error state.

### 14.7. Data quality test

| Test | Kỳ vọng |
|---|---|
| Duplicate snapshot | Unique constraint chặn |
| Duplicate position | Unique `(portfolio_id, position_id)` |
| Duplicate trade | Hash unique |
| Null Sharpe | Không chấm 0 |
| Zero copyAum | Không coi là missing |
| Stale > 150 phút | Flag |
| Total list thay đổi | Dedupe, không crash |
| ChartItems flow | Không dùng tính MDD |
| ROI 7000% | Flag anomaly, không auto reject |
| WinRate 100% + 5 orders | Low sample |
| Pre-filter counts | Watch ~515, Qualified ~109, High ~13 (snapshot 06/11) |
| Excluded không bị deep fetch | Không có request detail/position/trade |
| False negative | Sample 50 excluded, < 5% thực sự đủ điều kiện |
| Tier thay đổi | Trader chuyển tier khi đủ ngày/order |
| Pre-score missing Sharpe | Dùng 50 neutral, không 0 |

**Query kiểm tra định kỳ**

```sql
-- duplicate snapshot
SELECT lead_portfolio_id, collected_hour, count(*)
FROM portfolio_snapshots
GROUP BY 1,2 HAVING count(*) > 1;

-- trader thiếu performance
SELECT t.lead_portfolio_id
FROM traders t
LEFT JOIN performance_metrics p
  ON p.lead_portfolio_id = t.lead_portfolio_id
 AND p.time_range = '90D'
WHERE p.id IS NULL;

-- stale
SELECT count(*) FROM traders
WHERE last_collected_at < now() - interval '150 minutes';
```

### 14.8. Performance test

| Kịch bản | Mục tiêu |
|---|---|
| `GET /traders?page=1&page_size=50` | p95 < 500ms |
| `GET /traders` shortlist ~700 + filter | p95 < 1s |
| `GET /traders/{id}` | p95 < 300ms |
| Dashboard overview | p95 < 1s |
| Screener render 100 rows | < 1s |
| Scan 11.124 list (90D) | < 5 phút (thực đo Phase 0: 78s) |
| Deep fetch ~515 performance | < 5 phút (chưa đo đủ) |
| Deep fetch ~109–313 detail/positions | < 10 phút (chưa đo) |
| Full trade history ~13 trader | < 5 phút (chưa đo) |
| 1 chu kỳ đầy đủ | < 15 phút |

### 14.9. Security checklist

- [ ] Password hash Argon2id/bcrypt ≥ 12.
- [ ] JWT access 15 phút, refresh 7 ngày, rotate.
- [ ] RBAC admin/viewer.
- [ ] API key AI mã hóa at rest.
- [ ] Không trả API key về browser.
- [ ] CORS chỉ domain frontend.
- [ ] Rate limit login 5/phút/IP.
- [ ] Rate limit API 100/phút/user.
- [ ] Audit log settings/scoring/risk.
- [ ] Không log token/password/API key.
- [ ] SQL parameterized.
- [ ] Không `dangerouslySetInnerHTML`.
- [ ] Dependency scan (`pip-audit`, `npm audit`).
- [ ] HTTPS + HSTS.
- [ ] Backup mã hóa.
- [ ] Không mở PostgreSQL ra internet.
- [ ] Không dùng API key Binance có quyền giao dịch.

### 14.10. Acceptance test toàn MVP

- [ ] Scan 11.124 trader PUBLIC + SIGNAL đủ ≥ 99%.
- [ ] Shortlist Watch nằm trong 400–700.
- [ ] Không có trader excluded nào bị deep fetch.
- [ ] Không duplicate sau 3 lần chạy.
- [ ] Restart giữa crawl không mất dữ liệu.
- [ ] Trader mẫu ra “Excluded”, không top, không deep fetch.
- [ ] MDD hiển thị = published, không phải 88,67%.
- [ ] Sharpe null hiển thị `N/A`, không 0.
- [ ] WinRate order và position hiển thị tách biệt.
- [ ] AUM và Copy AUM hiển thị tách biệt.
- [ ] Filter/sort/pagination đúng.
- [ ] Compare max 4.
- [ ] Settings tạo version, rollback được.
- [ ] AI không sửa score.
- [ ] Backup restore thành công.
- [ ] Không có secret trong repo.
- [ ] p95 API đạt mục tiêu.
- [ ] Có 3–5 beta user phản hồi.

## 15. DEPLOY, VẬN HÀNH & BẢO MẬT

### 15.1. Topology MVP

```text
Internet
  │
  ├─ 443/tcp ──► Nginx (TLS, HSTS, rate limit tầng edge)
  │                ├─ /            ──► frontend (static build / container)
  │                └─ /api/v1      ──► FastAPI (uvicorn/gunicorn)
  │                                        ├─ PostgreSQL 16 (không mở internet)
  │                                        ├─ Redis (cache + lock + rate limit)
  │                                        └─ worker/scheduler (collector, quant, AI)
  └─ 22/tcp  ──► SSH (chỉ IP admin, key-only, không password)
```

| Thành phần | MVP | Ghi chú |
|---|---|---|
| VPS | 4 vCPU / 8 GB RAM / 100 GB SSD | Đủ cho 11k trader, raw JSONL tăng dần |
| OS | Ubuntu 24.04 LTS | Cập nhật bảo mật định kỳ |
| Runtime | Docker Compose | Đơn giản, đủ cho 1 node |
| Reverse proxy | Nginx | TLS, HSTS, giới hạn body, timeout |
| DB | PostgreSQL 16 | Volume riêng, backup ra ngoài |
| Cache/lock | Redis 7 | Tránh 2 collector chạy song song |
| Process | 1 API + 1 worker + 1 scheduler | Tách process, không chạy trong API |
| Tên miền | 1 domain + 1 subdomain API | Bắt buộc HTTPS |

**Không dùng Kubernetes, message queue, microservice trong MVP.** Một node + Compose là đủ và giảm bề mặt lỗi.

### 15.2. Biến môi trường

`.env.example` (không commit `.env` thật):

```dotenv
# App
APP_ENV=production
APP_BASE_URL=https://example.com
API_BASE_URL=https://api.example.com
LOG_LEVEL=INFO

# Database
POSTGRES_DB=copytrade
POSTGRES_USER=copytrade
POSTGRES_PASSWORD=<random-32+>
DATABASE_URL=postgresql+psycopg://copytrade:<password>@db:5432/copytrade

# Cache / lock
REDIS_URL=redis://redis:6379/0

# Auth
JWT_SECRET=<random-64>
JWT_ACCESS_TTL_MIN=15
JWT_REFRESH_TTL_DAYS=7
ADMIN_EMAIL=admin@example.com
ADMIN_INITIAL_PASSWORD=<random>

# Collector
BAPI_BASE_URL=https://www.binance.com
BAPI_CONCURRENCY=6
BAPI_TIMEOUT_SECONDS=20
BAPI_MAX_RETRIES=4
COLLECTOR_KILL_SWITCH=false

# AI (optional)
AI_PROVIDER=openai
AI_API_KEY=<encrypted-at-rest>
AI_MODEL=<model-id>
AI_MONTHLY_BUDGET_USD=20

# Ops
SENTRY_DSN=
BACKUP_DIR=/backups
```

**Quy tắc:** mọi secret chỉ nằm trong `.env`/secret store; không hardcode; không trả về browser; `.env` nằm trong `.gitignore`.

### 15.3. Quy trình deploy

| Bước | Lệnh/hành động | Kiểm tra |
|---:|---|---|
| 1 | Pull code/tag đã review | `git log -1` đúng commit |
| 2 | Build image | `docker compose build` |
| 3 | Backup DB trước migrate | `pg_dump -Fc` thành công |
| 4 | Chạy migration | `alembic upgrade head` |
| 5 | Restart API/worker | `docker compose up -d` |
| 6 | Health check | `/health` = 200, DB/Redis OK |
| 7 | Smoke test | login, `/traders?page_size=10`, detail 1 trader |
| 8 | Theo dõi 15 phút | 5xx < 1%, p95 < 2s |
| 9 | Ghi log deploy | thời điểm, version, người deploy |

**Rollback:** giữ image của bản trước; rollback = deploy lại image cũ + migration down nếu đã có. Không rollback DB nếu migration phá dữ liệu — thay vào đó restore backup đã kiểm tra.

### 15.4. Lịch chạy & tần suất

| Job | Tần suất | Timeout | Ghi chú |
|---|---|---|---|
| List scan PUBLIC + SIGNAL (90D) | 60 phút | 10 phút | ~78s thực đo Phase 0 |
| Performance 4 window cho Watch | 6 giờ | 15 phút | ~515 trader |
| Detail/positions/transfers cho Qualified + top Watch | 12 giờ | 30 phút | ~109–313 trader |
| Full trade history cho High + top Qualified | 24 giờ | 30 phút | ~13–50 trader |
| Quant + scoring + ranking snapshot | sau mỗi deep fetch | 10 phút | version hóa config |
| AI report theo yêu cầu | on-demand + cooldown | 60s/report | budget ngày/tháng |
| Backup DB | 02:00 UTC | 15 phút | giữ 7 daily + 4 weekly |
| Data quality check | 03:00 UTC | 5 phút | query mục 14.7 |
| Restore test | hàng tháng | — | môi trường staging |

**Nguyên tắc:** list scan nhẹ và thường xuyên; deep fetch nặng và thưa; không bao giờ deep fetch trader `Excluded`.

### 15.5. Backup & restore

```bash
# Backup
pg_dump -Fc "$DATABASE_URL" -f "/backups/copytrade_$(date +%F).dump"

# Restore (staging trước)
pg_restore --clean --if-exists -d "$DATABASE_URL" /backups/copytrade_YYYY-MM-DD.dump
```

- Giữ **7 daily + 4 weekly**, mã hóa at rest, copy ra ngoài VPS.
- Raw JSONL sync daily; có thể rebuild DB từ raw nếu cần.
- **Test restore hàng tháng**, ghi lại thời gian và kết quả.
- Không backup lên cùng volume với DB.

### 15.6. Monitoring & alert

| Metric | Ngưỡng cảnh báo | Kênh |
|---|---|---|
| Collector success | fail 2 lần liên tiếp | Email/Telegram |
| Data freshness | > 150 phút | Email/Telegram |
| API 5xx | > 1% trong 5 phút | Email |
| API p95 | > 2s trong 10 phút | Email |
| Disk | > 80% | Email |
| RAM | > 85% trong 10 phút | Email |
| DB connections | > 80% pool | Email |
| AI cost | > 80% budget | Email |
| Backup | không có file trong 26 giờ | Email |

**Log:** structured JSON, có `request_id`, `job_id`, `lead_portfolio_id`; **không log** token, password, API key, full header Authorization.

### 15.7. Runbook sự cố

| Sự cố | Dấu hiệu | Hành động |
|---|---|---|
| BAPI 403/404 | tất cả request fail | Kiểm tra path/header; dừng collector; bật adapter CSV/Demo; không xóa dữ liệu cũ |
| Rate limit `11012005` | 429/ lỗi tăng vọt | Giảm concurrency, tăng backoff, chờ; không retry dồn dập |
| List total giảm mạnh | total < 80% trung bình 7 ngày | Coi là bất thường API; giữ snapshot cũ; alert |
| DB đầy | disk > 80% | Archive/partition snapshot cũ; tăng disk; không xóa raw đột ngột |
| Collector treo | không có log mới | Kill worker, chạy lại từ JSONL checkpoint |
| API chậm | p95 > 2s | Kiểm tra query/index, cache, connection pool |
| AI lỗi | timeout/JSON invalid | Tắt AI, dùng fallback template; hệ thống vẫn chạy |
| Score bất thường | top thay đổi hàng loạt | So sánh `scoring_config_version`; rollback version |
| Data stale | freshness > 150 phút | Chạy collector thủ công; kiểm tra network/nguồn |
| Nghi lộ secret | log/scan cảnh báo | Rotate JWT/API key/DB password; audit access log |

### 15.8. Security checklist (MVP)

- [ ] Password hash Argon2id hoặc bcrypt cost ≥ 12.
- [ ] JWT access 15 phút, refresh 7 ngày, rotate refresh token.
- [ ] RBAC `admin` / `viewer`; kiểm tra quyền ở server, không chỉ ẩn UI.
- [ ] API key AI mã hóa at rest (KMS/secret store hoặc mã hóa ứng dụng).
- [ ] Không trả API key về browser; chỉ hiển thị trạng thái “đã cấu hình”.
- [ ] CORS chỉ domain frontend; không `*` ở production.
- [ ] Rate limit login 5/phút/IP; API 100/phút/user.
- [ ] Audit log cho thay đổi settings/scoring/risk và hành động admin.
- [ ] Không log token/password/API key.
- [ ] SQL parameterized / ORM; không nối chuỗi SQL từ input.
- [ ] Không `dangerouslySetInnerHTML` với nội dung AI/người dùng.
- [ ] Dependency scan (`pip-audit`, `npm audit`) trong CI.
- [ ] HTTPS + HSTS; redirect HTTP → HTTPS.
- [ ] Backup mã hóa; quyền file hạn chế.
- [ ] PostgreSQL/Redis không mở port ra internet.
- [ ] SSH key-only, tắt root login, firewall chỉ 22/80/443.
- [ ] Không dùng API key Binance có quyền giao dịch (hệ thống không cần).
- [ ] Content Security Policy cơ bản; security headers (`X-Content-Type-Options`, `Referrer-Policy`, `frame-ancestors`).

### 15.9. Vận hành dữ liệu

| Việc | Quy tắc |
|---|---|
| Raw archive | JSONL append-only, nén sau 7 ngày, giữ tối thiểu 90 ngày |
| Snapshot list | Giữ theo giờ; rollup/aggregate sau 30 ngày nếu cần |
| Trade/transfer | Giữ theo trader; hash unique chống trùng |
| Xóa theo yêu cầu | Có quy trình xóa dữ liệu liên quan trader/người dùng |
| Provenance | Mỗi bản ghi có `source`, `collected_at`, `endpoint`, `window` |
| Rebuild | Có script rebuild DB từ raw archive trên môi trường staging |

### 15.10. Tài liệu vận hành bắt buộc

- [ ] `docs/runbook.md` — sự cố, restart, rollback, escalation.
- [ ] `docs/deployment.md` — VPS, Nginx, TLS, cron, biến môi trường.
- [ ] `docs/api.md` — OpenAPI + ví dụ request/response.
- [ ] `docs/data-quality.md` — định nghĩa flag + query kiểm tra.
- [ ] `docs/security.md` — checklist, chính sách secret, quy trình rotate.
- [x] `SESSION.md` — nhật ký quyết định và việc còn lại (đã có, cập nhật mỗi phase).

### 15.11. Chi phí vận hành ước tính

| Khoản | Tháng | Ghi chú |
|---|---:|---|
| VPS 4 vCPU/8 GB | 20–40 USD | Tùy nhà cung cấp |
| Domain + TLS | ~1 USD | Let's Encrypt miễn phí |
| Backup storage | 5–10 USD | 100–200 GB |
| AI (tùy chọn) | 0–20 USD | Có budget cứng |
| Monitoring | 0–15 USD | Có thể dùng self-host |
| **Tổng** | **~25–85 USD** | Chưa tính thời gian dev |

---

## 16. RỦI RO, PHÁP LÝ & PHƯƠNG ÁN DỰ PHÒNG

### 16.1. Rủi ro nguồn dữ liệu

BAPI copy-trading **không phải API chính thức** trong Binance Developer Docs.

| Yếu tố | Thực tế | Hệ quả |
|---|---|---|
| Tài liệu | Không có tài liệu chính thức, không cam kết version | Field/path có thể đổi bất kỳ lúc nào |
| Xác thực | Không cần auth cho endpoint đang dùng | Dễ gọi nhưng dễ bị chặn |
| Ổn định | Đã đổi path/field trong quá khứ | Collector phải chịu lỗi và cảnh báo |
| Rate limit | Có, mã `11012005` | Cần backoff + concurrency thấp |
| Chặn IP/vùng | Có thể | Cần kill switch + phương án dự phòng |
| ToS | Vẫn áp dụng dù dữ liệu công khai | Không được mặc định “công khai = được phép” |
| 6 endpoint không có | positions, copier-list, funding-history, funding-fee (404) | Không thiết kế tính năng phụ thuộc |

**Kết luận:** coi BAPI là nguồn **có thể mất bất kỳ lúc nào**. Adapter + raw archive + kill switch là bắt buộc, không phải “nice to have”.

### 16.2. Rủi ro dữ liệu (đã kiểm chứng bằng Phase 0)

| Rủi ro | Bằng chứng thực tế | Giảm thiểu |
|---|---|---|
| **Flow distortion** | Tính MDD từ `chartItems` ra 88,67%; dùng `equity = 1 + ROI/100` ra 31,3384%, khớp published | Hiển thị `performance.mdd`; tự tính chỉ để audit, ghi “estimated” |
| **Null ≠ 0** | Sharpe null **34,9%** | Renormalize + confidence; UI hiển thị `N/A` |
| **Zero ≠ missing** | copyAum zero **63,3%**, currentCopyCount zero **74,2%**, copierPnl zero **65,4%** | Hiển thị “không có copier”, không phải `N/A` |
| **Window confusion** | ROI 7D/30D/90D/180D khác nhau rõ rệt | Luôn ghi cửa sổ cạnh chỉ số |
| **Portfolio mới** | Trader 4 ngày tuổi có 4 window giống nhau | Hard filter runtime ≥ 30/90/180 |
| **WinRate definition** | 50% theo order vs 62,5% theo position | Hiển thị cả hai, nhãn rõ |
| **AUM misleading** | AUM lớn nhưng copyAum nhỏ | Hiển thị AUM và Copy AUM tách biệt |
| **Lead PnL vs Copier PnL** | 583k vs 1k | Hiển thị cả hai, không gộp |
| **Fake/test profile** | Nickname mặc định, mô tả bất thường | Data quality flag, không auto top |
| **ROI cực cao** | 7.069% ROI, MDD 1,52% | Anomaly flag, không auto reject/top |
| **Sample nhỏ** | 5–10 order | Low sample badge + confidence thấp |
| **Trade pagination** | 5.292 fill, 200/page | Fetch đủ `total`, không break sớm |
| **List fluctuation** | total thay đổi giữa các trang/ngày | Dedupe theo ID, snapshot, log partial |
| **chartItems cố định** | Luôn đúng 90 điểm cho cả 11.124 trader | Không dùng làm MDD/equity chính thức |
| **`aiSummary` thiếu** | null **98,3%** | Không phụ thuộc; chỉ hiển thị khi có |
| **`badge` thiếu** | null **99,8%** | Không dùng làm tín hiệu chính |
| **Tier drift** | Trader đổi tier khi đủ ngày/order | Lưu lịch sử tier; chỉ đổi khi vượt ngưỡng rõ |

### 16.3. Rủi ro sản phẩm

| Rủi ro | Hậu quả | Giảm thiểu |
|---|---|---|
| Người dùng chase ROI | Chọn trader rủi ro cao | Score tổng hợp + risk flags; không có bảng “High Return” |
| Dashboard quá nhiều số | Không ra quyết định | 10 chỉ số cốt lõi; phần còn lại trong “xem thêm” |
| AI bịa | Mất niềm tin | Evidence IDs + JSON schema + fallback template |
| Scoring bị game | Trader tối ưu chỉ số | Percentile + hard filter + review định kỳ |
| AUM hiểu sai | Đánh giá sai độ phổ biến | CopyAum + số copier riêng |
| Paper Copy giả chính xác | Người dùng tin sai | Cắt khỏi MVP (D03) |
| Cấu hình web phá hệ thống | Ranking sai | Version + validation + audit + rollback |
| Quá nhiều tính năng | Trễ | Quyết định khóa D01–D30 |
| Người dùng hiểu “Excluded” là xấu | Bỏ qua trader tiềm năng | Giải thích lý do + “what’s missing” |
| So sánh correlation gây hiểu nhầm | Ra quyết định phân bổ sai | Ghi rõ “estimated”, không dùng cho sizing |

### 16.4. Rủi ro vận hành & kỹ thuật

| Rủi ro | Ảnh hưởng | Giảm thiểu |
|---|---|---|
| BAPI đổi/block | Trễ 1–2 tuần | Adapter + CSV/Demo fallback + raw archive |
| Rate limit nặng | Crawl chậm/không xong | 6–8 worker, backoff, cache, scan theo tầng |
| DB phình do snapshot | Disk đầy | Partition/rollup, retention, nén raw |
| Collector chạy trùng | Duplicate/race | Redis lock + unique constraint |
| Restart giữa crawl | Mất dữ liệu | JSONL append-only + checkpoint + idempotent upsert |
| Secret lộ | Mất tài khoản/chi phí | Secret store, rotate, scan CI, không log |
| AI cost vượt | Tốn tiền | Budget cứng + cooldown + manual default |
| Một dev ốm/bận | Trễ | Buffer 20% + task nhỏ + tài liệu hóa |
| Thiếu test regression | Sửa chỗ này hỏng chỗ khác | Golden dataset + contract test |

### 16.5. Phương án dự phòng nếu BAPI chết

| Phương án | Mô tả | Ưu điểm | Nhược điểm | Khi nào dùng |
|---|---|---|---|---|
| **A — CSV Import** | Người dùng export/nhập CSV theo schema chuẩn | Hợp pháp, ổn định | Coverage thấp, thủ công | BAPI chết nhưng vẫn muốn giữ sản phẩm |
| **B — Demo/Synthetic** | Golden dataset 12 archetype (gồm 2 excluded) | Không phụ thuộc mạng, test UI/scoring | Không có giá trị sản phẩm thật | Phát triển UI, demo nội bộ |
| **C — Chuyển hướng** | Trade journal cá nhân từ API key read-only của người dùng | Hợp pháp hơn | Không còn là copy-trading discovery | BAPI/ToS không cho phép |
| **D — Đàm phán** | Xin quyền truy cập chính thức/đối tác Binance | Bền vững nhất | Thời gian dài, không hợp MVP | Sau khi có traction |

**Khuyến nghị:** triển khai `BinanceBapiAdapter`, `CsvImportAdapter`, `DemoAdapter` ngay từ Phase 1–2. Không để UI/quant/scoring phụ thuộc cứng vào BAPI.

### 16.6. Kill criteria

Dừng hoặc pivot nếu bất kỳ điều kiện nào đúng:

- [ ] Không lấy được list/detail ổn định sau 5 ngày thử.
- [ ] BAPI chặn IP thường xuyên, không thể crawl 1 chu kỳ trong 60 phút.
- [ ] Kết luận pháp lý: không được phép dùng cho sản phẩm công khai.
- [ ] Dữ liệu thiếu đến mức không tính được 10 chỉ số cốt lõi.
- [ ] Pre-filter false negative > 10% (đã đo Phase 0: **0%** ở gate `fn_watch_eligible`).
- [ ] Không có nguồn thay thế trong 2 tuần.
- [ ] Chi phí vận hành vượt 3× dự toán mà không có người dùng trả tiền.

### 16.7. Disclaimer mẫu

> **Miễn trừ trách nhiệm**  
> Đây là công cụ phân tích dữ liệu công khai, **không phải tư vấn đầu tư**, không phải khuyến nghị mua/bán, không đảm bảo lợi nhuận. Dữ liệu có thể sai, thiếu hoặc bị thay đổi bởi nguồn cung cấp. Người dùng tự chịu trách nhiệm với quyết định của mình. Copy trading có rủi ro mất toàn bộ vốn.

Đặt disclaimer tại:

- Footer mọi trang.
- Đầu/cuối AI report.
- Trong API docs và response metadata (field `disclaimer`).
- Trong onboarding/email nếu có.
- Trong README và landing page.

### 16.8. Checklist pháp lý trước khi public

- [ ] Đọc lại ToS Binance tại thời điểm launch.
- [ ] Không dùng logo/nhãn Binance như chứng nhận hay đối tác.
- [ ] Có disclaimer rõ ràng trên UI/API/AI report.
- [ ] Không bán raw data.
- [ ] Không cung cấp tín hiệu đầu tư cá nhân hóa.
- [ ] Có chính sách xóa dữ liệu theo yêu cầu.
- [ ] Có privacy policy nếu lưu email người dùng.
- [ ] Kiểm tra quy định địa phương về crypto/copy trading.
- [ ] Có kill switch dữ liệu (tắt collector 1 config).
- [ ] Có log nguồn dữ liệu (provenance) cho mọi chỉ số.
- [ ] Không lưu API key giao dịch của người dùng.
- [ ] Hợp đồng/điều khoản sử dụng nêu rõ giới hạn trách nhiệm.

### 16.9. Data provenance & attribution

Mọi bản ghi chỉ số phải trả kèm:

| Field | Ví dụ | Mục đích |
|---|---|---|
| `source` | `binance_bapi` | Biết nguồn |
| `endpoint` | `/bapi/futures/v1/friendly/...` | Debug/audit |
| `window` | `90D` | Tránh nhầm cửa sổ |
| `collected_at` | `2026-11-06T16:34:00Z` | Freshness |
| `published` | `true/false` | Phân biệt published vs derived |
| `confidence` | `0.82` | Độ tin cậy |
| `flags` | `["low_sample","high_mdd"]` | Cảnh báo |

### 16.10. Ma trận rủi ro

| Rủi ro | Khả năng | Tác động | Ưu tiên | Chủ sở hữu |
|---|---|---|---|---|
| BAPI đổi/block | Trung bình | Cao | **P0** | Backend |
| Rate limit khi deep fetch | Trung bình | Trung bình | P1 | Backend |
| Sai lệch MDD/flow | Đã từng xảy ra | Cao | **P0** | Quant |
| Null bị hiển thị 0 | Cao nếu không test | Cao | **P0** | Full-stack |
| Pre-filter bỏ sót trader tốt | Thấp (đo 0%) | Cao | P1 | Quant |
| AI hallucination | Trung bình | Trung bình | P1 | Backend |
| Rò rỉ secret | Thấp | Rất cao | **P0** | DevOps |
| Scope creep | Cao | Trung bình | P1 | Product |
| Chi phí AI vượt | Trung bình | Thấp | P2 | Backend |
| Thiếu người review | Cao (1 dev) | Trung bình | P2 | Product |

---

## 17. LỘ TRÌNH & CHECKLIST CÔNG VIỆC

> **Đã chuyển sang [`TASKS.md`](./TASKS.md).**
>
> `TASKS.md` là checklist thực thi duy nhất: Phase 0 (đã xong, giữ nguyên) + Phase 1–6 + Backlog + Non-goals.
> Mỗi bước trong `TASKS.md` có kèm **mục + khoảng dòng** trong file này để tra cứu nhanh.
>
> Quy ước trạng thái và quy tắc cập nhật: xem mục 22.4.

---

## 18. BACKLOG v1.1

Chỉ làm sau khi MVP ổn định ≥ 2 tuần và có phản hồi beta. Ưu tiên theo **giá trị người dùng / công sức**.

| # | Tính năng | Giá trị | Công sức | Phụ thuộc | Ưu tiên |
|---|---|---|---:|---|---|
| B01 | Watchlist + alert trong web | Cao | Trung bình | Auth, notification | P1 |
| B02 | Lịch sử ranking theo thời gian | Cao | Trung bình | `ranking_snapshots` | P1 |
| B03 | Export PDF báo cáo trader/compare | Trung bình | Thấp | Template | P1 |
| B04 | Benchmark ETH/SOL | Trung bình | Thấp | Dữ liệu giá | P2 |
| B05 | AI report nâng cao: so sánh 2 report, phản biện | Trung bình | Trung bình | AI adapter | P2 |
| B06 | Correlation/portfolio allocator nâng cao | Trung bình | Cao | Dữ liệu đủ dài | P2 |
| B07 | Cải thiện phát hiện DCA/martingale | Cao | Cao | Trade history đủ sâu | P1 |
| B08 | Paper Copy (chỉ khi dữ liệu đủ tốt, ghi “estimated”) | Trung bình | Cao | Fill/slippage data | P3 |
| B09 | Email digest tuần | Trung bình | Thấp | Email service | P2 |
| B10 | Saved view chia sẻ bằng link | Trung bình | Thấp | Saved views | P2 |
| B11 | API public cho người dùng trả tiền | Cao (doanh thu) | Trung bình | Auth/rate limit | P2 |
| B12 | Per-copier analytics | Cao | Rất cao | Không có API | P3 |
| B13 | Open positions realtime | Cao | Không khả thi | Không có endpoint | — |
| B14 | Funding drag chính xác | Trung bình | Cao | Không có funding trong trade | P3 |
| B15 | Telegram bot tra cứu nhanh | Trung bình | Trung bình | API | P2 |
| B16 | Đa ngôn ngữ (EN/VI) | Trung bình | Trung bình | i18n | P2 |
| B17 | Custom scoring profile cho từng user | Trung bình | Cao | Config version | P3 |
| B18 | Mobile app | Thấp (MVP web đủ) | Rất cao | — | P3 |

**Quy tắc:** không bắt đầu B01–B18 khi còn `[!]` blocker ở mục 20 hoặc khi MVP chưa đạt acceptance mục 14.10.

---

## 19. VIỆC KHÔNG LÀM (NON-GOALS)

### 19.1. Trong MVP

| Không làm | Lý do |
|---|---|
| Auto copy / đặt lệnh Binance | Rủi ro pháp lý và tài chính; cần API key giao dịch |
| Realtime WebSocket | Không cần cho quyết định 60 phút/lần; tăng độ phức tạp |
| Paper Copy | Không đủ dữ liệu mô phỏng trung thực; tạo cảm giác chính xác giả |
| Deep fetch toàn bộ 11k trader | Phần lớn không có tiềm năng; tốn request/thời gian |
| Per-copier analytics | Không có API public |
| Open positions | Không có endpoint (404) |
| Funding drag chính xác | Không có funding trong trade-history |
| Copy fill rate / slippage | Cần tài khoản copier |
| Telegram bot / mobile app | Giữ hệ thống gọn |
| 6 bảng ranking | Giảm còn 3 bảng có ý nghĩa |
| Strategy labels tự động | Chỉ heuristic “suspected”, không khẳng định |
| Bán raw data | Rủi ro pháp lý |
| Dùng logo Binance như chứng nhận | Rủi ro pháp lý |
| Tư vấn đầu tư cá nhân hóa | Ngoài phạm vi công cụ phân tích |
| Multi-tenant / team workspace | Một admin + viewer là đủ MVP |
| Kubernetes/microservice | Over-engineering cho 1 node |

### 19.2. Không bao giờ (trừ khi đổi định vị sản phẩm)

- Hứa hẹn lợi nhuận hoặc “trader an toàn”.
- Hiển thị số liệu bịa khi thiếu dữ liệu.
- Chấm điểm 0 cho `null`.
- Để AI sửa score/ranking.
- Bán hoặc tái phân phối raw data.
- Dùng API key có quyền giao dịch của người dùng.

---

## 20. CÂU HỎI MỞ & QUYẾT ĐỊNH CẦN CHỐT

Các mục dưới đây **chưa được khóa**; cần quyết định trước phase tương ứng.

| ID | Câu hỏi | Lựa chọn | Khuyến nghị | Deadline | Trạng thái |
|---|---|---|---|---|---|
| Q01 | `mdd=None` xử lý thế nào? | (a) fail gate Qualified/High; (b) pass + flag | **(a) + flag cho Watch** | Trước Phase 2 | `[!]` |
| Q02 | `pre_score` percentile theo cohort nào? | (a) gộp PUBLIC+SIGNAL; (b) theo type | **(a) MVP**, ghi tooltip | Trước Phase 3 | `[!]` |
| Q03 | Preset AUM mặc định | 1k / 5k / 10k / 20k | **5k (D22)** | Đã chốt | `[x]` |
| Q04 | Mô hình kinh doanh | Free beta / subscription / API trả phí | Free beta → subscription sau | Trước Phase 6 | `[ ]` |
| Q05 | Auth tự host hay OAuth | Email/password JWT / Google OAuth | **Email/password JWT** cho MVP | Phase 1 | `[ ]` |
| Q06 | AI provider/model | OpenAI/Anthropic/local | Provider rẻ + JSON mode; dễ đổi adapter | Phase 5 | `[ ]` |
| Q07 | Retention raw JSONL | 30/90/180 ngày | **90 ngày**, nén sau 7 ngày | Phase 2 | `[ ]` |
| Q08 | Có hiển thị MDD tự tính không? | Ẩn / hiện “estimated” cạnh published | **Hiện trong audit panel**, không dùng ranking | Phase 3 | `[ ]` |
| Q09 | SIGNAL có bị giảm trọng số? | Có / không | **Không** trong MVP; theo dõi riêng | Phase 3 | `[ ]` |
| Q10 | Pháp nhân/khu vực vận hành | VN / offshore / khác | Tư vấn pháp lý trước public | Trước Phase 6 | `[!]` |
| Q11 | Có lưu email/PII người dùng? | Có / không | Chỉ email nếu có auth; có privacy policy | Phase 1 | `[ ]` |
| Q12 | Có mở API public? | Không / có | **Không** trong MVP | Sau MVP | `[x]` |
| Q13 | Ngưỡng tier cấu hình runtime? | Hardcode / config DB | **Config DB + version** (D15) | Phase 3 | `[ ]` |
| Q14 | Trader < 30 ngày nhưng ROI cao | Bỏ / Watch-only | **Watch-only + audit** | Đã chốt | `[x]` |
| Q15 | “Qualified” dùng cho ranking hay chỉ filter? | Cả hai / chỉ filter | **Chỉ filter**; ranking theo score | Phase 3 | `[ ]` |
| Q16 | Có benchmark BTC/ETH trong MVP? | Có / không | **Không**, để v1.1 (B04) | Đã cắt | `[x]` |
| Q17 | Có lưu lịch sử tier? | Có / không | **Có** `tier_history` | Phase 2 | `[ ]` |
| Q18 | Xử lý trader đổi tên/avatar | Update / giữ history | Update + giữ snapshot cũ | Phase 2 | `[ ]` |
| Q19 | Có cần đa ngôn ngữ MVP? | VI / VI+EN | **VI**, EN ở v1.1 | Đã cắt | `[x]` |
| Q20 | Có dùng CDN/Cloudflare? | Có / không | Khuyến khích để giảm tải/TLS | Phase 6 | `[ ]` |

**Cách chốt:** mỗi quyết định ghi vào bảng trên + thêm dòng vào `08-nhat-ky-quyet-dinh.md` và `SESSION.md`. Quyết định đã chốt chuyển `[x]`; nếu thay đổi quyết định cũ, ghi rõ “supersedes Dxx”.

---

## 21. VIỆC CẦN LÀM NGAY

### 21.1. 24–48 giờ tới (đóng Phase 0)

| # | Việc | Đầu ra/bằng chứng | Ước lượng |
|---:|---|---|---:|
| 1 | Sửa `summarize_tiers()` đọc fallback `reasons` → `tier_reasons` | `tier_summary.csv` có reason > 0; test so với `scan_summary.json` | 30–60 phút |
| 2 | Chốt `mdd=None`: đề xuất fail Qualified/High, Watch + flag | Quyết định ghi vào mục 20 (Q01) + code + test | 30 phút |
| 3 | Chốt cohort `pre_score`: đề xuất gộp cho MVP | Quyết định Q02 + tooltip copy | 15 phút |
| 4 | Cập nhật `SESSION.md` | Nhật ký D01–D30 + trạng thái + việc còn lại | 30 phút |
| 5 | Sửa `.gitignore` từ `phase0/` → `phase0/data/` | `git status` thấy script, không thấy raw lớn | 10 phút |
| 6 | Khởi tạo git repo + commit baseline | Commit đầu tiên, `git log` sạch | 15 phút |
| 7 | Cập nhật `02-data-contract-binance.md` | Số 11.124/515/109; bỏ claim `positionShow` | 30 phút |
| 8 | Thêm `requirements.txt` + pytest cho `tiering.py` | `pytest` xanh với ≥ 8 test tier/pre_score | 1–2 giờ |
| 9 | Ghi rõ “63 bundle là ngoại lệ được chấp thuận” trong report | Report/acceptance cập nhật | 5 phút |
| 10 | Tạo issue/backlog cho full-scale timing | Issue “Measure 515/109–313 deep fetch” | 10 phút |

**Định nghĩa đóng Phase 0:** 10 việc trên xong, `pytest` xanh, `tier_summary.csv` có reason, 2 quyết định `[!]` chuyển `[x]`.

### 21.2. Tuần 1 (khởi động Phase 1)

| # | Việc | Đầu ra |
|---:|---|---|
| 1 | Tạo `backend/`, `frontend/`, `docker-compose.yml`, `.env.example` | `docker compose up` chạy |
| 2 | PostgreSQL + Alembic migration đầu tiên | 4 bảng lõi + downgrade được |
| 3 | FastAPI skeleton + `/health` + logging | `/health` trả DB/Redis OK |
| 4 | React + Vite + TS + Tailwind + layout | Trang trống có sidebar/topbar |
| 5 | Auth login/JWT/RBAC | Admin + viewer đăng nhập được |
| 6 | `DemoAdapter` + seed 2 trader | 1 excluded + 1 qualified |
| 7 | API `/traders/{id}` | Trả đủ 10 chỉ số + provenance |
| 8 | Trang Trader Detail tối giản | Hiển thị tier/lý do excluded |
| 9 | CI lint + typecheck + test | Pipeline xanh trên commit |
| 10 | `SESSION.md` cập nhật | Quyết định Phase 1 |

### 21.3. Trước khi viết code backend đầu tiên

- [ ] Schema `traders`, `portfolio_snapshots`, `performance_metrics`, `users` đã vẽ ERD.
- [ ] Quy ước null/zero đã chốt (null = thiếu, zero = có giá trị 0).
- [ ] Quy ước timezone: lưu UTC, hiển thị theo locale.
- [ ] Quy ước ID: dùng `lead_portfolio_id` dạng text/bigint thống nhất.
- [ ] Quy ước window: `7D/30D/90D/180D` là enum, không string tự do.
- [ ] Quy ước version: `scoring_config_version` bắt buộc trên mọi score.
- [ ] Đã có golden dataset 12 archetype (kể cả 2 excluded).
- [ ] Đã có fixture trader thật `5296057151807357697`.

### 21.4. Lệnh kiểm tra nhanh (Phase 0)

```bash
# Tái tạo summary không gọi mạng
python phase0/recompute_summary.py

# Quét lại universe (tốn ~80s, 371 trang)
python phase0/scan_universe.py --preset balanced --types PUBLIC,SIGNAL --time-range 90D

# Chọn mẫu stratified
python phase0/sample.py

# Deep fetch mẫu (resume mặc định)
python phase0/deep_fetch.py

# Audit false negative 50 excluded
python phase0/audit_excluded.py --n 50

# Kiểm chứng proxy hoạt động 7D
python phase0/activity_check.py

# Đo rate limit
python phase0/rate_limit_test.py

# Kiểm chứng 7 nhóm chỉ số
python phase0/indicator_checks.py
```

**Lưu ý:** các lệnh trên gọi BAPI thật; không chạy song song nhiều process; giữ 5–6 worker.

### 21.5. Mẫu ghi quyết định

```markdown
### Dxx — <tên quyết định>
- Ngày: YYYY-MM-DD
- Bối cảnh: <vấn đề>
- Lựa chọn: <A/B/C>
- Quyết định: <chọn gì>
- Lý do: <dữ liệu/bằng chứng>
- Hệ quả: <ảnh hưởng code/UI/phase>
- Trạng thái: active | superseded by Dyy
```

### 21.6. Tiêu chí “sẵn sàng Phase 1”

- [ ] Phase 0 gate pass có văn bản + 2 quyết định `[!]` đã chốt.
- [ ] `pytest` cho tiering xanh.
- [ ] `.gitignore` + git repo sạch.
- [ ] `SESSION.md` tồn tại.
- [ ] Doc 02 không còn số liệu cũ gây nhầm.
- [ ] Có ERD + danh sách migration Phase 1.

---

## 22. PHỤ LỤC

### 22.1. Thuật ngữ

| Thuật ngữ | Định nghĩa |
|---|---|
| **Lead Trader** | Người quản lý portfolio được người khác copy |
| **Copier** | Người copy giao dịch của lead |
| **AUM** | Tổng tài sản quản lý của portfolio lead (phần lớn có thể là tiền lead) |
| **Copy AUM** | Phần tài sản đến từ copier |
| **Copier PnL** | Lợi nhuận/lỗ của copier (khác lead PnL) |
| **ROI** | Tỷ suất lợi nhuận theo cửa sổ (7D/30D/90D/180D) |
| **PnL** | Lợi nhuận/lỗ tuyệt đối |
| **MDD** | Maximum Drawdown — mức giảm tối đa từ đỉnh |
| **Sharpe** | Tỷ lệ lợi nhuận/độ biến động; có thể null |
| **WinRate (order)** | `winOrders / totalOrder` — định nghĩa Binance |
| **WinRate (position)** | Vị thế thắng / tổng vị thế đã đóng |
| **Profit Factor** | Tổng lãi / tổng lỗ |
| **Payoff** | Lãi trung bình / lỗ trung bình |
| **Leverage** | Đòn bẩy ước tính từ position/trade |
| **Holding time** | Thời gian giữ vị thế trung bình |
| **Data Confidence** | Điểm tin cậy dữ liệu (coverage + freshness + sample) |
| **Pre-score** | Điểm sơ bộ từ list để xếp thứ tự deep fetch |
| **Potential tier** | Tier tiềm năng từ list (chưa xác nhận bằng detail) |
| **Watch (C)** | Trader vượt pre-filter tối thiểu, cần theo dõi |
| **Qualified (B)** | Trader đủ điều kiện chất lượng (runtime/order/risk) |
| **High (A)** | Trader đủ điều kiện cao nhất (runtime ≥ 180, order ≥ 100) |
| **Excluded** | Trader không đạt pre-filter; không deep fetch |
| **Hard filter** | Điều kiện loại cứng, không bù bằng điểm |
| **Risk event** | Sự kiện rủi ro có severity + evidence |
| **Golden dataset** | Bộ 12 archetype dùng regression test |
| **Provenance** | Nguồn + thời điểm + cửa sổ của mỗi chỉ số |
| **Adapter** | Lớp trừu tượng nguồn dữ liệu (BAPI/CSV/Demo) |
| **Kill switch** | Công tắc tắt collector/nguồn dữ liệu |
| **Coverage** | % trader quét được so với `total` |
| **Freshness** | Độ mới của dữ liệu (phút kể từ lần collect) |
| **Snapshot** | Bản ghi trạng thái tại một thời điểm |
| **Tier drift** | Trader đổi tier giữa các lần chạy |
| **False negative** | Trader đủ điều kiện nhưng bị pre-filter loại |
| **Survivorship bias** | Chỉ nhìn trader còn hoạt động, bỏ qua trader đã rời |
| **Flow distortion** | Nạp/rút làm sai lệch ROI/equity/drawdown |

### 22.2. Artifact map

| File/thư mục | Nội dung | Dùng cho |
|---|---|---|
| `phase0/data/universe_90d.jsonl` | 11.124 trader + tier + reasons + pre_score | Nguồn sự thật Phase 0 |
| `phase0/data/tier_summary.csv` | Tổng hợp phễu theo PUBLIC/SIGNAL/TOTAL | Kiểm tra count |
| `phase0/data/scan_summary.json` | Metadata + thời gian + coverage | Báo cáo |
| `phase0/data/sample_manifest.csv` | 63 trader mẫu theo tier | Deep fetch |
| `phase0/data/deep_fetch_status.csv` | Trạng thái từng trader | Debug |
| `phase0/data/deep_fetch_summary.json` | Tổng hợp deep fetch | Báo cáo |
| `phase0/data/audit_summary.json` | False negative rates | Gate |
| `phase0/data/activity_check_summary.json` | Proxy vs lastTradeTime | Validate |
| `phase0/data/rate_limit_summary.json` | Kết quả concurrency | Capacity |
| `phase0/data/indicator_quality_summary.json` | Kiểm chứng 7 nhóm chỉ số | Quyết định metric |
| `phase0/data/unavailable_probe.json` | 6 endpoint 404 | Scope |
| `phase0/data/raw/` | Raw bundle theo trader | Audit/rebuild |
| `phase0/PHASE0_REPORT.md` | Báo cáo go/no-go | Quyết định |
| `docs/kehoach/data-availability-matrix.csv` | Field ↔ availability | Data contract |

### 22.3. Công thức tóm tắt

| Chỉ số | Công thức/quy tắc |
|---|---|
| ROI | Dùng published theo window; không tự suy từ PnL nếu thiếu vốn gốc |
| MDD | Dùng `performance.mdd`; estimated từ `chartItems` chỉ để audit |
| Estimated equity | `equity = 1 + ROI/100` (không dùng trực tiếp `ROI` làm equity) |
| Sharpe | Dùng published; null → `N/A`, không chấm 0 |
| WinRate order | `winOrders / totalOrder` |
| WinRate position | `wins / (wins + losses)` |
| Profit factor | `gross_profit / gross_loss`; loss = 0 → `N/A` hoặc cap |
| Payoff | `avg_win / abs(avg_loss)`; loss = 0 → `N/A` |
| Confidence | `w1*coverage + w2*freshness + w3*sample + w4*field_completeness` |
| Score | `Σ(weight_i × normalized_i)`; missing → renormalize trọng số |
| Risk penalty | Trừ điểm theo severity; hard filter loại trước khi score |
| Pre-score | Điểm list-level để xếp thứ tự deep fetch, không phải score cuối |

> Công thức chi tiết + trọng số nằm ở mục 9 và `03-bo-chi-so-va-scoring.md`. Khi sửa trọng số phải tạo `scoring_config_version` mới.

### 22.4. Quy ước trạng thái & quản trị tài liệu

| Ký hiệu | Nghĩa | Bằng chứng bắt buộc |
|---|---|---|
| `[x]` | Đã xong | Code/artifact/số đo cụ thể |
| `[~]` | Một phần | Có code/dữ liệu nhưng chưa đạt gate |
| `[ ]` | Chưa làm | — |
| `[!]` | Bị chặn/cần quyết định | Câu hỏi + lựa chọn + deadline |

**Quy tắc cập nhật:**

1. File này là **nguồn quyết định/kiến trúc**. `TASKS.md` là **nguồn tiến độ thực thi**.
2. Quyết định mới → thêm Dxx vào mục 3 hoặc Qxx vào mục 20; ghi `SESSION.md`.
3. Số liệu vận hành → lấy từ artifact mới nhất, ghi rõ thời điểm snapshot.
4. Không sửa số liệu lịch sử trong changelog; chỉ thêm mục mới.
5. Mỗi phase kết thúc → cập nhật bảng tổng quan trong `TASKS.md` + acceptance + changelog.
6. Review tài liệu mỗi 2 tuần hoặc khi có quyết định thay đổi kiến trúc.

### 22.5. Liên kết tài liệu

| File | Nội dung | Khi nào đọc |
|---|---|---|
| `01-pham-vi-va-kien-truc.md` | Phạm vi, kiến trúc chi tiết | Khi thiết kế module |
| `02-data-contract-binance.md` | Endpoint, field, mapping | Khi viết adapter/parser |
| `03-bo-chi-so-va-scoring.md` | Metric, công thức, risk rules | Khi viết quant/scoring |
| `04-lo-trinh-va-nghiem-thu.md` | Timeline, acceptance gốc | Khi lập sprint |
| `05-ui-ux-va-trang.md` | Screen, layout, component | Khi làm frontend |
| `06-kiem-thu-van-hanh-bao-mat.md` | Test, ops, security | Khi QA/deploy |
| `07-rui-ro-phap-ly-va-du-phong.md` | Risk, legal, fallback | Trước launch |
| `08-nhat-ky-quyet-dinh.md` | Decision log gốc | Khi cần bối cảnh quyết định |
| `TASKS.md` | Checklist thực thi Phase 1–6 + Phase 0 đã xong | Cập nhật tiến độ hằng ngày |
| `phase0/PHASE0_REPORT.md` | Bằng chứng Phase 0 | Khi cần số đo/GO |

### 22.6. Checklist đọc nhanh (one-page)

Nếu chỉ có 5 phút:

1. **Sản phẩm:** screener + risk analytics cho lead trader Binance Futures; không auto-trade, không realtime, không paper copy.
2. **Phễu:** 11.124 trader → Watch 515 → Qualified 109 → High 13; chỉ deep fetch Watch trở lên.
3. **Nguyên tắc dữ liệu:** null ≠ 0; MDD dùng published; WinRate order/position tách; AUM/CopyAum tách; mọi chỉ số có window + nguồn + confidence.
4. **Trạng thái:** Phase 0 ~95% (gate GO có điều kiện); Phase 1–6 chưa bắt đầu; timeline 7–9 tuần full-time.
5. **Việc tiếp theo:** sửa bug reason, chốt `mdd=None` + cohort, cập nhật `SESSION.md`, sửa `.gitignore`, init git, rồi Phase 1.

### 22.7. Changelog

| Version | Ngày | Thay đổi |
|---|---|---|
| v1.0 | — | Kế hoạch ban đầu (docx/01–08) |
| v2.0 | — | Bổ sung phễu 3 tầng, bỏ paper copy, 3 bảng ranking |
| **v3.0** | **06/11/2026** | Hợp nhất 01–08 + TASKS + artifact Phase 0; thêm số liệu thực 11.124/515/109/13; D01–D30; Q01–Q20; checklist Phase 0–6; sửa các sai lệch tài liệu ↔ code |
| **v3.1** | **07/11/2026** | Tách mục 17 (lộ trình/checklist) sang `TASKS.md`; TASKS.md có tham chiếu **mục + khoảng dòng** cho từng bước; Phase 0 giữ nguyên; cập nhật trạng thái `SESSION.md` |

---

> **Kết thúc kế hoạch tổng thể.**  
> File này thay thế việc đọc rải rác `01`–`08` để biết trạng thái. Khi có thay đổi, cập nhật `TASKS.md` (tiến độ) và mục 22.7 (changelog) trước.






