---
id: api-bao-mat
title: "API và bảo mật"
group: "Vận hành"
order: 14
keywords: "api, jwt, argon2id, rbac, pagination, rate limit, csp, fernet, response wrapper"
---

# API và bảo mật

## 1. Auth

- Access token JWT 15 phút.
- Refresh token 7 ngày.
- Mật khẩu hash Argon2id.
- RBAC kiểm tra server-side; `require_admin`.

## 2. Response

```json
{"data": {}, "meta": {"request_id": "...", "generated_at": "..."}, "error": null}
```

Lỗi:

```json
{"data": null, "error": {"code": "TRADER_NOT_FOUND", "message": "Không tìm thấy trader"}}
```

## 3. Pagination

- Mặc định 50.
- Tối đa 100.
- Positions/trades tối đa 200.

## 4. Nhóm endpoint

- Auth
- Traders/screener
- Compare
- Ranking
- Risk
- AI
- Settings
- Collector/data health
- Universe
- Saved views

## 5. Rate limit

- Login: 5/phút/IP.
- API: 100/phút/user.
- Vượt ngưỡng → 429.

## 6. Bảo mật

- API key AI lưu mã hoá Fernet, derive từ `JWT_SECRET`.
- Response chỉ trả `configured`/`masked`, không trả key.
- CSP và security headers ở Nginx.
- Không commit `.env`, secret, data.
- Log không chứa token/key.

## 7. Nguồn

`docs/api.md`, `backend/app/api/`, `infra/nginx/`, `docs/deployment.md`.
