# Source Platform Rollout

- [ ] Consolidate orchestration to one active path (`run_orchestrator.py` + `stream_orchestrator.py`), keep compatibility shim only.
- [ ] Wire config-driven stream registry into `default_streams()`.
- [ ] Add Hankyung stream set (`skinType` 6 variants) with `HK_INCREMENTAL_RECENT_PAGES` parameter.
- [ ] Set Naver all-ticker news polling cadence to `NAVER_TICKER_ALL_INTERVAL_MINUTES` (default 10).
- [ ] Remove/resolve duplicate Alembic revision path so schema history has one canonical upgrade branch.
- [ ] Verify modified modules compile and basic diagnostics are clean.
