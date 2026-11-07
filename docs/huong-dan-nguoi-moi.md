# Hướng dẫn cho người mới

> Tài liệu nguồn cho trang `/help`. Nội dung tĩnh, không phụ thuộc dữ liệu live.
> Cập nhật file này rồi đồng bộ `frontend/src/pages/HelpPage.tsx`.
>
> Trang `/help` có thêm: mục lục sticky (active + tiến độ), tìm kiếm theo keyword, drawer mobile,
> print CSS và **5 hình minh hoạ SVG** (luồng copy, phễu tier, cấu trúc metric card,
> risk evidence, quy trình 5 bước) trong `frontend/src/components/help/HelpIllustrations.tsx`.

## 1. Copy trading là gì?

Copy trading là cơ chế để tài khoản của bạn tự động sao chép lệnh của một trader khác
(lead trader). Khi lead trader mở/đóng vị thế, tài khoản copy làm theo theo tỷ lệ bạn chọn.

**Rủi ro cần hiểu ngay:**

- Bạn có thể **mất một phần hoặc toàn bộ vốn**.
- Hiệu suất quá khứ **không đảm bảo** tương lai.
- Copy trading **không phải** kênh đầu tư được bảo đảm lợi nhuận.
- Có độ trễ, trượt giá và phí; kết quả của lead và copier **không giống hệt nhau**.

## 2. Hệ thống này làm gì và không làm gì?

**Làm:**

- Thu thập dữ liệu công khai của lead trader trên Binance Futures.
- Tính chỉ số hiệu suất, rủi ro, độ tin cậy dữ liệu.
- Xếp hạng, sàng lọc và so sánh trader để bạn tự quyết định.

**Không làm:**

- Không auto-trade, không kết nối API giao dịch của bạn.
- Không mô phỏng “paper copy”.
- Không đưa lời khuyên đầu tư, không hứa hẹn lợi nhuận.
- Không hiển thị dữ liệu Binance không cung cấp (open positions, per-copier PnL, funding).

## 3. Cách đọc từng màn hình

| Màn hình | Dùng để |
|---|---|
| **Screener** | Lọc universe xuống shortlist theo tier, ROI, MDD, Sharpe, WinRate, leverage, risk |
| **Trader Detail** | Xem 10 chỉ số, breakdown điểm, risk flags, vị thế/trade/transfer gần nhất |
| **Compare** | So sánh 2–4 trader, xem tương quan (estimated) |
| **Risk Monitor** | Danh sách cảnh báo R01–R11 kèm evidence |
| **Ranking** | 3 bảng Overall / Low Risk / Consistency |
| **Data Health** | Độ phủ, lần chạy collector, dữ liệu cũ |

## 4. Từ điển thuật ngữ

- **ROI**: tỷ suất sinh lời trong cửa sổ 7/30/90/180 ngày.
- **PnL**: lợi nhuận/lỗ tuyệt đối (USDT).
- **MDD**: mức sụt giảm lớn nhất từ đỉnh, lấy số Binance công bố.
- **Sharpe**: lợi nhuận điều chỉnh theo biến động; `null` nghĩa là chưa đủ dữ liệu.
- **WinRate (order)**: order thắng / tổng order đóng.
- **WinRate (position)**: vị thế thắng / tổng vị thế đóng (khác WinRate order).
- **Profit Factor**: tổng lãi / |tổng lỗ|.
- **Payoff ratio**: lãi trung bình / |lỗ trung bình|.
- **AUM**: tổng tài sản quản lý; **Copy AUM**: phần vốn của copier.
- **Leverage**: đòn bẩy tối đa/trung bình từ position-history.
- **Confidence**: độ tin cậy dữ liệu 0–1 (coverage, history, freshness, continuity).
- **Low sample**: mẫu giao dịch nhỏ, kết luận kém tin cậy.

## 5. Tier và lý do loại

- **High**: vượt ngưỡng B/A trên dữ liệu hiện có.
- **Qualified**: vượt ngưỡng B (upper bound ở tầng list).
- **Watch**: pass pre-filter, chưa đủ điều kiện B/A.
- **Excluded**: có ít nhất một lý do loại.

**Excluded không hẳn là trader xấu.** Có thể chỉ vì: runtime < 30 ngày, AUM < 5.000,
không giao dịch 7 ngày, hết slot copy, hoặc thiếu dữ liệu. Hãy đọc `filter_reasons`.

Tier có thể đổi khi dữ liệu mới hơn; B/A ban đầu chỉ là upper bound và được hạ theo `totalOrder`.

## 6. Dữ liệu: published, derived, estimated

- **Published**: Binance trả trực tiếp (ROI, MDD, Sharpe, winRate…).
- **Derived**: hệ thống tự tính từ position/trade (profit factor, holding time, fee drag…).
- **Estimated**: ước tính từ chartItems (drawdown, correlation) — chỉ tham khảo.

Không có dữ liệu: open positions, per-copier PnL, funding, slippage, liquidation price.
`null` trên giao diện nghĩa là **không có dữ liệu**, không phải `0`.

## 7. Quy trình 5 bước cho người mới

1. **Mở Screener**, giữ filter mặc định (High/Qualified/Watch, runtime ≥ 30, orders ≥ 20).
2. **Đọc Trader Detail**: 10 chỉ số, score breakdown, risk flags, “what’s missing”.
3. **So sánh 2–4 ứng viên** ở Compare; xem correlation và mức tập trung.
4. **Kiểm tra Risk Monitor** cho các cảnh báo critical (MDD, leverage, worst ROI).
5. **Tự quyết định**: chỉ copy số vốn chấp nhận mất; bắt đầu nhỏ; theo dõi định kỳ.

Checklist trước khi copy:

- [ ] Hiểu có thể mất vốn.
- [ ] Đã đọc MDD, leverage, worst position ROI.
- [ ] Biết dữ liệu nào đang thiếu.
- [ ] Không copy vì ROI cao đơn thuần.
- [ ] Đã xem lại sau ít nhất 7 ngày.

## 8. FAQ & disclaimer

**Vì sao Sharpe hiển thị N/A?** Portfolio chưa đủ mẫu hoặc Binance không công bố.
Không chấm 0 và không tô đỏ.

**Vì sao trader ROI cao vẫn bị Excluded?** Có thể runtime quá ngắn, MDD quá cao,
mẫu quá nhỏ, hoặc thiếu dữ liệu.

**Score có phải khuyến nghị đầu tư?** Không. Score chỉ xếp hạng tương đối theo cấu hình hiện tại.

**Correlation có dùng để chia vốn?** Không. Đây là ước tính từ chartItems, bị ảnh hưởng nạp/rút.

**Disclaimer:** Công cụ phân tích dữ liệu công khai, không phải tư vấn đầu tư.
Copy trading có rủi ro mất toàn bộ vốn. Bạn tự chịu trách nhiệm với quyết định của mình.
