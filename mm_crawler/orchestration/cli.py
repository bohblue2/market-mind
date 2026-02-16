import argparse
import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from mm_crawler.config import settings
from mm_crawler.orchestration.runtime import StreamOrchestrator, build_default_streams


LOG = logging.getLogger(__name__)


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["poll", "backfill"],
        default="poll",
        help="execution mode",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="run one cycle and exit",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=settings.RUNNER_LOOP_INTERVAL_SECONDS,
        help="poll interval (seconds) while running forever",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="print due streams and stale lease state only",
    )
    parser.add_argument(
        "--recover-leases",
        action="store_true",
        help="release stale leases and mark stale runs as recovered",
    )
    parser.add_argument(
        "--lease-max-age",
        type=int,
        default=settings.RUNNER_LEASE_TTL_SECONDS,
        help="how old (seconds) a lease must be to be treated as stale",
    )
    parser.add_argument(
        "--run-max-age",
        type=int,
        default=3600,
        help="how old (seconds) RUNNING runs are marked failed on recovery",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit --check output as JSON",
    )
    parser.add_argument(
        "--from-date",
        help="backfill start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--to-date",
        help="backfill end date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--source",
        help="optional source filter (e.g. naver, hankyung_consensus)",
    )
    parser.add_argument(
        "--stream",
        help="optional stream filter (e.g. analysis.business, news.ticker_all)",
    )
    return parser


def emit_orchestrator_snapshot(snapshot: dict[str, Any], as_json: bool) -> None:
    if as_json:
        LOG.info("orchestrator snapshot: %s", json.dumps(snapshot, default=str))
        return

    print(f"collected_at: {snapshot['collected_at']}")
    print(f"poll_interval_seconds: {snapshot['poll_interval_seconds']}")
    print(f"enabled_stream_count: {snapshot['enabled_stream_count']}")
    print(f"due_stream_count: {snapshot['due_stream_count']}")
    if snapshot["due_stream_count"]:
        print("due_streams:")
        for stream in snapshot["due_streams"]:
            print(f"  - {stream}")
    stale = snapshot["stale_cursors"]
    if stale:
        print("stale_leases:")
        for item in stale:
            print(
                f"  - {item['source_code']}/{item['stream_key']} owner={item['lease_owner']} until={item['lease_until']}"
            )
    else:
        print("stale_leases: none")


def validate_iso_date(date_text: str) -> None:
    datetime.strptime(date_text, "%Y-%m-%d")


def run_orchestrator_cli() -> None:
    parser = build_cli_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    orchestrator = StreamOrchestrator(
        build_default_streams(), poll_interval_seconds=args.interval
    )

    if args.mode == "backfill":
        if not args.from_date or not args.to_date:
            parser.error("--mode backfill requires --from-date and --to-date")
        validate_iso_date(args.from_date)
        validate_iso_date(args.to_date)
        asyncio.run(
            orchestrator.run_backfill_once(
                from_date=args.from_date,
                to_date=args.to_date,
                source_code=args.source,
                stream_key=args.stream,
            )
        )
        return

    if args.check:
        snapshot = orchestrator.get_stream_snapshot()
        emit_orchestrator_snapshot(snapshot, as_json=args.json)
        return

    if args.recover_leases:
        stale_leases = orchestrator.recover_stale_leases(
            max_lease_age_seconds=args.lease_max_age
        )
        stale_runs = orchestrator.recover_stale_runs(
            max_running_age_seconds=args.run_max_age
        )
        LOG.info(
            "recovery complete: cleared %s stale leases, marked %s stale runs failed",
            stale_leases,
            stale_runs,
        )
        return

    if args.once:
        asyncio.run(orchestrator.run_once())
        return

    asyncio.run(orchestrator.run_forever())


main = run_orchestrator_cli


if __name__ == "__main__":
    run_orchestrator_cli()
