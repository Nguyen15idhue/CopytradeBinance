# Giao diện Sáng / Tối / Hệ thống

> Cập nhật: 07/11/2026 · Áp dụng cho toàn bộ frontend React + Tailwind.

## 1. Cách dùng

- Nút chuyển ở góc phải topbar (sau khi đăng nhập) và góc phải trang đăng nhập.
- Ba chế độ: **Sáng**, **Tối**, **Hệ thống**.
- Mặc định: `system` — theo `prefers-color-scheme` của trình duyệt/OS.
- Lựa chọn lưu ở `localStorage` key `ct_theme_mode`; áp dụng lại khi mở trang.
- Khi chọn `system`, giao diện tự đổi nếu OS đổi theme (MediaQuery listener).

## 2. Cơ chế

- `html` nhận class `light` hoặc `dark`, kèm `data-theme` để debug.
- `color-scheme` được set theo theme (scrollbar, form control native).
- Chuyển màu có transition 150ms, không giật.

## 3. Design token (bắt buộc dùng cho trang mới)

Khai báo trong `src/index.css`, map sang Tailwind trong `tailwind.config.js`.

| Token | Tailwind | Dark | Light |
|---|---|---|---|
| Nền trang | `bg-app` | `#020617` | `#f8fafc` |
| Panel/card | `bg-panel` | `#0f172a` | `#ffffff` |
| Nền nổi (hover, input phụ) | `bg-elevated` | `#1e293b` | `#f1f5f9` |
| Viền/đường kẻ | `border-line`, `divide-line` | `#1e293b` | `#e2e8f0` |
| Chữ chính | `text-strong` | `#f1f5f9` | `#0f172a` |
| Chữ thường | `text-body` | `#cbd5e1` | `#334155` |
| Chữ phụ | `text-muted` | `#94a3b8` | `#64748b` |
| Chữ mờ | `text-faint` | `#64748b` | `#94a3b8` |
| Nhấn (tốt) | `text-accent` | `#34d399` | `#047857` |
| Thông tin | `text-info` | `#7dd3fc` | `#0369a1` |
| Cảnh báo | `text-warn` | `#fcd34d` | `#b45309` |
| Nguy hiểm | `text-danger` | `#fca5a5` | `#b91c1c` |

**Quy tắc:**

- Không dùng lại `text-slate-300/400/500`, `bg-slate-900`, `border-slate-800` trong component mới.
- Nền nhấn giữ dạng `bg-{color}-500/10` + chữ `text-accent|info|warn|danger`.
- Chart dùng CSS var: `stroke="var(--accent)"`, `stroke="var(--danger)"`, tick `fill: "var(--text-faint)"`,
  tooltip `background: var(--panel)`.
- Nút CTA `bg-emerald-500 text-slate-950` giữ nguyên ở cả hai theme.

## 4. Kiểm thử

- E2E Playwright: bấm Sáng → `html.light` + nền `rgb(248,250,252)`; bấm Tối → `html.dark` +
  nền `rgb(2,6,23)`; bấm Hệ thống → không lỗi.
- Chạy: `cd frontend && npm run test:e2e`.
- Screenshot kiểm tra tay: `light-screener.png`, `light-detail.png`, `dark-detail.png` (không commit).

## 5. Giới hạn đã biết

- Chart dùng token màu nên tự đổi; nhưng màu chuỗi correlation/Compare chỉ có 4 màu cố định theo token.
- Các chip nền nhấn 10% alpha có thể hơi nhạt trên màn hình sáng yếu; có thể tăng lên 15% nếu cần.
- Theme không ảnh hưởng tới email/PDF/CSV export.
