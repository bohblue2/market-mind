import asyncio
from datetime import datetime
import os
import re
from enum import Enum
from typing import Any, Dict

import pytz  # type: ignore
import requests
import scrapy
from scrapy.http import HtmlResponse

from mm_crawler.items import ArticleItem, NaverArticleListFailedItem

kst = pytz.timezone('Asia/Seoul')

class NaverArticleErrorEnum(Enum):
    # Fatal errors
    MISSING_FIELD_EXISTS = "Missing field exists"
    END_OF_PAGE = "End of page reached"
    NO_CONTENT = "No content found"

    # Non-fatal errors(skip the article)
    OUT_OF_DATE_RANGE = "Out of date range"
    PROCESSED_ID_EXISTS = "Processed ID exists"
    
    FATAL_ERROR = "Fatal error"
    NON_FATAL_ERROR = "Non-fatal error"

class NaverNewsArticleList(scrapy.Spider):
    name = os.path.basename(__file__).replace('.py', '')
    allowed_domains = ['naver.com']
    custom_settings = {
        "ITEM_PIPELINES": {"mm_crawler.pipelines.FinanceNewsListPipeline": 1},
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
            "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
            "scrapy_fake_useragent.middleware.RandomUserAgentMiddleware": 400,
            "scrapy_fake_useragent.middleware.RetryUserAgentMiddleware": 401,
        },
        "FAKEUSERAGENT_PROVIDERS": [
            "scrapy_fake_useragent.providers.FakerProvider",
            "scrapy_fake_useragent.providers.FakeUserAgentProvider",
            "scrapy_fake_useragent.providers.FixedUserAgentProvider",
        ],
    }

    def __init__(self, ticker: str, from_date: str, to_date: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticker = ticker
        self.from_date = kst.localize(datetime.strptime(from_date.strip(), "%Y-%m-%d"))
        self.to_date = kst.localize(datetime.strptime(to_date.strip(), "%Y-%m-%d"))

    def start_requests(self):
        tickers = self._fetch_tickers()
        self.log(f"Extracted {len(tickers)} tickers from API")
        if self.ticker in tickers:
            yield self._create_request(self.ticker)

    async def parse(self, response: HtmlResponse) -> Any:
        meta = response.meta
        current_page = meta['page']

        # TODO: Implement a way to handle the case when the page is not vaild.
        
        if self._is_end_of_page(response):
            yield await self._handle_error(NaverArticleErrorEnum.END_OF_PAGE, response)
            return

        processed_ids: set[str] = set()
        for row in response.css('table.type5 tr'):
            if row.css('th::text').get() == "제목":
                self.log("Skipping header row")
                continue

            article_data = self._extract_article_data(meta.get('ticker', "None"), row, processed_ids)
            # TODO: 특정 date range에 해당하는 article이 없을 때 몇 번째 페이지 까지 찾아볼지 정해야 함.
            if isinstance(article_data, NaverArticleErrorEnum):
                ret = await self._handle_error(article_data, response)
                yield ret
                if ret.get('is_fatal', False) is True:
                    return
            else:
                yield ArticleItem(**article_data)
        yield self._create_next_page_request(meta, current_page)

    def _fetch_tickers(self, limit:int = 5000) -> list:
        response = requests.get(f"http://127.0.0.1:8080/api/securities/code?tr_code=t8436&limit={limit}")
        return [ticker['shcode'] for ticker in response.json() if not ticker['shcode'].endswith('K')]

    def _create_request(self, ticker: str) -> scrapy.Request:
        return scrapy.Request(
            self._get_target_url(ticker),
            headers=self._get_headers(ticker),
            meta={'ticker': ticker, 'page': 1},
            callback=self.parse,
            errback=self.errback,
        )

    @classmethod
    def _get_target_url(cls, ticker: str, page: int = 1) -> str:
        return f"https://finance.naver.com/item/news_news.naver?code={ticker}&page={page}"

    @classmethod
    def _get_headers(cls, ticker: str) -> Dict[str, str]:
        return {
            "Referer": f"https://finance.naver.com/item/news.naver?code={ticker}",
            "Accept": "application/json, text/plain, */*",
        }

    def _is_end_of_page(self, response: HtmlResponse) -> bool:
        info_text_area = response.css('div').get()
        return not info_text_area or '없습니다.' in info_text_area

    def _extract_article_data(self, ticker: str, row, processed_ids: set) -> Dict[str, Any] | NaverArticleErrorEnum:
        content_url = row.css('td.title a::attr(href)').extract_first()
        title = row.css('td.title a::text').get()
        source = row.css('td.info::text').get()
        date = row.css('td.date::text').get()

        if not content_url or not title or not source or not date:
            return NaverArticleErrorEnum.MISSING_FIELD_EXISTS

        article_id, office_id = self._extract_article_and_office_ids(content_url)
        if not article_id or not office_id or f"{office_id}{article_id}" in processed_ids:
            return NaverArticleErrorEnum.PROCESSED_ID_EXISTS 

        article_published_at = kst.localize(datetime.strptime(date.strip(), "%Y.%m.%d %H:%M"))
        if article_published_at < self.from_date or article_published_at > self.to_date:
            return NaverArticleErrorEnum.OUT_OF_DATE_RANGE 

        processed_ids.add(f"{office_id}{article_id}")
        self.log(f"Article ID: {article_id}, Office ID: {office_id}")

        row_class = row.attrib.get('class', '')
        is_relation_origin = 'relation_tit' in row_class
        is_related = 'relation_lst' in row_class
        relation_origin_id = self._get_relation_origin_id(row_class, is_related)

        return {
            'ticker': ticker,
            'article_id': article_id,
            'media_id': office_id,
            'media_name': source,
            'title': title,
            'link': content_url,
            'article_published_at': date,
            'is_origin': is_relation_origin,
            'origin_id': relation_origin_id if is_related else None,
        }

    def _get_relation_origin_id(self, row_class: str, is_related: bool) -> str:
        if is_related:
            rel_office_id, rel_article_id = self._extract_cluster_ids(row_class)
            if rel_office_id and rel_article_id:
                self.log(f"Office ID: {rel_office_id}, News ID: {rel_article_id}")
            return f"{rel_office_id}{rel_article_id}"
        return ''

    def _create_next_page_request(self, meta: Dict[str, Any], current_page: int) -> scrapy.Request:
        return scrapy.Request(
            self._get_target_url(meta['ticker'], current_page + 1),
            headers=self._get_headers(meta['ticker']),
            meta={'ticker': meta['ticker'], 'page': current_page + 1},
            callback=self.parse,
            errback=self.errback,
        )

    def _extract_cluster_ids(self, row_class: str) -> tuple:
        match = re.search(r'_clusterId(\d{3})(\d+)', row_class)
        return match.groups() if match else (None, None)

    def _extract_article_and_office_ids(self, content_url: str) -> tuple:
        match = re.search(r'article_id=(\d+)&office_id=(\d+)', content_url)
        return match.groups() if match else (None, None)

    async def _handle_error(self, error_code: NaverArticleErrorEnum, response: HtmlResponse) -> NaverArticleListFailedItem:
        if error_code in [
            NaverArticleErrorEnum.MISSING_FIELD_EXISTS,
            NaverArticleErrorEnum.END_OF_PAGE,
            NaverArticleErrorEnum.NO_CONTENT
        ]:
            return NaverArticleListFailedItem(
                ticker=response.meta['ticker'],
                error_code=error_code,
                response=response,
                created_at=datetime.now(),
                is_fatal=True
            )
        elif error_code in [
            NaverArticleErrorEnum.OUT_OF_DATE_RANGE,
            NaverArticleErrorEnum.PROCESSED_ID_EXISTS
        ]:
            return NaverArticleListFailedItem(
                ticker=response.meta['ticker'],
                error_code=error_code,
                response=response,
                created_at=datetime.now(),
                is_fatal=False
            )
        else:
            return NaverArticleListFailedItem(
                ticker=response.meta['ticker'],
                error_code=NaverArticleErrorEnum.FATAL_ERROR,
                response=response,
                created_at=datetime.now(),
                is_fatal=True
            )

    def errback(self, failure: Any) -> None:
        self.log(f"Errback: [{type(failure)}]{failure}")