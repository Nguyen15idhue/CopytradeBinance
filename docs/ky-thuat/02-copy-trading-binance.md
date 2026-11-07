---
id: copy-trading
title: "Copy trading và Binance Futures"
group: "Nền tảng"
order: 2
keywords: "copy trading, lead trader, copier, fixed ratio, phí, funding, slippage, leverage, thanh lý"
---

# Copy trading và Binance Futures

## 1. Lead trader và copier

- **Lead trader**: người mở/đóng vị thế trên tài khoản của họ.
- **Copier**: tài khoản sao chép lệnh theo tỷ lệ đã chọn.

Khi lead mở lệnh, hệ thống copy tạo lệnh tương ứng cho copier. Kết quả không giống hệt nhau.

## 2. Cơ chế copy

Có hai kiểu phổ biến:

- **Fixed ratio**: copy theo tỷ lệ vốn.
- **Fixed amount**: copy số tiền cố định mỗi lệnh.

Tỷ lệ copy ảnh hưởng trực tiếp đến mức lỗ/lãi và khả năng cháy tài khoản.

## 3. Vì sao kết quả khác nhau

- Độ trễ giữa lệnh lead và lệnh copy.
- Trượt giá do thanh khoản.
- Phí giao dịch và funding.
- Chênh lệch đòn bẩy/ký quỹ.
- Thời điểm vào/ra lệnh khác nhau.
- Lead có thể thay đổi chiến lược.

## 4. Phí và funding

- Phí có thể dương hoặc âm (rebate).
- Funding có thể làm thay đổi PnL ngoài giá.
- Hệ thống không có dữ liệu funding chi tiết; không hiển thị như thể có.

## 5. Đòn bẩy và thanh lý

- Đòn bẩy cao làm tăng rủi ro thanh lý.
- MDD thấp không có nghĩa là không thể lỗ sâu trong một vị thế.
- `worst_position_roi` giúp phát hiện vị thế lỗ cực lớn.

## 6. Dữ liệu Binance có và không có

Có:

- ROI, PnL, MDD, Sharpe, WinRate, AUM, Copy AUM.
- Position history, trade history, transfer history.
- Chart items (ROI lũy kế).

Không có:

- Vị thế đang mở.
- PnL từng copier.
- Funding, slippage, giá thanh lý.
- Lý do vào/ra lệnh của lead.

## 7. Nguồn

`docs/kehoach/02-data-contract-binance.md`, `docs/huong-dan-nguoi-moi.md`.
