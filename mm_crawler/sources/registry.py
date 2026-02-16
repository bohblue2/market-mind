from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from mm_crawler.config import settings


@dataclass(frozen=True)
class StreamPlan:
    source_code: str
    stream_key: str
    spider_name: str
    interval_minutes: int
    args: dict[str, str]


def enabled_sources() -> set[str]:
    return {
        entry.strip() for entry in settings.ENABLED_SOURCES.split(",") if entry.strip()
    }


def build_stream_plans(target_date: str) -> List[StreamPlan]:
    plans: List[StreamPlan] = []
    sources = enabled_sources()
    day = datetime.strptime(target_date, "%Y-%m-%d")
    from_date = day.strftime("%Y-%m-%d")
    to_date = (day + timedelta(days=1)).strftime("%Y-%m-%d")

    if "naver" in sources:
        plans.append(
            StreamPlan(
                source_code="naver",
                stream_key="news.ticker_all",
                spider_name="naver_news_list",
                interval_minutes=settings.NAVER_TICKER_ALL_INTERVAL_MINUTES,
                args={
                    "ticker": "all",
                    "from_date": from_date,
                    "to_date": to_date,
                },
            )
        )

    if "hankyung_consensus" in sources:
        for skin_type in [
            entry.strip()
            for entry in settings.HK_SKIN_TYPES.split(",")
            if entry.strip()
        ]:
            plans.append(
                StreamPlan(
                    source_code="hankyung_consensus",
                    stream_key=f"analysis.{skin_type}",
                    spider_name="hankyung_consensus_list",
                    interval_minutes=settings.HK_POLL_INTERVAL_MINUTES,
                    args={
                        "skin_type": skin_type,
                        "recent_pages": str(settings.HK_INCREMENTAL_RECENT_PAGES),
                        "order_type": settings.HK_ORDER_TYPE,
                        "from_date": from_date,
                        "to_date": to_date,
                    },
                )
            )

    return plans
