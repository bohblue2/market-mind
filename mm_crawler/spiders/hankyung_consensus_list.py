import os
import re
from datetime import datetime
from typing import Iterable, Optional
from urllib.parse import urljoin

import pytz  # type: ignore
import scrapy
from bs4 import BeautifulSoup
from scrapy.http import HtmlResponse, Request

from mm_crawler.items import HankyungConsensusItem


KST = pytz.timezone("Asia/Seoul")
SKIN_TYPES = {"business", "market", "derivative", "economy", "stock_good", "stock_bad"}


class HankyungConsensusList(scrapy.Spider):
    name = os.path.basename(__file__).replace(".py", "")
    allowed_domains = ["consensus.hankyung.com"]
    custom_settings = {
        "ITEM_PIPELINES": {"mm_crawler.pipelines.CanonicalDocumentPipeline": 1},
    }

    def __init__(
        self,
        skin_type: str,
        from_date: str,
        to_date: str,
        recent_pages: int = 2,
        order_type: str = "12000000",
        pagenum: int = 80,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if skin_type not in SKIN_TYPES:
            raise ValueError(f"Unsupported skin_type: {skin_type}")
        self.skin_type = skin_type
        self.from_date = datetime.strptime(from_date.strip(), "%Y-%m-%d")
        self.to_date = datetime.strptime(to_date.strip(), "%Y-%m-%d")
        self.recent_pages = max(1, int(recent_pages))
        self.order_type = order_type
        self.pagenum = int(pagenum)

    def start_requests(self) -> Iterable[Request]:
        for page in range(1, self.recent_pages + 1):
            yield Request(
                self._build_url(page),
                callback=self.parse_list,
                errback=self.errback,
                meta={"page": page},
            )

    def _build_url(self, now_page: int) -> str:
        return (
            "https://consensus.hankyung.com/analysis/list"
            f"?skinType={self.skin_type}"
            f"&sdate={self.from_date.strftime('%Y-%m-%d')}"
            f"&edate={self.to_date.strftime('%Y-%m-%d')}"
            f"&pagenum={self.pagenum}"
            f"&order_type={self.order_type}"
            f"&now_page={now_page}"
        )

    def parse_list(self, response: HtmlResponse):
        soup = BeautifulSoup(response.text, "html.parser")
        for anchor in soup.select("a[href]"):
            href = anchor.get("href")
            if not href:
                continue
            if not isinstance(href, str):
                continue
            if "analysis" not in href:
                continue
            external_id = self._extract_external_id(href)
            if external_id is None:
                continue

            detail_url = urljoin(response.url, href)
            title = anchor.get_text(strip=True)
            published_at = self._extract_published_at(anchor)

            yield Request(
                detail_url,
                callback=self.parse_detail,
                errback=self.errback,
                meta={
                    "external_id": f"{self.skin_type}:{external_id}",
                    "canonical_url": detail_url,
                    "title": title,
                    "published_at": published_at,
                    "skin_type": self.skin_type,
                },
            )

    def parse_detail(self, response: HtmlResponse):
        soup = BeautifulSoup(response.text, "html.parser")
        content_node = (
            soup.select_one("#contents")
            or soup.select_one(".article")
            or soup.select_one(".view_cont")
            or soup.select_one("body")
        )
        content_text = (
            content_node.get_text(" ", strip=True) if content_node is not None else ""
        )
        metadata = {
            "skin_type": response.meta["skin_type"],
            "url": response.meta["canonical_url"],
            "raw_length": len(response.text),
        }

        yield HankyungConsensusItem(
            source_code="hankyung_consensus",
            stream_key=f"analysis.{response.meta['skin_type']}",
            external_id=response.meta["external_id"],
            canonical_url=response.meta["canonical_url"],
            title=response.meta["title"],
            published_at=response.meta.get("published_at"),
            content_text=content_text,
            metadata_json=metadata,
            skin_type=response.meta["skin_type"],
        )

    def _extract_external_id(self, href: str) -> Optional[str]:
        candidates = [
            r"[?&]id=(\d+)",
            r"[?&]seq=(\d+)",
            r"/analysis/[^/]+/(\d+)",
            r"/(\d+)\.html",
        ]
        for pattern in candidates:
            match = re.search(pattern, href)
            if match:
                return match.group(1)
        return None

    def _extract_published_at(self, anchor) -> Optional[datetime]:
        text_block = " ".join(anchor.parent.get_text(" ", strip=True).split())
        for pattern in (
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{4}\.\d{2}\.\d{2})",
            r"(\d{2}\.\d{2}\.\d{2})",
        ):
            match = re.search(pattern, text_block)
            if not match:
                continue
            raw = match.group(1)
            for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%y.%m.%d"):
                try:
                    return KST.localize(datetime.strptime(raw, fmt))
                except ValueError:
                    continue
        return None

    def errback(self, failure):
        self.logger.error(f"Hankyung request failed: {failure}")
