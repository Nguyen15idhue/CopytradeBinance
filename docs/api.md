# API v1 — Phase 1

Base: `/api/v1`

## Quy ước

- Response thành công:

```json
{
  "data": {},
  "meta": { "request_id": "...", "generated_at": "..." },
  "error": null
}
```

- Response lỗi:

```json
{
  "data": null,
  "meta": { "request_id": "..." },
  "error": { "code": "TRADER_NOT_FOUND", "message": "...", "details": {} }
}
```

## Auth

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/auth/login` | `{email, password}` → access + refresh token |
| POST | `/auth/refresh` | `{refresh_token}` → cặp token mới (rotate) |
| POST | `/auth/logout` | `{refresh_token}` → thu hồi |
| GET | `/auth/me` | Thông tin user hiện tại |

- Access token 15 phút, refresh 7 ngày.
- Login rate limit 5/phút/IP.
- Gửi header `Authorization: Bearer <access_token>` cho endpoint bảo vệ.

## Trader

### GET `/traders/{id}`

Trả hồ sơ trader + 10 chỉ số + tier + confidence + provenance + flags.

- `null` giữ nguyên `null`, không đổi thành `0`.
- `tier`: `excluded | watch | qualified | high | unknown`.
- `reasons`: lý do loại/xếp tầng.
- `flags`: `missing_sharpe`, `missing_mdd`, `no_copiers`, `low_sample`, `excluded`, `derived_unavailable`.
- `provenance`: `source`, `collected_at`, `window`, `published`.

Ví dụ rút gọn:

```json
{
  "data": {
    "trader": { "id": "...", "nickname": "...", "portfolio_type": "PUBLIC" },
    "tier": "qualified",
    "reasons": [],
    "metrics": [
      { "key": "roi_90d", "label": "ROI 90D", "value": 19.19, "unit": "%", "window": "90D" }
    ],
    "confidence": 0.89,
    "flags": ["derived_unavailable"],
    "provenance": { "source": "demo", "window": "90D", "published": true }
  },
  "error": null
}
```
