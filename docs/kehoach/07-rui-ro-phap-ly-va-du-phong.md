# 07 — RỦI RO, PHÁP LÝ & PHƯƠNG ÁN DỰ PHÒNG

> Đọc kèm: `02-data-contract-binance.md`, `README.md`

---

## 1. Rủi ro nguồn dữ liệu

### 1.1. BAPI không phải API chính thức

| Yếu tố | Thực tế |
|---|---|
| Tài liệu | Không có trong Binance Developer Docs |
| Xác thực | Không cần auth |
| Ổn định | Có thể đổi path/field bất kỳ lúc nào |
| Rate limit | Có, mã `11012005` |
| Chặn IP | Có thể |
| Chặn vùng | Binance chặn một số khu vực (ví dụ Mỹ) |
| ToS | Vẫn áp dụng |

**Hệ quả:** không được coi BAPI là nền tảng ổn định cho một sản phẩm thương mại dài hạn nếu chưa có thỏa thuận với Binance.

### 1.2. Rủi ro pháp lý

- Dữ liệu công khai **không đồng nghĩa** được phép thu thập quy mô lớn, lưu trữ, tái phân phối.
- Không bán raw data.
- Không dùng logo/nhãn Binance như chứng nhận.
- Không đưa ra khuyến nghị đầu tư cá nhân hóa.
- Có disclaimer rõ: “công cụ phân tích, không phải tư vấn đầu tư”.
- Tuân thủ quy định địa phương về crypto và copy trading.

### 1.3. Giảm thiểu

| Biện pháp | Mô tả |
|---|---|
| Adapter pattern | `BinanceBapiAdapter`, `CsvImportAdapter`, `DemoAdapter` |
| Raw archive | JSONL append-only, có thể rebuild DB |
| Rate limit lịch sự | 6–8 workers, backoff, cache |
| Kill switch | Tắt collector bằng 1 config |
| Không phụ thuộc realtime | 60 phút/lần, chịu được gián đoạn |
| Disclaimer | Trên UI và trong API docs |
| Không auto-trade | Không lưu API key giao dịch |
| Data provenance | Ghi nguồn + thời điểm trên mọi chỉ số |

---

## 2. Rủi ro dữ liệu

| Rủi ro | Ví dụ thật | Giảm thiểu |
|---|---|---|
| **Flow distortion** | Coi ROI là equity → MDD 88,67%; đổi đúng `equity = 1 + ROI/100` → 31,3384%, khớp published | Dùng published MDD; tự tính chỉ để audit, ghi rõ “estimated” |
| **Null ≠ 0** | Sharpe null 34,9% | Renormalize, confidence |
| **Zero ≠ missing** | copyAum zero 60,5% | Hiển thị “không có copier”, không “N/A” |
| **Window confusion** | ROI 7D/30D/90D/180D | Luôn ghi cửa sổ |
| **New portfolio** | 4 ngày tuổi, cả 4 window giống nhau | Hard filter runtime |
| **WinRate definition** | 50% theo order vs 62,5% theo position | Hiển thị cả hai, ghi nhãn |
| **AUM misleading** | AUM 1,18M nhưng copyAum 22k | Hiển thị copyAum riêng |
| **Lead PnL vs Copier PnL** | 583k vs 1k | Hiển thị cả hai |
| **Fake/test profile** | nickname mặc định, mô tả “包亏” | Data quality flag |
| **ROI cực cao** | 7.069% ROI, MDD 1,52% | Anomaly flag, không auto top |
| **Sample nhỏ** | 5/10 order | Low sample badge |
| **Trade pagination** | 5.292 fill, 200/page | Fetch đủ total, không break sớm |
| **List fluctuation** | 8.976 → 8.973 | Dedupe, snapshot, log partial |
| **Pre-filter loại nhầm trader tốt** | Trader mới 20 ngày, ROI cao, bị loại vì <30 ngày | Watch tier + audit 50 excluded + ngưỡng configurable |
| **Tier quá chặt → shortlist rỗng** | AUM 5k loại 81,6% trader | Preset Broad/Balanced/Strict |
| **Tier quá lỏng → deep fetch nhiều** | AUM 1k → 1.021 Watch | Giới hạn max deep fetch/ngày |
| **Tier drift** | Trader đổi tier liên tục | Lưu lịch sử tier + chỉ đổi khi vượt ngưỡng rõ ràng |

---

## 3. Rủi ro sản phẩm

| Rủi ro | Hậu quả | Giảm thiểu |
|---|---|---|
| Người dùng chase ROI | Chọn trader rủi ro cao | Score + risk flags + không có bảng High Return |
| Dashboard quá nhiều số | Không ra quyết định | 10 chỉ số cốt lõi |
| AI bịa | Mất niềm tin | Evidence IDs + JSON schema + fallback |
| Scoring bị game | Trader tối ưu chỉ số | Percentile + hard filter + review |
| AUM hiểu sai | Đánh giá sai độ phổ biến | CopyAum + copiers |
| Paper Copy giả chính xác | Người dùng tin sai | Cắt khỏi MVP |
| Cấu hình web phá hệ thống | Ranking sai | Version + validation + audit + rollback |
| Quá nhiều tính năng | Trễ | Quyết định khóa + cắt scope |

---

## 4. Phương án dự phòng nếu BAPI chết

### Phương án A — CSV Import

- Người dùng tự export dữ liệu (nếu Binance cho phép) hoặc nhập tay.
- Hệ thống parse CSV theo schema chuẩn.
- Ưu điểm: hợp pháp, ổn định.
- Nhược điểm: coverage thấp, thủ công.

### Phương án B — Demo / Synthetic Data

- Dùng golden dataset 12 archetype (gồm 2 excluded).
- Mục đích: phát triển UI/scoring, không quảng cáo là dữ liệu thật.
- Ưu điểm: không phụ thuộc mạng.
- Nhược điểm: không có giá trị sản phẩm thật.

### Phương án C — Chuyển hướng sản phẩm

- Từ “screener toàn thị trường” sang “trade journal cá nhân”:
  - Người dùng cung cấp API key read-only của chính họ.
  - Phân tích lịch sử giao dịch của họ.
  - Hợp pháp hơn, nhưng không còn là copy trading discovery.

### Phương án D — Đàm phán dữ liệu

- Xin quyền truy cập chính thức/đối tác Binance.
- Thời gian dài, không phù hợp MVP.

**Khuyến nghị:** thiết kế Adapter ngay từ Phase 0; không để Phase 2–6 phụ thuộc cứng vào BAPI.

---

## 5. Kill criteria

Dừng hoặc pivot nếu:

- [ ] Không lấy được list/detail sau 5 ngày thử.
- [ ] BAPI chặn IP thường xuyên, không thể crawl ổn định.
- [ ] ToS/legal kết luận không được phép dùng cho sản phẩm công khai.
- [ ] Dữ liệu thiếu đến mức không thể tính 10 chỉ số cốt lõi.
- [ ] Pre-filter false negative > 10% (bỏ sót quá nhiều trader tốt).
- [ ] Không có nguồn thay thế trong 2 tuần.

---

## 6. Disclaimer mẫu

> **Miễn trừ trách nhiệm**  
> Đây là công cụ phân tích dữ liệu công khai, không phải tư vấn đầu tư, không phải khuyến nghị mua/bán, không đảm bảo lợi nhuận. Dữ liệu có thể sai, thiếu, hoặc bị thay đổi bởi nguồn cung cấp. Người dùng tự chịu trách nhiệm với quyết định của mình. Copy trading có rủi ro mất toàn bộ vốn.

Đặt disclaimer:

- Footer mọi trang.
- Trong AI report.
- Trong API docs.
- Trong email/onboarding nếu có.

---

## 7. Checklist pháp lý trước khi public

- [ ] Đọc lại ToS Binance tại thời điểm launch.
- [ ] Không dùng logo Binance gây hiểu nhầm.
- [ ] Có disclaimer rõ ràng.
- [ ] Không bán raw data.
- [ ] Không cung cấp tín hiệu đầu tư cá nhân hóa.
- [ ] Có chính sách xóa dữ liệu theo yêu cầu.
- [ ] Có privacy policy nếu lưu email người dùng.
- [ ] Kiểm tra quy định địa phương.
- [ ] Có kill switch dữ liệu.
- [ ] Có log nguồn dữ liệu.
