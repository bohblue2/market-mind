# SPEC: Evolve `mm_crawler` into a Multi-Source Ingestion Platform (Scrapy + Playwright)

Baseline: Python Scrapy project with `spiders/ items/ pipelines/ middlewares/ database/ alembic/ scrapy_settings.py`, SQLAlchemy ORM + Alembic migrations, mixed async/sync, no test harness in this directory, current spider->pipeline->DB coupling.

New sources to add:
- Hankyung Consensus (Scrapy)
- WiseReport (Playwright)

Hard requirements:
- DB persistence, backfill + 1-minute incremental polling, idempotent storage
- Clean architecture boundaries (domain/application/infrastructure)
- No big-bang rewrite; staged migration

---

## 1) Objectives

1. Multi-source ingestion with a single canonical persistence model usable by all sources.
2. Support two execution modes for every source:
   - Backfill: historical (date-range), partitioned and resumable
   - Poll: every minute incremental refresh, cursor-driven with overlap window
3. Idempotent at DB level (safe to rerun the same window many times).
4. Operational readiness:
   - run records, per-attempt logging, retry classification, guardrails (leases, caps)
5. Keep existing Naver spiders running while migrating incrementally.

## 2) Non-Goals

- Big-bang rewrite of all existing spiders/pipelines/models.
- Assuming Airflow/K8s/queues/object storage/metrics stack (allowed only as optional).
- Implementing downstream chunking/embedding/NLP (existing chunk tables remain unchanged).

## 3) Constraints and Current Coupling

- Pipelines currently write ORM directly (`pipelines/naver.py`, `pipelines/canonical.py` -> `database/models.py`) and depend on:
  - item field names
  - `response.meta` keys (`article_id`, `media_id`, etc.)
- Current state is mostly `latest_scraped_at` and date filters; no cursor/job tables.
- Duplicate control is partial (`naver_article_list` and `naver_research_reports` are insert-heavy).
- Middleware currently uses blocking `time.sleep` in reactor flow (risk for 1-minute polling + Playwright).

## 4) Target Architecture (Clean Architecture + Strangler)

### 4.1 Layering and dependency rules

Domain (pure)
- Entities/value objects: `SourceCode`, `ExternalId`, `Document`, `Cursor`, `RunStatus`, `FetchAttempt`
- Rules: stable external IDs; deterministic cursor advancement; idempotency keys per source/type

Application (use-cases)
- Orchestration without Scrapy/Playwright/SQLAlchemy imports
- Use-cases:
  - `Poll(source, cursor_key)`
  - `Backfill(source, partition_key)`
  - `UpsertDocument(document, blobs)`
  - `RecordAttempt(run_id, external_id, status, latency, error)`
  - `AcquireLease(cursor_key)` / `AdvanceCursor(cursor_key)`
- Ports: `DocumentRepo`, `BlobRepo`, `CursorRepo`, `RunRepo`, `AttemptRepo`, `Clock`

Infrastructure (adapters)
- SQLAlchemy repositories implementing upserts
- Scrapy adapters (spiders/pipelines) calling application services
- Playwright adapter (WiseReport extractor) called by application job

Entrypoints
- CLI jobs: `poll`, `backfill` (cron/systemd timer in MVP)

### 4.2 Incremental migration (strangler)

- Keep existing Naver spiders/pipelines initially.
- Add new canonical tables + job/cursor state.
- Convert legacy writes to idempotent (unique + upsert) before enabling 1-minute polling broadly.
- New sources (Hankyung/WiseReport) implement against the new canonical core from day 1.

### 4.3 Playwright integration decision (WiseReport)

Default for MVP: dedicated Playwright runner (not inside Scrapy reactor).
- Rationale: clearer lifecycle control, less Twisted coupling risk, easier concurrency caps.

Optional alternative: `scrapy-playwright` for WiseReport-only spiders if the site is simple render-then-parse.

## 5) Data Model (Alembic-managed)

### 5.1 New platform core tables (required)

1) `ingestion_sources`
- `source_code` (unique), `enabled`, timestamps

2) `ingestion_cursors`
- Uniqueness: (`source_code`, `cursor_key`)
- Fields:
  - `watermark_ts` (timestamptz), `watermark_id` (tie-breaker string)
  - `lookback_sec` (overlap window)
  - `state_json` (source-specific paging tokens)
  - lease: `lease_owner`, `lease_until`
  - `updated_at`

3) `ingestion_runs`
- One row per execution:
  - `source_code`, `job_type` (`POLL|BACKFILL`), `cursor_key`
  - `status` (`RUNNING|SUCCESS|FAILED|PARTIAL`)
  - `started_at`, `finished_at`
  - `stats_json`, `error_summary`, optional `host/pid`

4) `ingestion_fetch_attempts`
- Per fetch attempt:
  - `run_id`, `source_code`, `external_id`, `url`
  - `attempted_at`, `status` (`SUCCESS|RETRYABLE_FAIL|PERM_FAIL`)
  - `http_status`, `error_type`, `error_message` (truncate), `latency_ms`
  - optional `response_fingerprint` (content hash)

### 5.2 Canonical multi-source persistence (required)

5) `documents`
- Uniqueness: (`source_code`, `external_id`)
- Core fields:
  - `document_type` (`NEWS_ARTICLE`, `RESEARCH_REPORT`, `CONSENSUS_SNAPSHOT`)
  - `canonical_url`, `title`, `ticker` (nullable)
  - `published_at`, `modified_at` (timestamptz)
  - `language`, `content_text`, `content_hash`
  - `metadata_json` (jsonb)
  - `last_fetched_at`, `created_at`, `updated_at`

6) `document_blobs`
- Raw artifacts (HTML/PDF/JSON):
  - FK `document_id`
  - `blob_type`, `compression` (start with `LZMA` to match current practice)
  - `bytes`, `bytes_sha256`, `created_at`
- Versioning rule (pick one and enforce):
  - MVP recommended: unique (`document_id`, `blob_type`) and replace on change

### 5.3 Legacy tables: required idempotency upgrades

A) `naver_article_list`
- Add unique: (`ticker`, `category`, `media_id`, `article_id`)
- Add indexes:
  - (`latest_scraped_at`), (`article_published_at`), (`ticker`,`category`,`article_published_at`)

B) `naver_research_reports`
- Add unique: (`report_category`, `issuer_company_id`, `report_id`)

C) `naver_article_contents` uniqueness review
- Current unique on `article_id`; validate global uniqueness across `media_id`.
- If not guaranteed: migrate to unique (`media_id`, `article_id`).

### 5.4 External ID contract (mandatory)

All sources must define stable deterministic `external_id`:
- Naver News: `{media_id}:{article_id}`
- Naver Research: `{report_category}:{issuer_company_id}:{report_id}`
- Hankyung Consensus: source id preferred; else stable hash of canonical URL
- WiseReport: source id preferred; else stable hash of canonical URL

Acceptance: `external_id` derivable from a single fetch without DB lookups.

## 6) Scheduling and Workflows

### 6.1 Polling (every minute) workflow

Per (`source_code`, `cursor_key`):
1. Acquire cursor lease (`lease_until`), fail fast if held.
2. Create `ingestion_runs` row (RUNNING).
3. Compute time window:
   - `window_end = now()`
   - `window_start = watermark_ts - lookback`
   - apply per-source max scan cap (e.g., 24h)
4. Discovery step (list refs) in descending time order.
5. Detail fetch step (only refs needing insert/update):
   - missing document OR hash changed OR refresh TTL exceeded
6. Upsert into `documents` (+ `document_blobs`).
7. Record attempts in `ingestion_fetch_attempts`.
8. Advance cursor watermark to max processed `(published_at, external_id)`.
9. Close run with SUCCESS/FAILED/PARTIAL and `stats_json`.

Default lookback:
- Naver News: 15 min
- Research/Consensus/WiseReport: 60 min (tune after first week)

Sharding rule for SLA:
- If poll cannot complete in <60s, split into multiple `cursor_key` shards.

### 6.2 Backfill workflow (resumable partitions)

Partitioning (MVP):
- Time partition by day (`YYYY-MM-DD`) + optional shard suffix (ticker batch/section).

Per partition cursor:
1. Acquire lease, create run.
2. Fixed window = partition day range.
3. Discovery + detail + upsert as in polling.
4. Cursor state stores:
   - last `(published_at, external_id)` processed
   - paging tokens in `state_json` if needed
5. Mark partition complete when window fully processed.

Acceptance: kill/restart resumes without duplicates; rerun produces stable counts.

## 7) Failure Handling and Guardrails

### 7.1 Error classification
- RETRYABLE: 429/503, timeouts, transient network errors, Playwright navigation timeouts
- PERMANENT: 404 removed, deterministic parse failures after N retries, forbidden/auth failures

### 7.2 Retry policy (MVP)
- Max attempts per external_id per run (e.g., 3)
- Exponential backoff with jitter (or defer to next poll cycle in MVP)
- Circuit breaker:
  - if retryable failures exceed threshold in a run, mark PARTIAL and avoid unsafe watermark advance

### 7.3 Not-an-error normalization
- Do not persist control-flow as failures:
  - out-of-range or already-processed should be skip counters only.

### 7.4 Playwright stability guardrails
- Hard timeouts, low concurrency caps, deterministic shutdown
- Avoid global Scrapy reactor involvement in MVP

## 8) Observability (DB-first, optional metrics later)

Required outputs:
- `ingestion_runs` with `stats_json`:
  - discovered, fetched, inserted, updated, skipped, retryable_fail, perm_fail, duration_ms
- `ingestion_fetch_attempts` for every attempt with latency + classification
- Structured log fields:
  - `source_code`, `run_id`, `cursor_key`, `external_id`, `url`, `status`, `latency_ms`

Optional (post-MVP):
- Prometheus exporter / OpenTelemetry traces
- Alerts on: no-success polls for X minutes, sustained 429 spikes, cursor not advancing

## 9) Testing Strategy

1) Unit tests (required, fast)
- Domain: cursor advancement, external_id derivation, window computation, retry classification
- Application: lease logic (with fake repos), stats aggregation

2) Parsing tests (required, deterministic)
- Golden-file tests using saved HTML/JSON fixtures for:
  - Hankyung Consensus pages
  - WiseReport rendered HTML snapshots
- Assert extracted fields + external_id stability

3) DB integration tests (recommended)
- Upsert semantics: no duplicates on rerun; updates mutate allowed fields only
- Prefer ephemeral Postgres (docker) optional; otherwise dedicated local test DB

4) Smoke tests (required before rollout)
- Run one poll and one backfill partition in staging and validate:
  - run rows created
  - cursor advances only on success
  - idempotency by rerun

## 10) Phased Roadmap (P0/P1/P2/P3) - build order

### P0 (Foundation: idempotency + state + minimal jobs) - build first
1. Alembic: add core tables (`ingestion_*`, `documents`, `document_blobs`).
2. Alembic: add unique constraints/indexes to stop duplicates in legacy tables:
   - `naver_article_list`, `naver_research_reports`
   - decide/fix `naver_article_contents` uniqueness
3. Implement DB upsert capability for legacy writes.
4. Implement cursor lease + run/attempt recording.
5. Add CLI entrypoint skeleton: `poll`, `backfill` with no-op source.

P0 acceptance:
- Migrations apply on deduped staging DB.
- Re-running same Naver windows does not increase row counts.
- Poll job creates `ingestion_runs` and advances cursor only on success.

### P1 (Clean architecture core + Naver integration)
1. Introduce domain/application modules + repository ports.
2. Route at least one existing ingestion path through application service.
3. Replace control-flow failures with counters.
4. Implement poll orchestration for Naver (list->detail) without breaking existing spiders.

P1 acceptance:
- Naver poll runs minutely in staging with stable idempotent counts and visible runs/attempts.
- Cursor lease prevents overlap for same shard.

### P2 (New sources: Hankyung Consensus + WiseReport)
1. Hankyung Consensus spike (time-boxed): lock external_id + minimal field schema.
2. Implement Hankyung Scrapy extractor/pipeline using `documents` + cursor workflows.
3. Implement WiseReport Playwright extractor with `documents` + blobs + cursor workflows.
4. Tune lookback/max scan caps and shard strategy to meet 1-minute SLA.

P2 acceptance:
- Both new sources support backfill + 1-minute poll with idempotent persistence.
- WiseReport runs stable under concurrency caps; retries classified correctly.

### P3 (Unification, hardening, optional improvements)
1. Dual-write Naver outputs into `documents` (feature-flagged), then backfill canonical from legacy.
2. Operational hardening:
   - better backoff scheduling, replay of retryable failures, dashboarding
3. Optional infra:
   - object storage for blobs if DB size grows
   - distributed scheduler/queue if single-host cron is insufficient

P3 acceptance:
- Downstream can read from `documents` for all sources for a defined range with parity checks.

## 11) Rollout Plan

1) Staging-first DB migration:
- Run duplicate audit + dedupe before applying new unique constraints.
2) Deploy with new tables enabled but sources disabled by default (`ingestion_sources.enabled=false`).
3) Shadow mode:
- Run poll/backfill jobs writing run/cursor/attempt rows (and/or documents for new sources) without replacing legacy flow.
4) Enable idempotent upserts for legacy Naver tables (P0), monitor duplicates/errors.
5) Enable Hankyung then WiseReport in production with narrow scope/shards.
6) Expand scope gradually; add alert thresholds once stable.

Rollback strategy:
- Disable source via `ingestion_sources.enabled=false`; stop scheduling its cursor_keys.

## 12) Definition of Done

A. Functionality
- Hankyung Consensus (Scrapy) + WiseReport (Playwright) both support:
  - backfill (partitioned/resumable)
  - 1-minute polling (cursor + lookback)
- All ingestions persist to DB in `documents` (+ blobs when needed).

B. Idempotency
- Re-running same poll/backfill window does not create duplicates in:
  - `documents` (unique by source+external_id)
  - upgraded legacy tables
- Updates happen only on content/hash or mutable metadata change.

C. Operations
- Every run produces `ingestion_runs` + per-attempt rows.
- Cursor lease prevents overlapping runs on same shard.
- Retryable/permanent failures are visible and counted; control-flow skips are not stored as failures.

D. Quality
- Unit tests exist for core domain/application logic.
- Golden-file parsing tests exist for Hankyung and WiseReport.
- Staging smoke test demonstrates successful poll + backfill + rerun idempotency.

E. Documentation
- This SPEC remains current and includes runbook notes for:
  - enabling/disabling sources
  - shard strategy
  - dedupe procedure before unique constraints
