# SESSION — Phase 0 Data Spike

> **Ngày:** 2026-11-06  
> **Trạng thái:** Phase 0 hoàn tất — **GO CÓ ĐIỀU KIỆN**  
> **Sản phẩm:** Binance Copy Trader Screener & Risk Analytics (không auto-trade)

---

## 1. Mục tiêu phiên

1. Xác minh 6 endpoint BAPI bằng dữ liệu thật.
2. Chốt universe PUBLIC + SIGNAL và phễu C/B/A/Excluded.
3. Đo false negative của bộ lọc.
4. Kiểm chứng các bẫy chỉ số (MDD, WinRate, Sharpe, AUM, Copier PnL, fee).
5. Ra quyết định go/no-go cho Phase 1.

---

## 2. Kết quả chính

| Hạng mục | Kết quả |
|---|---|
| Universe | **11.124** = 8.970 PUBLIC + 2.154 SIGNAL, coverage 100% |
| Watch (C, gồm B/A) | **515** (457 PUBLIC + 58 SIGNAL) |
| Qualified gồm High (B+A) | **109** (99 + 10) |
| High (A) | **13** (13 + 0) |
| Excluded | **10.609** |
| Mẫu deep fetch | **63** (A=13, B=20, C=20, excluded=10) |
| Deep fetch | 63/63 OK, 153,34s, 0 lỗi |
| False negative thực | **0/50 = 0%** (`fn_watch_eligible`) |
| False negative literal | 12/50 = 24% (do thiếu AUM/MDD trong định nghĩa) |
| Activity proxy | 60/63 khớp (95,2%), 3 FP, 0 FN |
| Rate limit | 32 request, 0 bị chặn, 0 lỗi |

---

## 3. Quyết định quan trọng

### D-MDD — Nguồn MDD

- **Hiển thị/xếp hạng:** `performance.mdd` (published).
- **Audit:** `equity = 1 + chartItems.value / 100`, khớp published **63/63**, sai số max **4,9 × 10⁻⁷ pp**.
- Con số **88,67%** cũ là **lỗi công thức** (coi ROI lũy kế là equity), không phải lỗi `chartItems`.
- MDD **phụ thuộc window**: chỉ 6/63 trader giống nhau ở 4 window; chênh tối đa 70,26 pp.

### D-ACT — Activity

- List payload **không có** `lastTradeTime`.
- Proxy `traded_last_7d` không bỏ sót trader đang trade (0 FN) nhưng có thể giữ trader đã ngừng (3 FP).
- Bắt buộc xác minh `detail.lastTradeTime` trước khi ranking.

### D-WR — WinRate

- `winRate` = theo order; khác position-level.
- 59/63 so sánh được; median lệch 2,52 pp; 18 ca lệch > 5 pp; max 33,33 pp.
- Phải hiển thị tách biệt.

### D-NULL — Sharpe

- Null 34,9% universe, 4,8% sample.
- Hiển thị `N/A`, không chấm 0.

### D-FEES — Fee

- 56/58 trader có fee âm; tổng page 1 = −5.835,4656.
- Rebate là bình thường; không cộng fee như chi phí dương.

### D-SCOPE — Endpoint thiếu

- 6/6 probe trả 404: open positions, copier list, funding.
- Không cam kết các tính năng này trong MVP.

---

## 4. Artifact

- `phase0/PHASE0_REPORT.md` — báo cáo đầy đủ.
- `phase0/data/universe_90d.jsonl` — 11.124 trader.
- `phase0/data/tier_summary.csv` — phễu theo nguồn.
- `phase0/data/sample_manifest.csv` — 63 trader mẫu.
- `phase0/data/audit_summary.json` — false negative.
- `phase0/data/indicator_quality_summary.json` — kiểm chứng chỉ số.
- `phase0/data/rate_limit_summary.json` — rate limit.
- `phase0/data/raw/` — raw bundle.

**Giới hạn dữ liệu đã fetch:** positions 13.589/22.641 dòng (7 trader bị cap 1.000 vị thế gần nhất); trades chỉ page 1 (10.967/112.759 dòng); transfers đầy đủ 2.063/2.063.

Scripts:

- `phase0/fetch.py`, `tiering.py`, `scan_universe.py`, `recompute_summary.py`
- `phase0/sample.py`, `deep_fetch.py`, `activity_check.py`
- `phase0/audit_excluded.py`, `indicator_checks.py`, `rate_limit_test.py`

---

## 5. Tài liệu đã sửa

- `docs/kehoach/02-data-contract-binance.md` — đính chính MDD, thêm quy tắc audit.
- `docs/kehoach/03-bo-chi-so-va-scoring.md` — sửa cảnh báo công thức MDD.
- `docs/kehoach/06-kiem-thu-van-hanh-bao-mat.md` — acceptance test MDD.
- `docs/kehoach/07-rui-ro-phap-ly-va-du-phong.md` — mô tả flow distortion đúng.
- `docs/kehoach/08-nhat-ky-quyet-dinh.md` — sửa D06 + phát hiện #6.
- `docs/kehoach/data-availability-matrix.csv` — thêm giới hạn list/detail, audit MDD.
- `docs/kehoach/TASKS.md` — cập nhật trạng thái Phase 0.

---

## 6. Việc tiếp theo (Phase 1)

1. Dựng backend + model theo contract đã chốt.
2. Collector 2 tầng: list 90D → detail/performance cho Watch.
3. Lưu `timeRange` cùng mọi metric.
4. Hiển thị MDD published + nhãn window.
5. Hiển thị WinRate order và position tách biệt.
6. Sharpe null → `N/A` + confidence.
7. Không đưa open positions/per-copier/funding vào MVP.

---

## 7. Cảnh báo vận hành

- `performance` chỉ dùng `BASE_P`.
- List page size tối đa 30; trade tối đa 200.
- Giữ 5–6 worker; backoff khi 429/418.
- `total` có thể đổi giữa các trang → luôn dedupe theo `leadPortfolioId`.
- `positionShow=false` **không** chặn position-history.
- Young portfolio: không giả định 4 window giống nhau; đã thấy ca 29,98 ngày khác window.
