# PHASE 2 REPORT â€” Collector 2 táº§ng + raw storage

> NgĂ y: 07/11/2026  
> Pháº¡m vi: bÆ°á»›c 2.1 â†’ 2.8 (khĂ´ng lĂ m Phase 3)  
> Tráº¡ng thĂ¡i: **Äáº T GATE PHASE 2**

---

## 1. Káº¿t quáº£ gate

| TiĂªu chĂ­ | YĂªu cáº§u | Káº¿t quáº£ | Äáº¡t |
|---|---|---|---|
| Coverage universe 1 run | â‰¥ 99% cá»§a 11.124 | **11.132** trader = 100,07% | âœ… |
| Watch (C+B+A) | 400â€“700 | **511** | âœ… |
| PhĂ¢n bá»‘ tier | â€” | watch 425 Â· qualified 76 Â· high 10 Â· excluded 10.623 | âœ… |
| Excluded bá»‹ deep fetch | 0 | 0 táº¡i thá»i Ä‘iá»ƒm chá»n (test + filter tier) | âœ… |
| Cháº¡y láº¡i 3 láº§n | KhĂ´ng duplicate | counts giá»‘ng há»‡t cáº£ 3 láº§n | âœ… |
| Restart giá»¯a crawl | Resume Ä‘Æ°á»£c | kill sau 35s â†’ cháº¡y láº¡i Ä‘á»§ coverage, 0 duplicate | âœ… |
| Rate limit/backoff | Xá»­ lĂ½ `11012005` | Mock 3 ca + live 679 request trades, 0 lá»—i | âœ… |
| Chu ká»³ scan + shortlist | < 15 phĂºt | 142,6s scan + 38,7s performance = **181,3s** | âœ… |
| Full-scale deep fetch | Äo tháº­t ~515 | 511 perf + 278 detail + 57 trades = **250,8s** | âœ… |
| Test suite | Pass | **41 passed** (container, gá»“m integration) | âœ… |

---

## 2. Kiáº¿n trĂºc Ä‘Ă£ triá»ƒn khai

```text
backend/app/
  services/collector/http.py        retry/backoff/cooldown/circuit breaker
  services/collector/binance.py     BinanceBapiAdapter 6 endpoint
  services/collector/parsers.py     parse detail/performance/position/trade/transfer
  services/collector/lock.py        Redis lock + PG advisory fallback
  services/universe.py              scan, dedupe, recompute tier
  services/funnel.py                traded_last_7d, tier, reason, pre_score (pure)
  services/deep_fetch.py            L2 performance, L3 detail/positions/transfers, L4 trades
  services/storage/raw.py           JSONL archive + gzip + retention
  services/config_store.py          app_settings + kill switch
  services/jobs.py                  job registry cho API run-*
  worker/scheduler.py               scan 60m, perf 6h, detail 12h, trades 24h
  api/v1/universe.py                summary, traders, recompute
  api/v1/collector.py               status, run-scan, run-deep, jobs, kill-switch
  models/                           collection_log, tier_history, position, trade, transfer,
                                    data_quality_flag, app_setting
migrations 0004 â†’ 0007 (khĂ´ng sá»­a 0001â€“0003)
frontend/src/pages/DataHealthPage.tsx
scripts/check_refs.py, smoke_bapi.ps1, smoke_collector.ps1
```

Compose thĂªm `redis:7-alpine` vĂ  `worker`; volume `./data:/app/data`; nginx giá»¯ cá»•ng 8080.

---

## 3. Sá»‘ liá»‡u Ä‘o tháº­t

### 3.1. L0 â€” Universe scan

| Chá»‰ sá»‘ | GiĂ¡ trá»‹ |
|---|---:|
| Request | 372 trang |
| Trader | 11.132 (PUBLIC ~8.968 + SIGNAL 2.164) |
| Duplicate | 0 |
| Thá»i gian | 132â€“145s (láº§n Ä‘o 142,6s) |
| Lá»—i | 0 |

### 3.2. L2 â€” Performance 4 window

| Chá»‰ sá»‘ | GiĂ¡ trá»‹ |
|---|---:|
| Target | 511 trader (Watch Ä‘áº§y Ä‘á»§) |
| Request | 2.044 |
| Metric lÆ°u | 2.044 |
| Thá»i gian | 38,7s |
| Lá»—i | 0 |
| Sharpe null 90D | 9 |
| MDD null 90D | 1 |
| Háº¡ tier HF04 | 38 trader (highâ†’qualified, qualifiedâ†’watch) |

### 3.3. L3 â€” Detail + positions + transfers

| Chá»‰ sá»‘ | GiĂ¡ trá»‹ |
|---|---:|
| Target | 278 (76 qualified + 10 high + top 200 watch) |
| Ineligible (paused/full slot) | 2 |
| Positions | 70.567 |
| Transfers | 8.228 |
| Thá»i gian | 77,9s |
| Lá»—i | 0 |

### 3.4. L4 â€” Full trade history

| Chá»‰ sá»‘ | GiĂ¡ trá»‹ |
|---|---:|
| Target | 57 (10 high + 47 qualified top) |
| Request | 679 trang |
| Fill táº£i vá» | 130.962 |
| Trade unique lÆ°u | 120.595 |
| TrĂ¹ng bá»‹ hash loáº¡i | 10.367 |
| Thá»i gian | 134,2s |
| Lá»—i | 0 |

> `trade-history` khĂ´ng cĂ³ `trade_id`; hash `(time, symbol, side, price, qty, fee, positionSide)` lĂ  khĂ³a chá»‘ng trĂ¹ng.

### 3.5. Dá»¯ liá»‡u tĂ­ch lÅ©y

| Báº£ng | Sá»‘ dĂ²ng |
|---|---:|
| traders | 11.134 |
| trader_universe | 11.134 |
| performance_metrics | 4.088 |
| positions | 68.714 |
| transfers | 8.329 |
| trades | 120.595 |
| collection_logs | 75 |

Raw archive: 372+ file JSONL, ~144 MB táº¡i thá»i Ä‘iá»ƒm Ä‘o.

---

## 4. Idempotency & resume

**Cháº¡y 3 láº§n liĂªn tiáº¿p** (cĂ¹ng giá»):

| Run | Universe | Watch | traders | snapshots list | universe | metrics | trades |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 11.131 | 511 | 11.133 | 22.261 | 11.133 | 4.088 | 120.595 |
| 2 | 11.131 | 511 | 11.133 | 22.261 | 11.133 | 4.088 | 120.595 |
| 3 | 11.131 | 511 | 11.133 | 22.261 | 11.133 | 4.088 | 120.595 |

**Resume:** cháº¡y scan, kill process sau 35s, xĂ³a khĂ³a Redis, cháº¡y láº¡i â†’ universe 11.132, watch 511,
`portfolio_snapshots` duplicate trong giá» hiá»‡n táº¡i = **0**.

**Trades:** láº§n cháº¡y láº¡i cho 650 fill nhÆ°ng báº£ng váº«n 650 dĂ²ng (hash unique), khĂ´ng nhĂ¢n báº£n.

---

## 5. Rate limit & backoff

- Mock test: `11012005` â†’ retry thĂ nh cĂ´ng; HTTP 429 body HTML â†’ retry; `Retry-After` Ä‘Æ°á»£c tĂ´n trá»ng;
  429 háº¿t lÆ°á»£t â†’ `RATE_LIMITED`; 404 khĂ´ng retry; circuit breaker má»Ÿ sau 5 lá»—i.
- Live: trong láº§n cháº¡y full trades cĂ³ nhiá»u `11012005`; backoff + cooldown xá»­ lĂ½ háº¿t, **0 request tháº¥t báº¡i**.
- Sau khi crawl 130k fill liĂªn tá»¥c, BAPI cháº·n IP báº±ng HTTP 429. ÄĂ£ bá»• sung:
  - nháº­n diá»‡n 429 trÆ°á»›c khi parse JSON,
  - cooldown toĂ n cá»¥c 30â€“180s,
  - tá»‘i Ä‘a 5 retry,
  - trades cháº¡y **1 trader/láº§n**, nghá»‰ 0,4s/trang.
- Váº­n hĂ nh: náº¿u process cháº¿t khi Ä‘ang giá»¯ khĂ³a, xĂ³a báº±ng
  `docker compose exec redis redis-cli DEL lock:collector:scan lock:collector:deep`.

---

## 6. Kiá»ƒm thá»­

| Háº¡ng má»¥c | Káº¿t quáº£ |
|---|---|
| Backend test trong container (`RUN_INTEGRATION=1`) | **41 passed** |
| Backend test ngoĂ i container | 28 passed, 12 skipped |
| `ruff check backend` | Pass |
| `npm run build` | Pass |
| E2E Playwright | Pass: login â†’ Data Health â†’ trader qualified â†’ trader excluded â†’ logout |
| `npm audit --audit-level=high` | 0 vulnerability |
| Secret scan | KhĂ´ng track `.env`; khĂ´ng match pattern secret |
| `scripts/check_refs.py` | 164 tham chiáº¿u, 0 lá»—i |
| Migration | `0004 â†’ 0007`; `alembic current` = head |

---

## 7. Váº¥n Ä‘á» Ä‘Ă£ biáº¿t / quyáº¿t Ä‘á»‹nh

1. **Tier thay Ä‘á»•i giá»¯a cĂ¡c táº§ng:** B/A ban Ä‘áº§u lĂ  upper bound; sau L2 Ă¡p HF04 theo `totalOrder`.
   VĂ¬ váº­y truy váº¥n lá»‹ch sá»­ cĂ³ thá»ƒ tháº¥y trader tá»«ng watch/qualified nay Ä‘Ă£ excluded váº«n cĂ²n positions/trades cÅ©.
   Táº¡i thá»i Ä‘iá»ƒm chá»n cá»§a má»—i run, excluded **khĂ´ng** Ä‘Æ°á»£c deep fetch (test `test_excluded_trader_never_targeted`).
2. **Job registry trong process:** restart API máº¥t tráº¡ng thĂ¡i job; Phase 5 chuyá»ƒn sang queue/DB.
3. **Redis lock TTL 30 phĂºt:** process cháº¿t cĂ³ thá»ƒ cháº·n run káº¿ tiáº¿p tá»‘i Ä‘a 30 phĂºt; cĂ³ lá»‡nh xĂ³a thá»§ cĂ´ng trong README.
4. **BAPI IP rate limit:** sau crawl lá»›n cáº§n nghá»‰; scheduler Ä‘Ă£ giĂ£n táº§n suáº¥t vĂ  trades cháº¡y tuáº§n tá»±.
5. `mdd = null` giá»¯ null + `missing_mdd`; Sharpe null giá»¯ null (Q01).
6. `pre_score` dĂ¹ng má»™t cohort chung `all` (Q02).

---

## 8. Káº¿t luáº­n

Phase 2 Ä‘áº¡t toĂ n bá»™ gate: coverage 100,07%, Watch 511, khĂ´ng deep fetch excluded, idempotent qua 3 láº§n cháº¡y,
resume sau restart, chu ká»³ scan + shortlist 181,3s, full deep 250,8s, test suite pass.
Sáºµn sĂ ng cho Phase 3 â€” Quant + Scoring + Screener.
