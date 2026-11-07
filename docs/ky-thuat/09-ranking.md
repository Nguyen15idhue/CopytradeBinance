---
id: ranking
title: "Ranking"
group: "Phân tích"
order: 9
keywords: "ranking, overall, low risk, consistency, snapshot, config version"
---

# Ranking

## 1. Ba bảng

| Board | Mục đích |
|---|---|
| Overall | Điểm tổng hợp sau hard filter |
| Low Risk | Ưu tiên trader ít rủi ro |
| Consistency | Ưu tiên độ ổn định, không chạy theo ROI |

## 2. Low Risk

Điều kiện board:

- Runtime ≥ 90 ngày.
- MDD ≤ 20%.
- Max leverage ≤ 5x (hoặc null).
- Confidence ≥ 0.8.
- Sharpe không null và ≥ 0.

Sharpe veto:

- Sharpe null → không vào Low Risk.
- Sharpe âm → không vào Low Risk.
- Sharpe 0–0.5 chỉ qua khi:
  - MDD ≤ 15%
  - max leverage ≤ 3x
  - runtime ≥ 180 ngày

`risk_rules.eligible_for_low_risk` là cùng logic veto; `ranking.py` kiểm tra thêm các ngưỡng board.

## 3. Consistency

- Xếp theo component/score ổn định.
- Không dùng ROI làm tiêu chí chính.
- Không có bảng “High Return” để tránh chase ROI.

## 4. Snapshot

- Ranking đọc snapshot mới nhất.
- Mỗi snapshot gắn `config_version`.
- Không trộn trader/score từ nhiều version.
- Nếu version active chưa có score, hệ thống rebuild trước khi chụp.

## 5. UI

- `/ranking`
- 3 tab, metadata snapshot, bảng xếp hạng, link Detail.
- Admin có nút chạy ranking.
- Empty state nếu chưa có snapshot.

## 6. Nguồn

`backend/app/api/v1/ranking.py`, `backend/app/services/ranking.py`, `docs/api.md`.
