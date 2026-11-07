---
id: gioi-han
title: "Known limitations"
group: "Tham chiếu"
order: 19
keywords: "giới hạn, open positions, funding, slippage, ai, bundle, nginx dns"
---

# Known limitations

## 1. Dữ liệu

- Không có vị thế đang mở.
- Không có PnL từng copier.
- Không có funding, slippage, giá thanh lý.
- Không có lý do lead vào/ra lệnh.

## 2. AI

- Primary model có lúc trả thiếu field/JSON lỗi.
- Fallback vẫn có thể sai.
- Không đảm bảo phát hiện mọi rủi ro.
- Không thay thế đọc số liệu gốc.

## 3. Frontend

- Bundle lớn do chart library.
- Cần code-split thêm ở phase sau.

## 4. Vận hành

- Recreate backend có thể cần restart nginx do cache DNS.
- Ranking snapshot cũ vẫn giữ; UI chỉ hiển thị bản mới nhất.
- Dữ liệu thô có thể tăng dung lượng; cần theo dõi.

## 5. Nguồn

`SESSION.md`, `docs/kehoach/PHASE5-REPORT.md`.
