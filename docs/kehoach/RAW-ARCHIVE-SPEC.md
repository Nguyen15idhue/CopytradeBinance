# RAW ARCHIVE SPEC — lưu trữ dữ liệu thô collector

> Trạng thái: spec cho kế hoạch 05 (`docs/0/05-ke-hoach-do-tuoi-du-lieu-va-data-health.md`).
> Phạm vi: L0 list scan (PUBLIC/SIGNAL). L2–L4 vẫn nằm trong DB JSONB, không đổi.

## 1. Mode

| Mode | Mô tả | Dùng khi |
|---|---|---|
| `latest_previous` (mặc định) | Mỗi endpoint giữ đúng 2 bản: `latest` và `previous` | Vận hành thường ngày |
| `audit` | Mỗi scan một bundle riêng, nén sau 1 ngày, xoá sau 90 ngày | Cần replay/điều tra |

## 2. Layout

```text
data/raw/archive/
  <endpoint>/
    latest.jsonl.gz
    previous.jsonl.gz

# audit mode
data/raw/archive/
  2026-11-08/
    scan-<scan_id>-list-public.jsonl.gz
    scan-<scan_id>-list-signal.jsonl.gz
```

Quy ước tên:
- `endpoint` = `list-public` | `list-signal` (mở rộng sau nếu cần).
- `scan_id`: UUID4 cho mỗi lần scan, lưu trong manifest.
- Không dùng thư mục theo giờ nữa (bỏ `YYYY-MM-DD/HH`).

## 3. Ghi atomic

1. Ghi ra `latest.jsonl.gz.tmp` (gzip, mỗi record một dòng JSON).
2. `os.replace(tmp, latest.jsonl.gz)` — atomic trên cùng filesystem.
3. Trước khi replace: `latest` → `previous` (nếu tồn tại).
4. Nếu bất kỳ bước nào lỗi: xoá `.tmp`, giữ nguyên `latest`/`previous`, manifest
   `status='failed'` + `error`.

Không append theo giờ. Cùng một giờ chạy 2 lần vẫn chỉ có `latest`/`previous`.

## 4. Manifest

Bảng `raw_archive_manifests` (migration `0019_raw_archive_manifest`):

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | bigserial | PK |
| `scan_id` | uuid | Một scan có thể có nhiều endpoint |
| `layer` | varchar(8) | `L0` |
| `endpoint` | varchar(64) | `list-public` / `list-signal` |
| `mode` | varchar(16) | `latest_previous` / `audit` |
| `status` | varchar(16) | `writing` / `success` / `failed` / `purged` |
| `path_latest` | text | Đường dẫn tương đối |
| `path_previous` | text | Đường dẫn tương đối |
| `files` | int | Số file của bundle |
| `bytes` | bigint | Tổng dung lượng |
| `records` | bigint | Số bản ghi |
| `checksum` | varchar(64) | sha256 của `latest` |
| `error` | text | Lỗi nếu `failed` |
| `created_at` | timestamptz | Mặc định `now()` |
| `rotated_at` | timestamptz | Lúc rotate gần nhất |
| `purged_at` | timestamptz | Lúc retention xoá |

Index: `ix_raw_manifest_created (created_at DESC)`, `ix_raw_manifest_layer_status (layer, status)`.

Quy tắc trạng thái:
- `writing` khi bắt đầu ghi.
- `success` sau khi replace xong.
- `failed` khi scan lỗi; file tạm đã xoá.
- `purged` khi retention xoá bundle audit.

`stats()` đọc manifest (bản `success` mới nhất), **không** quét filesystem.

## 5. Retention

| Mode | Nén | Xoá | Bảo vệ |
|---|---|---|---|
| `latest_previous` | Không cần | Không xoá | Luôn giữ `latest` + `previous` |
| `audit` | Sau 1 ngày | Bundle cũ hơn 90 ngày | Không đụng `latest`/`previous` |

Chạy hằng ngày trong worker, lock riêng `lock:collector:retention`.
CLI: `python -m app.collector_cli archive-retention [--dry-run]`.
`--dry-run` in danh sách sẽ xoá nhưng không thực thi.

## 6. Cấu hình

```env
RAW_ARCHIVE_MODE=latest_previous
RAW_ARCHIVE_HOT_VERSIONS=2
RAW_ARCHIVE_COMPRESS_AFTER_DAYS=1
RAW_ARCHIVE_AUDIT_RETENTION_DAYS=90
RAW_ARCHIVE_DIR=data/raw
```

## 7. Tương thích

- API cũ `RawArchive.append()` giữ trong giai đoạn chuyển tiếp nhưng scan mới dùng
  `write_bundle()`.
- `RawArchive.stats()` đổi nguồn sang manifest; nếu manifest trống (lần đầu nâng cấp)
  thì trả `source="empty"` và job reconcile sẽ ghi manifest ở lần scan kế tiếp.
