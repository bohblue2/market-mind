import asyncio
import os
import re
import time
from enum import Enum
from typing import Any, Dict

import requests
import scrapy
from scrapy.http.response.html import HtmlResponse

from mm_crawler.items import ArticleItem


class NaverArticleErrorEnum(Enum):
    END_OF_PAGE = "End of page reached"
    NO_CONTENT = "No content found"


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

    def start_requests(self):
        self.tickers = self._fetch_tickers()
        self.log(f"Extracted {len(self.tickers)} tickers from API")

        for ticker in self.tickers:
            # TODO: 
            time.sleep(1)
            yield self._create_request(ticker)

    def _fetch_tickers(self):
        response = requests.get("http://127.0.0.1:8080/api/securities/code?tr_code=t8436")
        tickers = [ticker['shcode'] for ticker in response.json()]
        return [ticker for ticker in tickers if not ticker.endswith('K')]

    def _create_request(self, ticker):
        target_url = self._get_target_url(ticker)
        return scrapy.Request(
            target_url,
            headers=self._get_headers(ticker),
            meta={'ticker': ticker, 'page': 1},
            callback=self.parse,
            errback=self.errback,
        )

    @classmethod
    def _get_target_url(cls, ticker: str, page: int = 1):
        return f"https://finance.naver.com/item/news_news.naver?code={ticker}&page={page}"

    @classmethod
    def _get_headers(cls, ticker: str) -> Dict[str, str]:
        return {
            "Referer": f"https://finance.naver.com/item/news.naver?code={ticker}",
            "Accept": "application/json, text/plain, */*",
        }

    async def parse(self, response: HtmlResponse):
        meta = response.meta
        current_page = meta['page']

        if self._is_end_of_page(response):
            yield await self.handle_error(NaverArticleErrorEnum.END_OF_PAGE, response)

        processed_ids: set[str] = set()
        for row in response.css('table.type5 tr'):
            article_data = self._extract_article_data(meta.get('ticker', "None"), row, processed_ids)
            if not article_data:
                yield await self.handle_error(NaverArticleErrorEnum.NO_CONTENT, response)
            else:
                yield ArticleItem(**article_data)

        yield self._create_next_page_request(meta, current_page)

    def _is_end_of_page(self, response):
        info_text_area = response.css('div').get()
        is_end_of_page = False

        if not info_text_area:
            is_end_of_page = True
        if info_text_area and '없습니다.' in info_text_area:
            is_end_of_page = True

        return is_end_of_page

    def _extract_article_data(self, ticker, row, processed_ids):
        content_url = row.css('td.title a::attr(href)').extract_first()
        title = row.css('td.title a::text').get()
        source = row.css('td.info::text').get()
        date = row.css('td.date::text').get()
        
        if not content_url or not title or not source or not date:
            return None
            
        article_id, office_id = self._extract_article_and_office_ids(content_url)
        if not article_id or not office_id or f"{office_id}{article_id}" in processed_ids:
            return None

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

    def _get_relation_origin_id(self, row_class, is_related):
        if is_related:
            rel_office_id, rel_article_id = self._extract_cluster_ids(row_class)
            if rel_office_id and rel_article_id:
                self.log(f"Office ID: {rel_office_id}, News ID: {rel_article_id}")
            return f"{rel_office_id}{rel_article_id}"
        return ''

    def _create_next_page_request(self, meta, current_page):
        return scrapy.Request(
            self._get_target_url(meta['ticker'], current_page + 1),
            headers=self._get_headers(meta['ticker']),
            meta={'ticker': meta['ticker'], 'page': current_page + 1},
            callback=self.parse,
            errback=self.errback,
        )

    def _extract_cluster_ids(self, row_class: str):
        """
        Extracts the office ID and article ID from a given row class string.

        The row class string is expected to contain a pattern like 
        'relation_lst _clusterId0310000829596', where '_clusterId0310000829596' 
        is the target substring. The first three digits represent the unique 
        office ID, and the remaining digits represent the unique article ID.

        Args:
            row_class (str): The class attribute of a table row element, 
                             which includes the cluster ID information.

        Returns:
            tuple: A tuple containing the office ID (str) and article ID (str) 
                   if the pattern is found, otherwise (None, None).

        Example:
            >>> _extract_cluster_ids('relation_lst _clusterId0310000829596')
            ('031', '0000829596')

            >>> _extract_cluster_ids('some_other_class')
            (None, None)
        """
        match = re.search(r'_clusterId(\d{3})(\d+)', row_class)
        return match.groups() if match else (None, None)

    def _extract_article_and_office_ids(self, content_url: str):
        """
        Extracts the article ID and office ID from a given content URL.

        This method searches for the article ID and office ID within the 
        query parameters of a URL. The URL is expected to contain parameters 
        in the format 'article_id=<article_id>&office_id=<office_id>'.

        Args:
            content_url (str): The URL string from which to extract the 
                               article ID and office ID.

        Returns:
            tuple: A tuple containing the article ID (str) and office ID (str) 
                   if both are found in the URL, otherwise (None, None).

        Example:
            >>> _extract_article_and_office_ids("/item/news_read.naver?article_id=0000365184&office_id=374&code=060310&page=1&sm=")
            ('0000365184', '374')

            >>> _extract_article_and_office_ids("/item/news_read.naver?code=060310&page=1&sm=")
            (None, None)
        """
        match = re.search(r'article_id=(\d+)&office_id=(\d+)', content_url)
        return match.groups() if match else (None, None)
    
    async def handle_error(self, error_code: NaverArticleErrorEnum, response: Any) -> Any:
        error_handler = {
            NaverArticleErrorEnum.END_OF_PAGE: self._handle_end_of_page,
            NaverArticleErrorEnum.NO_CONTENT: self._handle_no_content,
        }[error_code]
        
        ret = await error_handler(response)
        return ret
    
    async def _handle_end_of_page(self, response: Any):
        self.log("End of page reached")
        # TODO: Handle end of page
        return None
    
    async def _handle_no_content(self, response: Any):
        self.log("No content found")
        # TODO: Handle no content
        return None 
            
    def errback(self, failure):
        self.log(f"Errback: [{type(failure)}]{failure}")