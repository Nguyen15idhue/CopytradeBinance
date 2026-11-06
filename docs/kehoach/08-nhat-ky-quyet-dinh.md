# 08 — NHẬT KÝ QUYẾT ĐỊNH & TÓM TẮT PHÂN TÍCH

> Mục đích: ghi lại **vì sao** kế hoạch v2 khác v1, để sau này không tranh luận lại các quyết định đã chốt.  
> Ngày: 06/11/2026.

---

## 1. Đầu vào

| Tài liệu | Nội dung | Đánh giá |
|---|---|---|
| `Kế hoạch v1.docx` | Kiến trúc, 9 màn hình, 7 phase, database, AI, settings | Tốt về cấu trúc, lạc quan về dữ liệu và timeline |
| `các chỉ số cho copy trade.docx` | Kiến thức domain, chỉ số, cách chọn trader, copy settings | Tốt về domain, thiếu mapping dữ liệu, có lỗi ví dụ |
| Kiểm chứng BAPI thực tế | 6 endpoint, 13.004 trader, 111 field | Xác nhận nhiều điểm, bác bỏ một số giả định |

---

## 2. Kết luận phân tích chính

### 2.1. Điểm mạnh của v1

1. Modular Monolith đúng hướng.
2. Tách raw snapshot và derived metrics.
3. Không ghi đè lịch sử.
4. Config có version.
5. AI không sửa điểm.
6. Không realtime, không auto-trade.
7. Có bộ test 10 trader archetype.

### 2.2. Lỗ hổng P0 của v1

| # | Lỗ hổng | Kết luận |
|---|---|---|
| P0.1 | Giả định Binance cho phép lấy dữ liệu | Đã xác nhận **có** BAPI nội bộ, nhưng không chính thức, có ToS risk |
| P0.2 | Cam kết chỉ số vượt năng lực dữ liệu | Đã xác nhận **trade-level data có thật**, nhưng open positions/per-copier/funding **không có** |
| P0.3 | Cold start 90/180 ngày | Vẫn đúng; `chartItems` giúp có shape 90D nhưng bị flow distort |
| P0.4 | Timeline 29–47 ngày | Vẫn lạc quan; thực tế 34–49 ngày + buffer, 8–10 tuần |

### 2.3. Phát hiện mới từ dữ liệu thật

1. **13.004 trader**, không phải 8.990 như ước lượng ban đầu.
2. Trader trong URL mẫu là **SIGNAL**, không phải PUBLIC.
3. **111 field** thô; ~26 chỉ số trực tiếp; ~35–40 suy ra.
4. **Không có open positions**; `positionShow=false` nhưng position-history vẫn trả.
5. **Không có per-copier, funding, liquidation, copy slippage**.
6. **MDD: 88,67% là lỗi công thức, không phải lỗi `chartItems`**. Coi ROI lũy kế là equity → 88,67%; đổi đúng `equity = 1 + ROI/100` → 31,3384%, khớp published 31,338369%. Vẫn dùng published làm nguồn hiển thị.
7. **WinRate theo order ≠ theo position**: 50% vs 62,5%.
8. **AUM ≠ chất lượng**: AUM 1,18M nhưng copyAum 22k.
9. **Lead PnL ≠ Copier PnL**: 583k vs 1k.
10. **Null/zero rates cao**: Sharpe 34,9% null; AI summary 97,8% null; badge 99,7% null; copier 69,8% zero.
11. **Page cap**: list 30, trade 200.
12. **Performance dùng `BASE_P`**, không phải `BASE_F`.
13. **Trader 4 ngày tuổi** có ROI 7D/30D/90D/180D giống hệt.
14. **Fee có thể âm** (rebate).

### 2.4. Phễu chọn trader (thay đổi lớn nhất của v2.1)

| Tầng | Số lượng | Ghi chú |
|---|---:|---|
| Universe PUBLIC + SIGNAL | 11.130 | Không quét PRIVATE |
| C — Watch | 517 | Có trade 7D, runtime ≥30, ROI/PnL >0, WR≥40, MDD≤40, AUM≥5k, còn slot |
| B — Qualified | 113 | Runtime ≥90, ROI≥10, WR≥45, MDD≤30, AUM≥10k |
| A — High | 13 | Runtime ≥180, ROI≥20, WR≥50, MDD≤20, Sharpe≥1 |
| Excluded | ~10.613 | Không deep fetch |

Lý do loại (trên PUBLIC, có overlap):

- AUM < 5k: 81,6%.
- ROI ≤ 0: 59,1%.
- PnL ≤ 0: 57,5%.
- WinRate < 40: 39,9%.
- MDD > 40: 33,4%.
- Runtime < 30 ngày: 24,9%.
- Không trade 7D: 12,8%.
- Full slot: 0,1%.

> Đây là lý do không thể — và không nên — deep-fetch toàn bộ 13.004 trader.

---

## 3. Quyết định đã chốt

| # | Quyết định | Lý do | Hệ quả |
|---|---|---|---|
| D01 | Tái định vị thành **Screener & Risk Analytics** | Không có dữ liệu cho auto-copy/paper copy trung thực | Bỏ auto-trade, paper copy |
| D02 | MVP còn **4 màn hình chính** | Giảm scope, tăng chất lượng | Screener, Detail, Compare, Settings/Data Health |
| D03 | **Bỏ Paper Copy** khỏi MVP | Mô phỏng sẽ tạo cảm giác chính xác giả | Đưa vào backlog v1.1 |
| D04 | **3 bảng ranking** | 6 bảng là quá nhiều, dễ chase ROI | Overall, Low Risk, Consistency |
| D05 | **Published metrics trước, derived sau** | Dữ liệu published có ngay; derived cần thời gian | Không block launch |
| D06 | **MDD hiển thị = `performance.mdd`** | Published là định nghĩa chính thức; `chartItems` chỉ có điểm ngày và từng bị tính sai thành 88,67% | Không dùng MDD tự tính để xếp hạng; tự tính chỉ để audit |
| D07 | **Null ≠ 0** | Sharpe null 34,9%; zero rates cao | Renormalize + confidence |
| D08 | **Runtime là hard filter** | Trader 4 ngày lọt bảng 90D | Min 30 ngày |
| D09 | **AUM và Copy AUM tách biệt** | AUM 98% có thể là tiền lead | Hiển thị cả hai |
| D10 | **WinRate order và position tách biệt** | Định nghĩa khác nhau | Ghi rõ nhãn |
| D11 | **AI không sửa điểm** | Tránh hallucination ảnh hưởng ranking | AI chỉ giải thích + evidence |
| D12 | **Adapter pattern** | BAPI có thể đổi/block | Có CSV/Demo fallback |
| D13 | **Không realtime** | Không cần, giảm rủi ro | 60 phút/lần |
| D14 | **Không auto trading** | Rủi ro pháp lý/tài chính | Không lưu API key giao dịch |
| D15 | **Config có version + audit** | Đổi trọng số không được làm sai lịch sử | `scoring_config_versions` |
| D16 | **Timeline 7–9 tuần** | Thực tế hơn 29–47 ngày; phễu giảm thời gian crawl | Có buffer 20% |
| D17 | **Phễu 3 tầng, không deep-fetch toàn bộ** | 10.600+ trader không có tiềm năng hoặc thiếu dữ liệu | List scan 11.130; deep fetch ~517; full trades ~13–50 |

---

## 4. Những gì đã thay đổi so với v1

| Hạng mục | v1 | v2 |
|---|---|---|
| Định vị | AI Copy Trading Intelligence | Binance Copy Trader Screener & Risk Analytics |
| Số màn hình | 9 | 4 (+ AI report phase sau) |
| Phạm vi fetch | Toàn bộ 13.004 | Universe 11.130 + shortlist ~517 |
| Deep fetch | 13.004 detail | ~517 performance, ~113–313 detail/positions |
| Full trade history | 13.004 | ~13–50 |
| Thời gian crawl | 45–60 phút | 5–10 phút |
| Paper Copy | Có | Không (backlog) |
| Ranking | 6 bảng | 3 bảng |
| Strategy labels | Cam kết | Heuristic “suspected” |
| Copy Performance | 15% trọng số | 10%, renormalize nếu thiếu |
| Scoring weights | 8 nhóm | 7 nhóm, rõ công thức hơn |
| Data source | “Nguồn được phép” | Data contract + adapter + fallback |
| MDD | Không nói rõ nguồn | Chỉ published, cấm chartItems |
| Null handling | Chưa có | Bắt buộc renormalize |
| Runtime | Filter mềm | Hard filter |
| Timeline | 29–47 ngày | 34–49 ngày + buffer |
| Testing | Danh mục | Golden dataset + acceptance criteria |

---

## 5. Câu hỏi còn mở

| # | Câu hỏi | Cần quyết trước |
|---|---|---|
| Q01 | Có cần lưu list record của trader excluded để audit không? | Phase 2 |
| Q02 | Có cần trade-history cho mọi trader hay chỉ shortlist? | Phase 2 |
| Q03 | Retention trade-history bao lâu? | Phase 2 |
| Q04 | AI provider nào? Budget bao nhiêu/tháng? | Phase 5 |
| Q05 | Có cần multi-user hay chỉ 1 admin? | Phase 1 |
| Q06 | Có cần export CSV/PDF? | Phase 3 |
| Q07 | Có cần correlation matrix ở MVP? | Phase 4 |
| Q08 | Có cần benchmark ETH/SOL ngoài BTC? | Phase 4 |
| Q09 | Có cần cảnh báo qua email không? | Backlog |
| Q10 | Có cần lưu lịch sử ranking bao lâu? | Phase 3 |
| Q11 | Ngưỡng tier có nên khác nhau cho PUBLIC và SIGNAL? | Phase 0 |
| Q12 | Preset AUM mặc định là Balanced (5k) hay Broad (1k)? | Phase 0 |
| Q13 | Có cần quét PRIVATE không? | Phase 0 |
| Q14 | Có nên giữ trader <30 ngày trong “Watch” nếu ROI/MDD rất tốt? | Phase 0 |

---

## 6. Việc tiếp theo

1. Chạy Phase 0 trên 20 trader mỗi tier (C/B/A) + 10 excluded.
2. Xác nhận lại counts 460 / 103 / 13 và false negative < 5%.
3. Xác nhận `data-availability-matrix.csv`.
4. Chốt 20 chỉ số MVP.
5. Dựng skeleton repo.
6. Tạo golden dataset gồm cả excluded.
7. Chưa làm UI chi tiết trước khi Phase 0 xong.

---

## 7. Ghi chú về độ tin cậy của kết luận

- Số lượng trader và field được đo tại **06/11/2026**; có thể thay đổi.
- Các endpoint là BAPI nội bộ; có thể đổi.
- Trader mẫu là SIGNAL, mới 4 ngày; không đại diện cho toàn thị trường.
- Các kết luận về scoring là đề xuất, cần hiệu chỉnh bằng dữ liệu thật sau 30–90 ngày.
- Không có kết luận nào ở đây là khuyến nghị đầu tư.
