# 05 — Kế hoạch: vòng đời raw archive, độ tươi dữ liệu và Data Health

> Trạng thái: **kế hoạch**, chưa triển khai.
> Phạm vi: `RawArchive`, scheduler collector, API `/collector/status`, job thủ công, UI `/data-health`,
> độ tươi dữ liệu (agent + trader detail), `as_of` của published metrics, backfill `risk_score`.
> Nguồn khảo sát: đọc code + query PostgreSQL + đo trực tiếp trong container ngày 2026-11-07/08.
> Liên quan: `backend/app/services/storage/raw.py`, `backend/app/worker/scheduler.py`,
> `backend/app/api/v1/collector.py`, `backend/app/services/jobs.py`,
> `frontend/src/pages/DataHealthPage.tsx`, `frontend/src/pages/TraderDetailPage.tsx`,
> `frontend/src/pages/ScreenerPage.tsx`, `backend/app/services/agent/`,
> `docs/ky-thuat/11-data-health-collector.md`, `docs/ky-thuat/12-ai.md`.

---

## 1. Vấn đề đã xác nhận (có bằng chứng)

### V1 — Raw archive đang append vô hạn, không ghi đè

| Bằng chứng | Chi tiết |
|---|---|
| `storage/raw.py:17-25` | Đường dẫn `data/raw/<ngày>/<giờ>/<endpoint>/<page>.jsonl` |
| `storage/raw.py:39` | Mở file bằng `mode="a"` → append, không ghi đè |
| `universe.py:184-196` | Mỗi page gọi `archive.append(...)`; một scan ghi 373 file |
| Số đo live | 4.474 file / 1,76 GB trong `data/raw/2026-11-07` |
| Một scan bình thường | 373 file / ~68,9 MB (giờ 16h) |
| Cùng giờ có nhiều scan | Giờ 04h: 372 file nhưng **553,9 MB**; `04/list-public/page-0022.jsonl` có **9 dòng `_meta`** |
| Retention | `compress_older_than()` / `purge_older_than()` có code nhưng **không có caller** |

Hệ quả:

- Mỗi giờ tạo thêm 373 file mới; 24 giờ ≈ **8.952 file/ngày**, ~**1,65 GB/ngày**.
- Scan lặp trong cùng giờ append trùng vào cùng file, làm file phình và dữ liệu bị lặp.
- Sau 90 ngày ước tính ~**805.000 file**; `stats()` hiện mất ~20 giây cho 4.474 file,
  nên khi đó có thể mất hàng chục phút mỗi lần gọi.
- Raw archive hiện **không được đọc ở đâu** ngoài `RawArchive().stats()` → đang là write-only.

### V2 — `stats()` chặn toàn bộ event loop

| Phép đo | Kết quả |
|---|---|
| `RawArchive().stats()` trong container | **20,04 giây** |
| `GET /api/v1/collector/status` | **18,99 giây** |
| `GET /health` gọi song song lúc status đang chạy | **18,95 giây** |
| `GET /health` gọi một mình | **0,015 giây** |

`stats()` là hàm đồng bộ, được gọi trực tiếp trong async endpoint
(`api/v1/collector.py:68`), nên chặn event loop của toàn bộ backend.
Trong lúc `/data-health` tải, các API khác cũng bị treo theo.

### V3 — Deep fetch bị trễ sau mỗi lần worker restart

| Bằng chứng | Chi tiết |
|---|---|
| `worker/scheduler.py:94-96` | `last_run = {kind: now ...}` rồi chỉ `pop("scan")` |
| Hệ quả | `scan` chạy ngay; `perf` chờ 6h, `detail` chờ 12h, `trades` chờ 24h |
| Worker hiện tại | Khởi động `13:57 UTC`; chưa có log `perf xong` / `detail xong` / `trades xong` |
| `performance_metrics` | Bản đầy đủ cuối cùng `04:00 UTC`; bản mới nhất `05:00 UTC` → cũ ~12–13 giờ |
| Log deep thật | L2/L3/L4 chạy `03:49–04:17 UTC`; sau restart chỉ có log test |
| Kế hoạch chạy tiếp | `perf` ~`19:57 UTC`, `detail` ~`01:57 UTC`, `trades` ~`13:57 UTC` hôm sau |

Nếu worker restart thường xuyên hơn 6 giờ, dữ liệu performance gần như không bao giờ
được refresh tự động. Đây là nguyên nhân chính của cảm giác “dữ liệu cũ” dù scan L0 vẫn chạy.

### V4 — Fetch thủ công chỉ có API/CLI, job nằm trong bộ nhớ

| Thành phần | Hiện trạng |
|---|---|
| API | `POST /collector/run-scan`, `POST /collector/run-deep` (admin) |
| CLI | `python -m app.collector_cli scan|deep|perf|detail|trades|...` |
| UI | Không có nút chạy; chỉ hiển thị danh sách “Job thủ công” |
| Lưu trữ job | `services/jobs.py` dùng dict `JOBS` trong process backend |
| Hệ quả | Backend restart là mất job + lịch sử; job đang chạy bị kill giữa chừng |

### V5 — UI Data Health không có trạng thái tải thực

| Bằng chứng | Chi tiết |
|---|---|
| `DataHealthPage.tsx:27` | `refetchInterval: 30_000` |
| `DataHealthPage.tsx:30-32` | Chỉ có skeleton `h-40` khi `isLoading` lần đầu |
| Không có | Thời gian đã tải, trạng thái đang cập nhật, lần cập nhật cuối, nút thử lại |
| Hệ quả | Request 19 giây lặp lại mỗi 30 giây; UI gần như luôn trong trạng thái chờ |

### V6 — Rủi ro môi trường trong lúc khảo sát

Trong lúc khảo sát, một process PowerShell bên ngoài chạy lặp
`docker compose up -d --build backend`, làm container backend bị recreate khoảng 1 phút/lần.
Việc này không phải lỗi code nhưng làm job thủ công biến mất và có thể gây lỗi kết nối.
Khi triển khai/QA phải đảm bảo chỉ có một tiến trình compose đang chạy.

### V7 — Hệ thống biết dữ liệu cũ nhưng không cảnh báo ai

| Bằng chứng | Chi tiết |
|---|---|
| `trader_metrics.metrics.freshness_minutes` | Trader `5076854789130646529` = **765,96 phút** (~12,8h) |
| `metrics.provenance.performance_at` | `2026-11-07T04:00:00+00:00` trong khi bây giờ `17:27 UTC` |
| Kế hoạch 03 §8 | Yêu cầu “dữ liệu cũ > 150 phút → cảnh báo” — **chưa implement** |
| `services/agent/` | Không đọc `freshness_minutes`; `grep freshness` chỉ thấy mô tả tool |
| `TraderDetailPage.tsx` / `ScreenerPage.tsx` | Không hiển thị mốc dữ liệu hay badge “cũ” |
| Hệ quả thực tế | AI trình bày 7D `+3.85%` (dữ liệu 04:00) như số hiện tại; Binance lúc kiểm tra là `−3.57%` |

Đây là lỗi trung thực dữ liệu: cùng một con số nhưng người dùng không biết nó cũ 12,8 giờ,
trong khi cửa sổ 7D cuộn và vị thế mở có thể đổi dấu trong vài giờ.

### V8 — `as_of` của published metrics lấy sai mốc

| Bằng chứng | Chi tiết |
|---|---|
| `agent/db_tools.py` | `as_of = metric.computed_at.isoformat()` |
| Thực tế trader trên | `computed_at = 16:45 UTC` (vừa rebuild) nhưng nguồn published là `04:00 UTC` |
| `metrics.provenance.performance_at` | Đã lưu đúng mốc nguồn nhưng không được dùng |
| Hệ quả | UI/AI ghi “as_of 2026-11-07” như thể dữ liệu mới, che mất độ trễ 12,8h |

`computed_at` là lúc **tính lại**, không phải lúc **thu thập**. Dùng nó làm `as_of` cho số
published là sai ngữ nghĩa.

### V9 — `risk_score` trống toàn bộ, filter và hiển thị vô dụng

| Bằng chứng | Chi tiết |
|---|---|
| `trader_metrics` | `risk_score` not null: **0/531** |
| `risk_level` | Vẫn có (trader trên = `high`) |
| Nguyên nhân | Risk V2 mới ở mức code + migration `0014`; chưa chạy backfill `collector_cli risk` |
| Hệ quả | Filter `max_risk_score` (kế hoạch 04) luôn trả rỗng; cột “Điểm rủi ro” và `veto` trống; AI không nêu được điểm rủi ro |

---

## 2. Mục tiêu

1. Raw archive không tăng vô hạn; mặc định chỉ giữ **latest + previous**, có chế độ audit tuỳ chọn.
2. `/collector/status` trả về **< 300 ms p95**, không quét filesystem.
3. Deep fetch chạy đúng hạn kể cả sau restart; dữ liệu quá hạn được chạy bù ngay.
4. Job thủ công được lưu DB, không mất khi backend restart, có thể xem trạng thái trên UI.
5. UI Data Health không còn màn hình trắng/treo: skeleton từng phần, thời gian đã tải,
   trạng thái đang cập nhật, lần cập nhật cuối, nút thử lại.
6. Không dùng phần trăm tiến trình giả; nếu muốn tiến trình thật thì phải có tín hiệu từ server.
7. Mọi màn hình/AI hiển thị số liệu published phải kèm **mốc dữ liệu thật** và cảnh báo
   khi `freshness_minutes > 150`; không được trình bày số cũ như số hiện tại.
8. `as_of` của published metrics lấy từ `provenance.performance_at` (mốc thu thập), không
   dùng `computed_at` (mốc tính lại).
9. `risk_score`/`risk_veto` phải được backfill cho toàn bộ trader trước khi filter
   `max_risk_score` được coi là dùng được.

---

## 3. Quyết định thiết kế

| # | Quyết định | Lý do |
|---|---|---|
| D1 | Raw archive mặc định **`latest_previous`**: mỗi endpoint giữ 1 bản latest + 1 bản previous | Đúng nhu cầu fallback, chặn tăng trưởng vô hạn |
| D2 | Mỗi lần scan ghi **một bundle hoàn chỉnh** cho từng endpoint, gzip, ghi atomic | Giảm từ 373 file/lần xuống 1–2 file/lần; tránh file dở dang |
| D3 | Thêm bảng `raw_archive_manifests`; `stats()` đọc manifest thay vì `rglob()` | O(1), không chặn event loop |
| D4 | Scheduler dùng **last success** từ `collection_logs`, không dùng `last_run = now` khi start | Restart không làm trễ deep fetch |
| D5 | Job thủ công lưu DB + worker queue; API chỉ enqueue | Không mất job khi backend restart |
| D6 | Tách API nhanh/chậm: `/collector/status` nhanh, `/collector/archive-stats` riêng | UI load được phần nhanh trước, không chặn toàn trang |
| D7 | UI giữ dữ liệu cũ khi refetch, hiện thời gian đã tải; **không hiện % giả** | Trung thực dữ liệu, tránh màn hình trắng |
| D8 | Retention chạy hằng ngày; có CLI dry-run | Kiểm soát dung lượng, không xoá nhầm |
| D9 | Không sửa migration cũ; migration mới đánh số tiếp từ `0019` | AGENTS.md §3 |
| D10 | Giữ phạm vi raw archive ở L0 list; L2–L4 raw vẫn nằm trong DB JSONB | Không mở rộng phạm vi, tránh tăng dung lượng đột biến |
| D11 | Ngưỡng cảnh báo dữ liệu cũ **150 phút** (hằng số dùng chung backend + UI), có 3 mức: `ok ≤150`, `stale ≤1440`, `very_stale >1440` | Một nguồn sự thật, tránh mỗi nơi một ngưỡng |
| D12 | `as_of` published = `provenance.performance_at`; `computed_at` trả riêng là `computed_at` | Đúng ngữ nghĩa thu thập vs tính lại |
| D13 | `risk_score` backfill bằng `collector_cli risk` + kiểm tra `count(risk_score) = count(*)`; nếu thiếu thì filter `max_risk_score` trả `meta.risk_score_missing` | Không âm thầm trả rỗng |

---

## 4. Thiết kế chi tiết

### 4.1. Raw archive mới

#### Chế độ mặc định `latest_previous`

```text
data/raw/
  latest/
    list-public.jsonl.gz
    list-signal.jsonl.gz
  previous/
    list-public.jsonl.gz
    list-signal.jsonl.gz
```

- Mỗi scan tạo **một bundle** cho `list-public` và một bundle cho `list-signal`.
- Bundle chứa toàn bộ page + `_meta` của scan hiện tại.
- Ghi vào `*.tmp` → `fsync` → `os.replace()` thành `latest`.
- Chỉ sau khi scan **thành công** mới rotate:
  - `latest` cũ → `previous`
  - `latest` mới → `latest`
- Scan lỗi: xoá file tạm, giữ nguyên `latest`/`previous`.
- Không còn append theo giờ, không còn trùng dữ liệu trong cùng giờ.

#### Chế độ audit (tuỳ chọn)

```text
data/raw/archive/
  2026-11-07/
    scan-<scan_id>-list-public.jsonl.gz
    scan-<scan_id>-list-signal.jsonl.gz
```

- Bật bằng `RAW_ARCHIVE_MODE=audit`.
- Mỗi scan một bundle; không append.
- Dùng khi cần replay/audit dài ngày.
- Mặc định **tắt** để không tăng dung lượng.

#### Cấu hình đề xuất

```env
RAW_ARCHIVE_MODE=latest_previous        # latest_previous | audit
RAW_ARCHIVE_HOT_VERSIONS=2
RAW_ARCHIVE_COMPRESS_AFTER_DAYS=1
RAW_ARCHIVE_AUDIT_RETENTION_DAYS=90
RAW_ARCHIVE_DIR=data/raw
```

### 4.2. Manifest

Migration mới `0019_raw_archive_manifest`:

```sql
CREATE TABLE raw_archive_manifests (
    id              BIGSERIAL PRIMARY KEY,
    scan_id         UUID NOT NULL,
    layer           VARCHAR(8) NOT NULL,
    endpoint        VARCHAR(64) NOT NULL,
    mode            VARCHAR(16) NOT NULL,
    status          VARCHAR(16) NOT NULL,   -- writing | success | failed | purged
    path_latest     TEXT,
    path_previous   TEXT,
    files           INTEGER NOT NULL DEFAULT 0,
    bytes           BIGINT NOT NULL DEFAULT 0,
    records         BIGINT NOT NULL DEFAULT 0,
    checksum        VARCHAR(64),
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    rotated_at      TIMESTAMPTZ,
    purged_at       TIMESTAMPTZ
);

CREATE INDEX ix_raw_manifest_created ON raw_archive_manifests (created_at DESC);
CREATE INDEX ix_raw_manifest_layer_status ON raw_archive_manifests (layer, status);
```

Quy tắc:

- `status=writing` khi bắt đầu ghi.
- `status=success` sau khi rotate thành công.
- `status=failed` nếu scan lỗi; file tạm bị xoá.
- `status=purged` khi retention xoá bundle audit.
- `files`/`bytes`/`records` phục vụ `stats()`; không cần quét lại filesystem.

### 4.3. Retention

Chạy trong worker, mỗi ngày một lần (ví dụ 03:15 UTC), có lock riêng.

| Chế độ | Quy tắc |
|---|---|
| `latest_previous` | Luôn giữ `latest` + `previous`; không có file lịch sử |
| `audit` | Nén sau 1 ngày; xoá bundle cũ hơn 90 ngày; cập nhật `status=purged` |

Thêm CLI:

```bash
python -m app.collector_cli archive-retention --dry-run
python -m app.collector_cli archive-retention
```

- `--dry-run` in danh sách file sẽ xoá, không thực thi.
- Không xoá `latest`/`previous`.
- Nếu manifest thiếu, job reconcile bằng cách liệt kê thư mục **một lần** rồi ghi lại manifest.

### 4.4. API

#### `GET /api/v1/collector/status` — nhanh

Giữ shape cũ, bổ sung field:

```json
{
  "enabled": true,
  "tiers": {"watch": 436, "qualified_upper": 72, "high_upper": 9, "excluded": 10724},
  "latest_runs": {"L0": {"...": "..."}, "L2": {"...": "..."}},
  "jobs": [],
  "raw_archive": {
    "mode": "latest_previous",
    "files": 2,
    "bytes": 138000000,
    "records": 11151,
    "latest_at": "2026-11-08T00:00:36Z",
    "source": "manifest"
  },
  "generated_at": "2026-11-08T00:00:00Z"
}
```

- Không gọi `rglob()`.
- `raw_archive` đọc từ manifest + cache Redis TTL 60 giây.
- Nếu cache/manifest lỗi: trả `source: "stale"` + `latest_at` cũ, không làm request thất bại.
- Mục tiêu p95 < 300 ms.

#### `GET /api/v1/collector/archive-stats` — chi tiết

- Trả danh sách manifest gần nhất, tổng file/bytes/records theo ngày.
- Dùng cho card “Lưu trữ dữ liệu thô” nếu cần chi tiết.
- Có thể cache 60 giây; không chặn `/collector/status`.

#### Tiến trình thật (tuỳ chọn P2)

Nếu cần hiển thị “đã quét bao nhiêu file”:

```text
GET /api/v1/collector/archive-stats/stream   (SSE)
  event: stage   data: {"stage":"manifest","done":true}
  event: stage   data: {"stage":"reconcile","scanned":1200,"total":4474}
  event: done    data: {"files":2,"bytes":138000000}
```

Chỉ dùng khi thật sự cần; ưu tiên cache/manifest để không phải quét file.

### 4.5. Scheduler

#### Xác định job đến hạn

Map job → layer:

| Job | Layer | Interval mặc định |
|---|---|---|
| `scan` | L0 | 60 phút |
| `perf` | L2 | 6 giờ |
| `detail` | L3 | 12 giờ |
| `trades` | L4 | 24 giờ |

Quy tắc mới:

```text
last_success = max(collection_logs.finished_at)
              where layer = <layer> and status = 'success'

due = (last_success is null) or (now - last_success >= interval)
```

- Khi worker start: tính `due` từ DB, chạy ngay job quá hạn.
- Không khởi tạo `last_run = now` cho deep job.
- Sau khi chạy thành công, ghi `collection_logs` như hiện tại; lần sau tính từ đó.
- Nếu job lỗi: thử lại sau 15 phút, tối đa 3 lần; sau đó chờ interval tiếp theo.
- Thêm jitter ±5 phút cho deep job để tránh trùng thời điểm.
- Manual job thành công cũng cập nhật `last_success` (qua `collection_logs`), tránh chạy lặp.

#### Timeout và lock

- Giữ `CollectorLock` hiện tại (`lock:collector:scan`, `lock:collector:deep`).
- Thêm timeout cấu hình:
  - `COLLECTOR_JOB_TIMEOUT_MIN=60`
  - Job quá timeout → log error, giải phóng lock, ghi `collection_logs.status='failed'`.
- Không chạy 2 job deep song song.

### 4.6. Job thủ công

Migration mới `0020_collector_jobs`:

```sql
CREATE TABLE collector_jobs (
    id              UUID PRIMARY KEY,
    kind            VARCHAR(16) NOT NULL,      -- scan | deep | perf | detail | trades
    status          VARCHAR(16) NOT NULL,      -- queued | running | success | failed | skipped
    requested_by    UUID REFERENCES users(id),
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    result          JSONB,
    error           TEXT
);

CREATE INDEX ix_collector_jobs_requested ON collector_jobs (requested_at DESC);
CREATE INDEX ix_collector_jobs_status ON collector_jobs (status, requested_at);
```

Luồng:

1. API `POST /collector/run-scan` / `run-deep`:
   - Kiểm tra kill switch + quyền admin.
   - Tạo row `collector_jobs(status='queued')`.
   - Push job id vào Redis list `queue:collector:jobs`.
   - Trả `202 {job_id}`.
2. Worker:
   - `BRPOP queue:collector:jobs`.
   - Set `status='running'`, chạy job với lock.
   - Ghi `result`/`error`, `finished_at`.
3. API `GET /collector/jobs/{job_id}`:
   - Đọc DB, trả trạng thái; không phụ thuộc process backend.
4. UI Data Health:
   - Hiện 10 job gần nhất từ DB.
   - Admin có nút “Chạy scan” / “Chạy deep” + xác nhận.
   - Poll job đang chạy mỗi 2–3 giây; job xong tự refresh status.

Không còn dùng dict `JOBS` làm nguồn sự thật. Có thể giữ dict làm cache tạm trong worker,
nhưng DB là nguồn chính.

### 4.7. UI Data Health

#### Query

```tsx
useQuery({
  queryKey: ["collector-status"],
  queryFn: getCollectorStatus,
  placeholderData: keepPreviousData,
  staleTime: 10_000,
  refetchInterval: 60_000,
  refetchIntervalInBackground: false,
});
```

#### Trạng thái hiển thị

| Trạng thái | UI |
|---|---|
| Lần đầu, chưa có dữ liệu | Skeleton từng section (header, tier cards, bảng lần chạy, raw archive, job) |
| Đang refetch, đã có dữ liệu | Giữ dữ liệu cũ + spinner nhỏ + “Đang cập nhật…” |
| Đang tải | Hiện “Đang tải… 12s” (đếm thời gian đã trôi qua) |
| Thành công | Hiện “Cập nhật lúc HH:mm:ss” + “Tự làm mới sau 60s” |
| Lỗi | Giữ dữ liệu cũ nếu có + banner lỗi + nút “Thử lại” |
| Không có dữ liệu | Empty state rõ ràng, không hiện số 0 giả |

#### Nguyên tắc

- **Không hiện % tiến trình** nếu server không gửi tiến trình thật.
- Countdown chỉ dùng cho “lần tự làm mới tiếp theo”, không dùng cho thời gian tải.
- Nếu bật SSE archive-stats: hiện stage thật (`manifest` → `reconcile` → `done`).
- `aria-busy`, `aria-live="polite"` cho vùng trạng thái.
- Số dùng `toLocaleString("vi-VN")`; ngày dùng `toLocaleString("vi-VN")`.
- Không hiển thị `undefined`, `NaN`, `null`; null → `—` hoặc `N/A`.

### 4.8. Độ tươi dữ liệu hiển thị cho người dùng

Nguồn: `trader_metrics.metrics.freshness_minutes` + `metrics.provenance.performance_at`.

Phân mức dùng chung (backend `services/freshness.py`, frontend `lib/freshness.ts`):

| Mức | Điều kiện | UI | AI |
|---|---|---|---|
| `ok` | `≤ 150` phút | chip xanh “Dữ liệu 12 phút trước” | không cảnh báo |
| `stale` | `151–1440` phút | chip vàng “Dữ liệu cũ 2 giờ” | `warning` + nêu mốc as_of |
| `very_stale` | `> 1440` phút | banner đỏ “Dữ liệu cũ hơn 1 ngày” | `warning` + từ chối kết luận xu hướng ngắn hạn |
| `unknown` | thiếu `freshness_minutes` | chip xám “Chưa rõ độ mới” | nêu `missing_data` |

Quy tắc:
- Không đổi giá trị số; chỉ thêm cảnh báo.
- Với `very_stale`, AI vẫn được nêu số nhưng phải ghi “số liệu tại `<as_of>`, có thể đã thay đổi”.
- Không tự động refresh khi người dùng đang xem (tránh nhảy số).

---

## 5. Các bước triển khai

### Bước 5.0.1 — Chốt spec + migration manifest (0,5 ngày)

- Viết `docs/ky-thuat/RAW-ARCHIVE-SPEC.md`: mode, layout, atomic write, retention, manifest.
- Migration `0019_raw_archive_manifest` + `downgrade()`.
- Test: upgrade/downgrade; bảng + index tồn tại.

### Bước 5.0.2 — Refactor RawArchive (1 ngày)

- Thêm mode `latest_previous` / `audit`.
- Ghi bundle gzip, atomic write, rotate latest/previous.
- Ghi manifest `writing` → `success`/`failed`.
- Giữ API `append()` cũ trong giai đoạn chuyển tiếp nếu cần, nhưng scan mới dùng `write_bundle()`.
- Test:
  - 2 scan cùng giờ không tạo file trùng.
  - Scan lỗi không làm mất `latest`.
  - `previous` đúng là bản trước.
  - `stats()` đọc manifest, không quét file.

### Bước 5.0.3 — Retention + CLI (0,5 ngày)

- Job retention hằng ngày trong worker.
- CLI `archive-retention --dry-run`.
- Test: audit mode nén/xoá đúng; latest/previous không bị xoá.
- Log số file/bytes đã xoá.

### Bước 5.0.4 — API status nhanh + archive-stats (0,5 ngày)

- Bỏ `RawArchive().stats()` khỏi `/collector/status`.
- Đọc manifest + cache Redis TTL 60s.
- Thêm `/collector/archive-stats`.
- Test: status < 300 ms p95 với 4.474 file; response shape tương thích UI cũ.
- Test: manifest lỗi → trả stale, không 500.

### Bước 5.0.5 — Scheduler freshness (1 ngày)

- Tính `last_success` từ `collection_logs`.
- Startup chạy bù job quá hạn.
- Retry 3 lần/15 phút; timeout; jitter.
- Test:
  - Worker start với `perf` quá hạn → chạy ngay.
  - Restart không reset đồng hồ deep.
  - Manual job thành công → không chạy lặp.
  - Job lỗi → retry đúng số lần.

### Bước 5.0.6 — Job thủ công lưu DB (1 ngày)

- Migration `0020_collector_jobs`.
- API enqueue; worker consume Redis queue.
- `GET /collector/jobs/{id}` đọc DB.
- UI hiện lịch sử job + nút chạy (admin).
- Test: backend restart không mất job; job `queued` vẫn chạy khi worker lên.
- Test: kill switch chặn job; quyền viewer bị 403.

### Bước 5.0.7 — UI loading/progress (1 ngày)

- `keepPreviousData`, `staleTime`, `refetchInterval` 60s, tắt refetch nền.
- Skeleton từng section; elapsed timer; trạng thái đang cập nhật; lỗi + thử lại.
- Countdown “tự làm mới sau …”; không hiện % giả.
- Tách card raw archive nếu dùng endpoint riêng.
- Test Playwright:
  - Route chậm 20s: skeleton + elapsed tăng, không màn hình trắng.
  - Refetch: dữ liệu cũ vẫn hiển thị, có spinner.
  - Lỗi 500: banner lỗi + nút thử lại.
  - Không có `undefined/NaN`.

### Bước 5.0.8 — Freshness hiển thị + cảnh báo AI (1 ngày)

- Backend `services/freshness.py`: `level(freshness_minutes)` → `ok|stale|very_stale|unknown`,
  hằng số `STALE_MINUTES = 150`, `VERY_STALE_MINUTES = 1440`.
- API `/traders`, `/traders/{id}`, `/traders/{id}/performance` trả thêm
  `freshness: {minutes, level, as_of}`.
- `agent` thêm `warning` khi `stale`/`very_stale`, và `missing_data: ["freshness_unknown"]`.
- Frontend `lib/freshness.ts` + chip/banner ở Screener, Trader Detail, Agent panel.
- Test: unit 4 mức; integration API trả đúng mức; E2E chip hiện với trader có
  `freshness_minutes` lớn (mock response).

### Bước 5.0.9 — `as_of` đúng mốc thu thập (0,5 ngày)

- `agent/db_tools.get_trader_profile` và `search_traders`: `as_of` = `provenance.performance_at`;
  trả thêm `computed_at` riêng.
- `api/v1/trader_detail` và `screener.serialize_row`: thêm `as_of` (nguồn) + giữ `computed_at`.
- Test: trader có `computed_at` mới hơn `performance_at` → response có hai mốc khác nhau,
  `as_of` khớp `performance_at`.

### Bước 5.0.10 — Backfill `risk_score` + chống rỗng âm thầm (0,5 ngày)

- Chạy `python -m app.collector_cli risk` rồi `rank`; kiểm tra `count(risk_score) = count(*)`.
- `screener.list_traders`: nếu `max_risk_score` được dùng mà cột toàn null →
  `meta.risk_score_missing = true` (không trả rỗng im lặng).
- UI: cột “Điểm rủi ro” hiện `N/A` + chú thích khi thiếu; ẩn filter cho tới khi có dữ liệu.
- Test: backfill 531/531; filter `max_risk_score` trả đúng; case thiếu → meta flag.

### Bước 5.0.11 — QA + docs (0,5 ngày)

- `ruff`, `pytest` full, `npm run build`, Playwright.
- `scripts/check_refs.py` 0 lỗi.
- Cập nhật:
  - `docs/ky-thuat/11-data-health-collector.md`
  - `docs/api.md`
  - `docs/kehoach/TASKS.md`
  - `SESSION.md`
  - `KE-HOACH-TONG-THE.md` nếu thay đổi kiến trúc raw archive
- Commit theo format `feat(phaseN): ...`; N chốt khi triển khai.

---

## 6. Kiểm chứng

### Raw archive

- [ ] Hai scan trong cùng giờ: chỉ có `latest`/`previous`, không append trùng.
- [ ] `latest` và `previous` mở được bằng `gzip`, JSONL hợp lệ.
- [ ] Scan lỗi giữa chừng: `latest` cũ vẫn còn, không có file tạm rác.
- [ ] `latest_previous`: số file cố định = 2 × số endpoint.
- [ ] `audit`: retention nén/xoá đúng; `--dry-run` không xoá.
- [ ] Manifest khớp số file/bytes thực tế.

### API

- [ ] `/collector/status` p95 < 300 ms khi có 4.474 file.
- [ ] `/collector/status` không gọi `rglob()`/`stat()` trên toàn bộ archive.
- [ ] `/health` gọi song song vẫn < 100 ms.
- [ ] `/collector/archive-stats` trả đúng manifest; cache hoạt động.
- [ ] Manifest lỗi → response stale có `source`, không 500.

### Scheduler

- [ ] Worker start khi `perf` quá hạn → chạy ngay.
- [ ] Restart worker không làm `perf`/`detail`/`trades` trễ thêm 6/12/24h.
- [ ] Job lỗi retry đúng 3 lần, không loop vô hạn.
- [ ] Manual scan thành công cập nhật `last_success`.
- [ ] Không chạy 2 deep job song song.

### Độ tươi dữ liệu & as_of

- [ ] `freshness_minutes` 4 mức trả đúng `ok/stale/very_stale/unknown`.
- [ ] Trader có `freshness_minutes = 766` → API trả `level=stale`, UI hiện chip vàng.
- [ ] Agent trả lời câu hỏi 7D khi dữ liệu `stale` → có `warning` nêu mốc `as_of`;
  khi `very_stale` → không kết luận xu hướng ngắn hạn.
- [ ] `as_of` của published = `provenance.performance_at`, khác `computed_at` khi rebuild.
- [ ] Không còn trường hợp AI ghi `as_of` là thời điểm tính lại.
- [ ] `risk_score` backfill đủ `531/531`; `count(risk_score) = count(*)`.
- [ ] Filter `max_risk_score` trả đúng; nếu cột null → `meta.risk_score_missing = true`.
- [ ] Cột “Điểm rủi ro” hiện số, không `N/A` sau backfill.

### Job thủ công

- [ ] Backend restart giữa lúc job chạy: DB có trạng thái `running`/`failed`, không mất row.
- [ ] Worker restart: job `queued` được chạy tiếp.
- [ ] Viewer không gọi được API admin.
- [ ] UI hiện lịch sử job từ DB sau restart.

### UI

- [ ] Route chậm 20s: skeleton + elapsed timer, không màn hình trắng.
- [ ] Refetch: dữ liệu cũ vẫn hiển thị, có “Đang cập nhật…”.
- [ ] Lỗi: banner + nút “Thử lại”.
- [ ] Countdown “tự làm mới sau …” đúng, không dùng làm progress.
- [ ] Không có `undefined/NaN/null` lọt UI.

### Hồi quy

- [ ] Scan L0 vẫn ghi `portfolio_snapshots` đủ ~11k trader/giờ.
- [ ] `recompute_universe` vẫn cho cùng tier counts.
- [ ] `performance_metrics`/`trades` không bị ảnh hưởng.
- [ ] `pytest`, `ruff`, `npm run build`, Playwright pass.
- [ ] `check_refs` 0 lỗi.

---

## 7. Checklist nghiệm thu

- [ ] Raw archive mặc định không tăng quá 2 bản/endpoint.
- [ ] Không còn file `page-*.jsonl` mới sinh ra mỗi giờ.
- [ ] `/data-health` load < 1 giây khi manifest/cache hoạt động.
- [ ] Deep data được refresh đúng hạn sau restart.
- [ ] Có nút chạy scan/deep trên UI admin và trạng thái job đọc từ DB.
- [ ] UI có skeleton, elapsed timer, trạng thái cập nhật, lỗi + thử lại.
- [ ] Không có % tiến trình giả.
- [ ] Docs + `TASKS.md` + `SESSION.md` cập nhật; `check_refs` 0 lỗi.
- [ ] Không commit secret, `.env`, `data/`, `dist`, `graphify-out/`, token tạm.
- [ ] Mọi màn hình/AI hiển thị số published đều có mốc dữ liệu và cảnh báo khi > 150 phút.
- [ ] `as_of` là mốc thu thập (`performance_at`), không phải `computed_at`.
- [ ] `risk_score` đủ 531/531; filter `max_risk_score` dùng được, thiếu thì có meta flag.

---

## 8. Rủi ro & kiểm soát

| Rủi ro | Kiểm soát |
|---|---|
| Xoá nhầm `latest` khi rotate | Ghi atomic + giữ `previous`; test crash; CLI dry-run |
| Manifest lệch thực tế | Job reconcile định kỳ; log cảnh báo; stats trả `source` |
| Windows bind mount vẫn chậm | Cân nhắc named volume cho `data/raw`; không đo bằng `rglob` nữa |
| Scheduler chạy trùng sau restart | Lock + `last_success` từ DB + jitter |
| Job thủ công bị treo | Timeout + trạng thái `failed` + retry có giới hạn |
| UI progress gây hiểu nhầm | Không hiện %; chỉ elapsed/stage thật |
| Retention làm mất dữ liệu audit | Mặc định `latest_previous`; audit phải bật rõ; dry-run trước |
| Cảnh báo cũ gây nhiễu | Ngưỡng 150 phút dùng chung; chỉ cảnh báo, không đổi số |
| `as_of` vẫn bị lấy sai ở nơi khác | Grep `computed_at` trong agent/API; test so sánh hai mốc |
| Backfill `risk_score` sai hàng loạt | Chạy dry-run/đếm trước–sau; giữ `risk_level` cũ nếu lỗi |
| `portfolio_snapshots` vẫn tăng ~11k dòng/giờ | Theo dõi riêng; plan partition/retention ở giai đoạn sau |

---

## 9. Việc không làm

- Không đổi cổng host (web 8090, backend 8010).
- Không sửa `phase0/`.
- Không sửa migration cũ.
- Không tự ý xoá dữ liệu thật ngoài chính sách retention đã chốt.
- Không mở rộng raw archive sang L2–L4 trong kế hoạch này.
- Không dùng progress bar % dựa trên thời gian.
- Không auto-trade, không đưa lời khuyên đầu tư.

---

## 10. Definition of Done

- Raw archive chuyển sang `latest_previous` (hoặc `audit` nếu bật), ghi atomic, có manifest.
- `stats()` không còn quét filesystem; `/collector/status` p95 < 300 ms.
- Deep fetch chạy bù khi quá hạn; restart không làm trễ 6/12/24 giờ.
- Job thủ công lưu DB, worker xử lý, UI xem được trạng thái.
- `/data-health` có skeleton từng phần, thời gian đã tải, trạng thái cập nhật, lỗi + thử lại.
- Test backend/frontend/E2E pass; docs cập nhật; `check_refs` 0 lỗi.
- Báo cáo 1–3 dòng kèm commit hash khi hoàn thành.

---

## 10. Tiến độ triển khai

- [x] B5.0.1 Chốt spec + migration manifest — `docs/kehoach/RAW-ARCHIVE-SPEC.md`,
  migration `0019_raw_archive_manifest` (bảng + 2 index), model `RawArchiveManifest`.
  → Bằng chứng: `alembic upgrade head → downgrade -1 → upgrade head` OK; psql xác nhận
  `ix_raw_manifest_created (created_at DESC)` + `ix_raw_manifest_layer_status`;
  `test_models` 5 pass; ruff pass.
- [x] B5.0.2 Refactor RawArchive — `write_bundle()` gzip + tmp + `os.replace`, rotate
  `latest→previous`, manifest `writing→success/failed`; `manifest_stats()` đọc manifest;
  scan gom tất cả trang rồi ghi 1 bundle/endpoint (không còn 373 file/lần).
  Config `RAW_ARCHIVE_MODE/HOT_VERSIONS/COMPRESS_AFTER_DAYS/AUDIT_RETENTION_DAYS`.
  → Bằng chứng: `test_raw_archive` 4 pass (2 scan cùng giờ chỉ latest/previous; lỗi giữ latest,
  không còn `.tmp`; stats không gọi `rglob`; audit ghi bundle theo ngày).
  Chạy thật 2 lần scan: `list-public` 8.926 records / 5,3 MB; `list-signal` 2.181 / 1,2 MB;
  lần 2 tạo `previous.jsonl.gz` (03:20) + `latest` (03:23); manifest 4 dòng success.
- [x] B5.0.3 Retention + CLI — `services/storage/retention.py`: `latest_previous` không xoá;
  `audit` nén sau `RAW_ARCHIVE_COMPRESS_AFTER_DAYS`, xoá quá `RAW_ARCHIVE_AUDIT_RETENTION_DAYS`,
  đánh dấu manifest `purged`; worker có job `retention` mỗi ngày (lock riêng);
  CLI `python -m app.collector_cli archive-retention [--dry-run]`.
  → Bằng chứng: `test_raw_retention` 2 pass (latest/previous không bị xoá; dry-run không xoá,
  chạy thật xoá + purged manifest); CLI dry-run in đúng mode hiện tại.
- [x] B5.0.4 API status nhanh + archive-stats — `/collector/status` đọc manifest + cache Redis 60s,
  không quét filesystem; manifest lỗi → `source=stale` (không 500); thêm `/collector/archive-stats`
  (50 manifest gần nhất + tổng + theo ngày).
  → Bằng chứng: `test_collector_status` 4 pass (rglob bị chặn vẫn 200; p95 < 300ms; shape;
  manifest lỗi → stale); đo thực tế: **p50 40ms, p95 76ms, max 102ms**.
- [x] B5.0.5 Scheduler last_success — `last_success = max(collection_logs.finished_at)` theo layer
  L0/L2/L3/L4 (bỏ log `detail.test=true`); `next_due()` + jitter ±5 phút cho deep job;
  startup chạy bù job quá hạn; retry 15 phút × 3; timeout `COLLECTOR_JOB_TIMEOUT_MIN=60`.
  → Bằng chứng: `test_scheduler_freshness` 7 pass + `test_scheduler_last_success` 1 pass +
  `test_scheduler` 3 pass; log worker khởi động đọc `last_success` thật từ DB
  (scan 03:36, perf/detail/trades 02:38) và chạy `retention` ngay vì chưa từng chạy.
- [x] B5.0.6 Job thủ công lưu DB — migration `0020_collector_jobs` + model; API tạo job
  `queued` rồi đẩy Redis `queue:collector:jobs`; worker consume, cập nhật
  `running/success/failed/skipped` + `result/error`; thêm `GET /collector/jobs` và
  `GET /collector/jobs/{uuid}`; job `queued/running` được requeue khi worker restart;
  UI Data Health hiện 10 job + nút “Chạy scan/deep” cho admin.
  → Bằng chứng: `test_collector_jobs` 2 pass (job trong DB, list/get/404), `test_collector_api`
  pass (RBAC viewer 403, kill switch 409, UUID sai → 404); chạy thật: job `deep` được worker
  nhận (queued→running) và job `scan` hoàn tất **queued→success** lúc 03:56 (371 trang, 11.108 trader);
  E2E PASS thêm “Data Health ẩn nút job với viewer”.
- [x] B5.0.7 UI loading/progress — `keepPreviousData` (placeholderData), `staleTime/refetchInterval`
  60s, `refetchOnWindowFocus=false`, `refetchIntervalInBackground=false`; skeleton từng section
  (`aria-busy`); đồng hồ "Cập nhật Ns trước · tự làm mới sau Ms"; "Đang cập nhật…" khi fetching;
  lỗi khi đã có dữ liệu → banner + Thử lại và giữ nội dung cũ; lỗi khi chưa có dữ liệu →
  trang lỗi + Thử lại; card raw archive hiện mode/records/source.
  → Bằng chứng: build pass; E2E thêm route chậm 2,5s (thấy skeleton) và route 500
  (thấy trang lỗi + Thử lại); toàn bộ E2E PASS, 0 console error.
