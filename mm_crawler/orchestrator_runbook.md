# Orchestrator Runbook

## 1) What this runbook covers
- Stream-first scheduler in `orchestration/runtime.py` and CLI in `orchestration/cli.py`
- Startup behavior, one-shot polling, stale lease/run recovery, and safe restarts

## 2) Default scheduler behavior
- `orchestration/cli.py` builds default stream definitions from `build_default_streams()` in `orchestration/runtime.py`.
- The loop wakes every `--interval` seconds, then:
  - finds cursors whose `next_run_at` is null or in the past,
  - tries to acquire a lease using `lease_owner` + `lease_until`,
  - creates a `crawl_runs` row with `status=RUNNING`,
  - runs the spider for that stream,
  - writes `run.start`, `run.success`, or `run.failed` events,
  - updates `source_cursors.next_run_at` only after successful completion.

## 3) Recommended bootstrap steps
1. Apply migrations and initialize schema before first run.
2. Start the orchestrator in check mode first:
   - `python -m mm_crawler.orchestration.cli --check [--json]`
3. Confirm cursors are created and expected streams are shown as due.
4. Start loop mode:
   - `python -m mm_crawler.orchestration.cli --interval 5`
5. Keep an eye on the periodic checkpoint output from your process logs.

## 4) Recovery from stale state
### Clear stale leases
- Use: `python -m mm_crawler.orchestration.cli --recover-leases`
- This clears `source_cursors.lease_owner` where `lease_until` is older than `--lease-max-age`.

### Mark stale running runs failed
- Same command also marks `crawl_runs` with `status='RUNNING'` older than `--run-max-age` to `FAILED`.

### Why recovery helps
- If the process crashes mid-run, leases may remain held and block rerun.
- Recovery allows another scheduler cycle to reacquire that stream and continue.

## 5) Restart sequence
- On normal shutdown, the process releases leases in `finally`, so restart usually resumes naturally.
- On hard crash or kill:
  1. Start with `--check` to inspect stale leases and due streams.
  2. Run `--recover-leases` if needed.
  3. Start loop mode.

## 6) One-shot and dry-run style execution
- Run one pass (all enabled streams once): `python -m mm_crawler.orchestration.cli --once`
- Useful for quick validation without leaving a long-running loop.

## 7) Notes and caveats
- `orchestration/runtime.py` is currently wired to a small, hardcoded seed set of streams. Expand `build_default_streams()` as your source set grows.
- Legacy wrappers remain available:
  - `run_orchestrator.py` forwards to `orchestration/cli.py`
  - `stream_orchestrator.py` re-exports runtime symbols
  - `orchestrator.py` forwards to `orchestration/cli.py`
