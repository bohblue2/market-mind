import time
import scrapy
import pandas as pd
import os
import re
from datetime import datetime

from scrapy.http.response.html import HtmlResponse
from language_crawler.items import ArticleItem

class FinanceNewsList(scrapy.Spider):
    name = os.path.basename(__file__).replace('.py', '')
    allowed_domains = ['naver.com']
    custom_settings = dict(
        ITEM_PIPELINES={"language_crawler.pipelines.FinanceNewsListPipeline": 1}
    )

    df = pd.read_csv('datasets/kosdaq.csv')
    tickers = df['종목코드'].tolist()

    # Define the date range
    start_date = datetime.strptime('2023-01-02', '%Y-%m-%d')
    end_date = datetime.strptime('2024-01-02', '%Y-%m-%d')

    def start_requests(self):
        for ticker in self.tickers:
            target_url = self._get_target_url(ticker, page=1)
            yield scrapy.Request(
                target_url,
                meta=dict(ticker=ticker, page=1),
                callback=self.parse,
                errback=self.errback,
            )

    def _get_target_url(self, ticker: str, page: int = 1):
        return f"https://finance.naver.com/item/news_news.naver?code={ticker}&page={page}"

    def parse(self, response: HtmlResponse):
        meta = response.meta
        current_page = meta['page']

        # Check end of page
        if '뉴스가 없습니다.' in response.text:
            self.log(f"End of page reached for {meta['ticker']}")
            return

        processed_ids = set()

        for row in response.css('table.type5 tr'):
            content_url = row.css('td.title a::attr(href)').extract_first()
            title = row.css('td.title a::text').get()
            source = row.css('td.info::text').get()
            date_text = row.css('td.date::text').get()

            if date_text:
                date_text = date_text.strip()  # Remove any leading/trailing whitespace
                article_date = datetime.strptime(date_text, '%Y.%m.%d %H:%M')
                if not (self.start_date <= article_date <= self.end_date):
                    continue  # Skip articles outside the date range

            article_id = None
            office_id = None
            if content_url:
                article_id, office_id = self._extract_article_and_office_ids(content_url)
                if article_id and office_id:
                    if f"{office_id}{article_id}" in processed_ids:
                        self.log(f"Skipping duplicate article: {title}")
                        self.log(f'------' * 5)
                        continue
                    else:
                        processed_ids.add(f"{office_id}{article_id}")
                    self.log(f"Article ID: {article_id}, Office ID: {office_id}")
            else:
                self.log(f"Failed to extract article_id and office_id from content_url: {content_url}")

            row_class = row.attrib.get('class', '')
            is_relation_origin = False
            is_related = False
            if 'relation_tit' in row_class:
                is_relation_origin = True
            elif 'relation_lst' in row_class:
                is_related = True

            relation_origin_id = ''
            self.log(f"Content URL: {content_url}")
            if is_related:
                self.log(f"Related article found: {title}")
                rel_office_id, rel_article_id = self._extract_cluster_ids(row_class)
                if rel_office_id and rel_article_id:
                    self.log(f"Office ID: {rel_office_id}, News ID: {rel_article_id}")
                relation_origin_id = f"{rel_office_id}{rel_article_id}"
            else:
                self.log(f"Main article found: {title}")

            yield ArticleItem(
                ticker=response.meta['ticker'],
                article_id=article_id,
                media_id=office_id,
                media_name=source,
                title=title,
                link=content_url,
                article_published_at=date_text,
                is_origin=is_relation_origin,
                origin_id=relation_origin_id if is_related else None,
            )
            self.log(f'------' * 5)

        time.sleep(0.5)

        yield scrapy.Request(
            self._get_target_url(meta['ticker'], current_page + 1),
            meta=dict(ticker=meta['ticker'], page=current_page + 1),
            callback=self.parse,
            errback=self.errback,
        )

    def _extract_cluster_ids(self, row_class: str):
        # Extract clusterId
        match = re.search(r'_clusterId(\d{3})(\d+)', row_class)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def _extract_article_and_office_ids(self, content_url: str):
        # Extract office_id and article_id from content_url
        match = re.search(r'article_id=(\d+)&office_id=(\d+)', content_url)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def errback(self, failure):
        self.log(type(failure))
        meta = failure.request.meta
