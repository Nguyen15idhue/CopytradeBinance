# Hướng dẫn cho người mới

> Tài liệu nguồn cho trang `/help`. Nội dung tĩnh, không phụ thuộc dữ liệu live.
> Cập nhật file này rồi đồng bộ `frontend/src/pages/HelpPage.tsx`.
>
> Trang `/help` có thêm: mục lục sticky (active + tiến độ), tìm kiếm theo keyword, drawer mobile,
> print CSS và **5 hình minh hoạ SVG** (luồng copy, phễu nhóm, cấu trúc thẻ chỉ số,
> bằng chứng rủi ro, quy trình 5 bước) trong `frontend/src/components/help/HelpIllustrations.tsx`.

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
| **Bộ lọc trader** | Lọc universe xuống shortlist theo nhóm, ROI, MDD, Sharpe, WinRate, đòn bẩy, rủi ro |
| **Chi tiết trader** | Xem 10 chỉ số, phân rã điểm, cảnh báo rủi ro, vị thế/giao dịch/nạp rút gần nhất |
| **So sánh** | So sánh 2–4 trader, xem tương quan (ước tính) |
| **Cảnh báo rủi ro** | Danh sách cảnh báo R01–R11 kèm bằng chứng |
| **Bảng xếp hạng** | 3 bảng Tổng hợp / Rủi ro thấp / Độ ổn định |
| **Sức khỏe dữ liệu** | Độ phủ, lần chạy bộ thu thập, dữ liệu cũ |

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

## 5. Nhóm và lý do loại

- **Cao (A)**: vượt ngưỡng B/A trên dữ liệu hiện có.
- **Đạt (B)**: vượt ngưỡng B (giới hạn trên ở tầng list).
- **Theo dõi (C)**: pass pre-filter, chưa đủ điều kiện B/A.
- **Bị loại**: có ít nhất một lý do loại.

**Bị loại không hẳn là trader xấu.** Có thể chỉ vì: số ngày hoạt động < 30, AUM < 5.000,
không giao dịch 7 ngày, hết slot copy, hoặc thiếu dữ liệu. Hãy đọc `lý do loại`.

Nhóm có thể đổi khi dữ liệu mới hơn; B/A ban đầu chỉ là giới hạn trên và được hạ theo `tổng số lệnh`.

## 6. Dữ liệu: Binance công bố, hệ thống tính, ước tính

- **Binance công bố (Published)**: Binance trả trực tiếp (ROI, MDD, Sharpe, WinRate…).
- **Hệ thống tính (Derived)**: tự tính từ vị thế/giao dịch (profit factor, thời gian giữ, chi phí…).
- **Ước tính (Estimated)**: ước tính từ chartItems (drawdown, tương quan) — chỉ tham khảo.

Không có dữ liệu: vị thế đang mở, PnL từng copier, funding, slippage, giá thanh lý.
`null` trên giao diện nghĩa là **không có dữ liệu**, không phải `0`.

## 7. Quy trình 5 bước cho người mới

1. **Mở Bộ lọc trader**, giữ bộ lọc mặc định (Cao/Đạt/Theo dõi, số ngày ≥ 30, số lệnh ≥ 20).
2. **Đọc Chi tiết trader**: 10 chỉ số, phân rã điểm, cảnh báo rủi ro, dữ liệu còn thiếu.
3. **So sánh 2–4 ứng viên** ở trang So sánh; xem tương quan và mức tập trung.
4. **Kiểm tra Cảnh báo rủi ro** cho các cảnh báo nghiêm trọng (MDD, đòn bẩy, ROI xấu nhất).
5. **Tự quyết định**: chỉ copy số vốn chấp nhận mất; bắt đầu nhỏ; theo dõi định kỳ.

Checklist trước khi copy:

- [ ] Hiểu có thể mất vốn.
- [ ] Đã đọc MDD, leverage, worst position ROI.
- [ ] Biết dữ liệu nào đang thiếu.
- [ ] Không copy vì ROI cao đơn thuần.
- [ ] Đã xem lại sau ít nhất 7 ngày.

## 8. Câu hỏi thường gặp & miễn trừ trách nhiệm

**Vì sao Sharpe hiển thị N/A?** Portfolio chưa đủ mẫu hoặc Binance không công bố.
Không chấm 0 và không tô đỏ.

**Vì sao trader ROI cao vẫn bị loại?** Có thể số ngày hoạt động quá ngắn, MDD quá cao,
mẫu quá nhỏ, hoặc thiếu dữ liệu.

**Điểm có phải khuyến nghị đầu tư?** Không. Điểm chỉ xếp hạng tương đối theo cấu hình hiện tại.

**Tương quan có dùng để chia vốn?** Không. Đây là ước tính từ chartItems, bị ảnh hưởng nạp/rút.

**Miễn trừ trách nhiệm:** Công cụ phân tích dữ liệu công khai, không phải tư vấn đầu tư.
Copy trading có rủi ro mất toàn bộ vốn. Bạn tự chịu trách nhiệm với quyết định của mình.
