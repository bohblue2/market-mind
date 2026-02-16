from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, Optional

from scrapy.crawler import AsyncCrawlerRunner
from scrapy.utils.project import get_project_settings
from sqlalchemy import or_, update

from mm_crawler.config import settings
from mm_crawler.constant import KST
from mm_crawler.database.models import CrawlRunOrm, IngestionEventOrm, SourceCursorOrm
from mm_crawler.database.session import SessionLocal

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _build_window_from_cursor(
    cursor_value: Optional[str], now: datetime, default_lookback: int
) -> tuple[datetime, datetime]:
    if cursor_value:
        start = datetime.fromisoformat(cursor_value)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
    else:
        start = now - timedelta(seconds=default_lookback)
    return start, now


def _to_date_str(value: datetime) -> str:
    return value.astimezone(KST).strftime("%Y-%m-%d")


@dataclass(frozen=True)
class StreamSpec:
    source_code: str
    stream_key: str
    spider_name: str
    interval_seconds: int
    lookback_seconds: int
    lease_seconds: int
    build_kwargs: Callable[[Dict[str, Optional[str]]], Dict[str, Any]]
    run_type: str = "POLL"
    enabled: bool = True


class OrchestrationError(RuntimeError):
    pass


class StreamOrchestrator:
    def __init__(
        self, stream_specs: Iterable[StreamSpec], poll_interval_seconds: int = 5
    ):
        self.stream_specs = list(stream_specs)
        self.poll_interval_seconds = max(poll_interval_seconds, 1)
        self.crawler_settings = get_project_settings()

    async def run_forever(self) -> None:
        logger.info("starting stream orchestrator")

        while True:
            due_streams = self._collect_due_streams()
            if not due_streams:
                await asyncio.sleep(self.poll_interval_seconds)
                continue

            await asyncio.gather(
                *(self._run_stream(spec) for spec in due_streams),
                return_exceptions=True,
            )
            await asyncio.sleep(self.poll_interval_seconds)

    async def run_once(self) -> None:
        logger.info("running single pass for all enabled streams")
        await asyncio.gather(
            *(self._run_stream(spec) for spec in self.stream_specs if spec.enabled),
            return_exceptions=True,
        )

    async def run_backfill_once(
        self,
        from_date: str,
        to_date: str,
        source_code: Optional[str] = None,
        stream_key: Optional[str] = None,
    ) -> None:
        stream_specs = [spec for spec in self.stream_specs if spec.enabled]

        if source_code:
            stream_specs = [
                spec for spec in stream_specs if spec.source_code == source_code
            ]
        if stream_key:
            stream_specs = [
                spec for spec in stream_specs if spec.stream_key == stream_key
            ]

        if not stream_specs:
            raise OrchestrationError(
                "no stream matched source/stream filters for backfill"
            )

        await asyncio.gather(
            *(
                self._run_stream(
                    replace(spec, run_type="BACKFILL"),
                    forced_window={"from_date": from_date, "to_date": to_date},
                    advance_cursor=False,
                    schedule_next_run=False,
                )
                for spec in stream_specs
            ),
            return_exceptions=True,
        )

    def get_stream_snapshot(self) -> dict[str, object]:
        now = utcnow()
        due_streams = self._collect_due_streams()
        stale_cursors = self._collect_stale_cursors(now=now)

        return {
            "collected_at": now.isoformat(),
            "poll_interval_seconds": self.poll_interval_seconds,
            "enabled_stream_count": len([s for s in self.stream_specs if s.enabled]),
            "due_stream_count": len(due_streams),
            "due_streams": [f"{s.source_code}/{s.stream_key}" for s in due_streams],
            "stale_cursors": [
                {
                    "source_code": row.source_code,
                    "stream_key": row.stream_key,
                    "lease_owner": row.lease_owner,
                    "lease_until": row.lease_until.isoformat()
                    if row.lease_until
                    else None,
                    "age_seconds": (now - row.lease_until).total_seconds()
                    if row.lease_until
                    else None,
                }
                for row in stale_cursors
            ],
        }

    def recover_stale_leases(self, max_lease_age_seconds: int = 300) -> int:
        cutoff = utcnow() - timedelta(seconds=max_lease_age_seconds)
        with SessionLocal() as session:
            stale = (
                session.query(SourceCursorOrm)
                .filter(
                    SourceCursorOrm.lease_owner.is_not(None),
                    SourceCursorOrm.lease_until <= cutoff,
                )
                .all()
            )
            for row in stale:
                row.lease_owner = None
                row.lease_until = None
                row.updated_at = utcnow()
            session.commit()
            return len(stale)

    def recover_stale_runs(self, max_running_age_seconds: int = 3600) -> int:
        cutoff = utcnow() - timedelta(seconds=max_running_age_seconds)
        recovered = 0
        with SessionLocal() as session:
            running_rows = (
                session.query(CrawlRunOrm)
                .filter(
                    CrawlRunOrm.status == "RUNNING",
                    CrawlRunOrm.started_at <= cutoff,
                )
                .all()
            )
            for row in running_rows:
                row.status = "FAILED"
                row.completed_at = utcnow()
                if row.error_message is None:
                    row.error_message = "recovered by manual recovery"
                recovered += 1
            session.commit()
        return recovered

    def _collect_due_streams(self) -> list[StreamSpec]:
        now = utcnow()
        due_streams: list[StreamSpec] = []

        with SessionLocal() as session:
            for spec in self.stream_specs:
                if not spec.enabled:
                    continue

                cursor = (
                    session.query(SourceCursorOrm)
                    .filter_by(source_code=spec.source_code, stream_key=spec.stream_key)
                    .one_or_none()
                )

                if cursor is None:
                    self._create_cursor(session, spec, now)
                    due_streams.append(spec)
                    continue

                if cursor.next_run_at is None or cursor.next_run_at <= now:
                    due_streams.append(spec)

        return due_streams

    async def _run_stream(
        self,
        spec: StreamSpec,
        forced_window: Optional[Dict[str, str]] = None,
        advance_cursor: bool = True,
        schedule_next_run: bool = True,
    ) -> None:
        owner = f"worker-{uuid.uuid4().hex[:12]}"
        run_id: Optional[int] = None

        with SessionLocal() as session:
            now = utcnow()
            cursor_row = self._acquire_lease(session, spec, owner, now)
            if cursor_row is None:
                logger.info("skip %s/%s: lease held", spec.source_code, spec.stream_key)
                return

            cursor_value = cursor_row.cursor_value

            run = CrawlRunOrm(
                source_code=spec.source_code,
                stream_key=spec.stream_key,
                run_type=spec.run_type,
                status="RUNNING",
            )
            session.add(run)
            session.flush()
            run_id = run.id

            self._append_event(
                session,
                run,
                spec,
                event_type="run.start",
                status="RUNNING",
                message="crawler start",
            )
            session.commit()

        try:
            if forced_window is not None:
                kwargs = spec.build_kwargs(
                    {
                        "from_date": forced_window["from_date"],
                        "to_date": forced_window["to_date"],
                    }
                )
                run_window_end = utcnow()
            else:
                start, end = _build_window_from_cursor(
                    cursor_value=cursor_value,
                    now=utcnow(),
                    default_lookback=spec.lookback_seconds,
                )

                kwargs = spec.build_kwargs(
                    {
                        "from_date": _to_date_str(start),
                        "to_date": _to_date_str(end),
                    }
                )
                run_window_end = end

            runner = AsyncCrawlerRunner(self.crawler_settings)
            await runner.crawl(spec.spider_name, **kwargs)
            await runner.join()

            with SessionLocal() as session:
                run = session.get(CrawlRunOrm, run_id)
                if run is not None:
                    run.status = "SUCCESS"
                    run.completed_at = utcnow()
                    session.add(run)
                    self._append_event(
                        session,
                        run,
                        spec,
                        event_type="run.success",
                        status="SUCCESS",
                        message=f"crawler success for {spec.spider_name}",
                    )

                if advance_cursor:
                    self._update_cursor_after_success(
                        session, spec, new_cursor_value=run_window_end
                    )
                session.commit()

            logger.info(
                "stream completed %s/%s status=SUCCESS",
                spec.source_code,
                spec.stream_key,
            )
        except Exception as exc:
            logger.exception("stream failed %s/%s", spec.source_code, spec.stream_key)
            with SessionLocal() as session:
                run = session.get(CrawlRunOrm, run_id)
                if run is not None:
                    run.status = "FAILED"
                    run.completed_at = utcnow()
                    run.error_message = str(exc)
                    session.add(run)
                    self._append_event(
                        session,
                        run,
                        spec,
                        event_type="run.failed",
                        status="FAILED",
                        message=str(exc),
                    )
                    session.commit()
            raise OrchestrationError(
                f"stream failed {spec.source_code}:{spec.stream_key}"
            ) from exc
        finally:
            with SessionLocal() as session:
                self._release_lease(session, spec, owner)
                if schedule_next_run:
                    self._set_next_run_at(session, spec)
                run = session.get(CrawlRunOrm, run_id)
                if run is not None and run.status == "RUNNING":
                    run.status = "PARTIAL"
                    run.completed_at = utcnow()
                    session.add(run)
                session.commit()

    def _collect_stale_cursors(self, now: datetime) -> list[SourceCursorOrm]:
        cutoff = now - timedelta(seconds=self.poll_interval_seconds * 2)
        with SessionLocal() as session:
            return (
                session.query(SourceCursorOrm)
                .filter(
                    SourceCursorOrm.lease_owner.is_not(None),
                    SourceCursorOrm.lease_until <= cutoff,
                )
                .all()
            )

    def _create_cursor(
        self, session, spec: StreamSpec, now: datetime
    ) -> SourceCursorOrm:
        row = SourceCursorOrm(
            source_code=spec.source_code,
            stream_key=spec.stream_key,
            cursor_type="time",
            cursor_value=None,
            lookback_sec=spec.lookback_seconds,
            next_run_at=now,
            state_json={"created_by_orchestrator": True},
        )
        session.add(row)
        session.flush()
        return row

    def _acquire_lease(
        self,
        session,
        spec: StreamSpec,
        owner: str,
        now: datetime,
    ) -> Optional[SourceCursorOrm]:
        cursor = (
            session.query(SourceCursorOrm)
            .filter_by(source_code=spec.source_code, stream_key=spec.stream_key)
            .one_or_none()
        )

        if cursor is None:
            cursor = self._create_cursor(session, spec, now)
            session.flush()

        updated = session.execute(
            update(SourceCursorOrm)
            .where(
                SourceCursorOrm.id == cursor.id,
                or_(
                    SourceCursorOrm.lease_until.is_(None),
                    SourceCursorOrm.lease_until <= now,
                ),
            )
            .values(
                lease_owner=owner,
                lease_until=now + timedelta(seconds=spec.lease_seconds),
                last_started_at=now,
                updated_at=utcnow(),
            )
            .returning(SourceCursorOrm.id)
        ).first()

        if updated is None:
            session.commit()
            return None

        session.commit()
        session.refresh(cursor)
        return cursor

    def _release_lease(self, session, spec: StreamSpec, owner: str) -> None:
        cursor = (
            session.query(SourceCursorOrm)
            .filter_by(
                source_code=spec.source_code,
                stream_key=spec.stream_key,
                lease_owner=owner,
            )
            .one_or_none()
        )
        if cursor is None:
            return

        cursor.lease_owner = None
        cursor.lease_until = None
        cursor.last_completed_at = utcnow()
        cursor.updated_at = utcnow()

    def _set_next_run_at(self, session, spec: StreamSpec) -> None:
        cursor = (
            session.query(SourceCursorOrm)
            .filter_by(source_code=spec.source_code, stream_key=spec.stream_key)
            .one_or_none()
        )
        if cursor is None:
            return

        cursor.next_run_at = utcnow() + timedelta(seconds=spec.interval_seconds)

    def _append_event(
        self,
        session,
        run: Optional[CrawlRunOrm],
        spec: StreamSpec,
        event_type: str,
        status: str,
        message: str,
    ) -> None:
        if run is None:
            return

        session.add(
            IngestionEventOrm(
                run_id=run.id,
                source_code=spec.source_code,
                stream_key=spec.stream_key,
                external_id=None,
                event_type=event_type,
                status=status,
                message=message,
            )
        )

    def _update_cursor_after_success(
        self,
        session,
        spec: StreamSpec,
        new_cursor_value: datetime,
    ) -> None:
        cursor = (
            session.query(SourceCursorOrm)
            .filter_by(source_code=spec.source_code, stream_key=spec.stream_key)
            .one_or_none()
        )
        if cursor is None:
            return

        cursor.cursor_value = new_cursor_value.isoformat()
        cursor.updated_at = utcnow()
        cursor.last_completed_at = utcnow()


def build_default_streams() -> list[StreamSpec]:
    streams: list[StreamSpec] = []

    enabled_sources = {
        entry.strip() for entry in settings.ENABLED_SOURCES.split(",") if entry.strip()
    }

    if "naver" in enabled_sources:
        streams.append(
            StreamSpec(
                source_code="naver",
                stream_key="news.ticker_all",
                spider_name="naver_news_list",
                interval_seconds=max(
                    60, settings.NAVER_TICKER_ALL_INTERVAL_MINUTES * 60
                ),
                lookback_seconds=max(
                    600, settings.NAVER_TICKER_ALL_INTERVAL_MINUTES * 60
                ),
                lease_seconds=settings.RUNNER_LEASE_TTL_SECONDS,
                build_kwargs=lambda window: {
                    "ticker": "all",
                    "from_date": window["from_date"],
                    "to_date": window["to_date"],
                },
            )
        )

    if "hankyung_consensus" in enabled_sources:
        skin_types = [
            entry.strip()
            for entry in settings.HK_SKIN_TYPES.split(",")
            if entry.strip()
        ]
        for skin_type in skin_types:
            streams.append(
                StreamSpec(
                    source_code="hankyung_consensus",
                    stream_key=f"analysis.{skin_type}",
                    spider_name="hankyung_consensus_list",
                    interval_seconds=max(60, settings.HK_POLL_INTERVAL_MINUTES * 60),
                    lookback_seconds=max(3600, settings.HK_POLL_INTERVAL_MINUTES * 60),
                    lease_seconds=settings.RUNNER_LEASE_TTL_SECONDS,
                    build_kwargs=lambda window, skin_type=skin_type: {
                        "skin_type": skin_type,
                        "recent_pages": str(settings.HK_INCREMENTAL_RECENT_PAGES),
                        "order_type": settings.HK_ORDER_TYPE,
                        "from_date": window["from_date"],
                        "to_date": window["to_date"],
                    },
                )
            )

    return streams
