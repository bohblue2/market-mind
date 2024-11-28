import asyncio
import os
import re
import time

from bs4 import BeautifulSoup
import requests
import scrapy
from scrapy.http.response.html import HtmlResponse
from scrapy.http.request import Request
from scrapy_playwright.page import PageMethod

from mm_crawler.items import ArticleItem


class NaverFinanceNewsList(scrapy.Spider):
    name = os.path.basename(__file__).replace('.py', '')
    allowed_domains = ['naver.com']
    custom_settings =dict(
        ITEM_PIPELINES = {"mm_crawler.pipelines.FinanceNewsListPipeline": 1},
        DOWNLOADER_MIDDLEWARES={
            "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
            "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
            "scrapy_fake_useragent.middleware.RandomUserAgentMiddleware": 400,
            "scrapy_fake_useragent.middleware.RetryUserAgentMiddleware": 401,
        },
        FAKEUSERAGENT_PROVIDERS=[
            "scrapy_fake_useragent.providers.FakerProvider",
            "scrapy_fake_useragent.providers.FakeUserAgentProvider",
            "scrapy_fake_useragent.providers.FixedUserAgentProvider",
        ],
    )

    def start_requests(self):        
        resp = requests.get("http://127.0.0.1:8080/api/securities/code?tr_code=t8436")
        self.tickers = [ticker['shcode'] for ticker in resp.json()]
        self.tickers = [ticker for ticker in self.tickers if not ticker.endswith('K')] # NOTE: 우선주 제외
        self.log(f"Extracted {len(self.tickers)} tickers from API") 
        
        for ticker in self.tickers:
            target_url = self._get_target_url(ticker)

            yield scrapy.Request(
                target_url,
                meta=dict(
                    ticker=ticker, 
                    page=1, 
                    playwright=True, 
                    playwright_include_page=True,
                    playwright_page_methods=[PageMethod('wait_for_selector', '#content > div.section.inner_sub')]
                    ),
                callback=self.parse, 
                errback=self.errback,
            )
        
    def _get_target_url(self, ticker: str):
        return f"https://finance.naver.com/item/news.naver?code=005930"


    async def parse(self, response: HtmlResponse):
        meta = response.meta
        page = meta["playwright_page"]
        response_html = await page.content()

        news_frame = page.frame(name='news')
        if news_frame:
            content = await news_frame.content()
            html = BeautifulSoup(content, 'html.parser')

            page_num = 1
            for row in html.select("table.type5 tr"):
                title_tag = row.select_one("td.title a")
                title = title_tag.text if title_tag else None
                if title:
                    content_url = title_tag.get("href") if title_tag else None# type: ignore
                    
                    # Extract the source
                    source_tag = row.select_one("td.info")
                    source = source_tag.text if source_tag else "No source"

                    # Extract the date
                    date_tag = row.select_one("td.date")
                    date = date_tag.text.strip() if date_tag else "No date"

                    article_id, office_id = self._extract_article_and_office_ids(content_url) # type: ignore
                    if article_id and office_id:
                        self.log(f"Article ID: {article_id}, Office ID: {office_id}")

                    row_class = row.get('class', '')
                    is_relation_origin = False
                    is_related = False

                    if row_class is not None and 'relation_tit' in row_class:
                        is_relation_origin = True
                    elif row_class is not None and 'relation_lst' in row_class:
                        is_related = True

                    relation_origin_id = ''
                    self.log(f"Content URL: {content_url}")
                    if is_related:
                        self.log(f"Related article found: {title}")
                        rel_office_id, rel_article_id = self._extract_cluster_ids(row_class) # type: ignore 
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
                        article_published_at=date,
                        is_origin=is_relation_origin,
                        origin_id=relation_origin_id if is_related else None,
                    )
                    self.log(f'------' * 5)
                    page_num += 1
            await page.click(f"a[href*='page={page_num}']")
            # Wait for the page to load
            await page.wait_for_selector('#content > div.section.inner_sub')
    
        # meta = response.meta
        # current_page = meta['page']
        # page = meta["playwright_page"]
        # response_html = await page.content()
        # html_parser = BeautifulSoup(response_html, 'html.parser')
        
        # import pickle
        # with open(f'naver_news_list_{meta["ticker"]}_{current_page}.html', 'wb') as f:
        #     pickle.dump(html_parser, f)

        # # Check end of page
        # info_text_area = response.css('div > table > tbody > tr > td > div').get()
        # if info_text_area and '뉴스가 없습니다.' in info_text_area:
        #     self.log(f"End of page reached for {meta['ticker']}")
        #     return

        # if not info_text_area:
        #     self.log(f"Failed to find info_text_area for {meta['ticker']}. Performing full search.")
        #     if '뉴스가 없습니다.' in response.text:
        #         self.log(f"Full Searching successfully done! End of page reached for {meta['ticker']}")
        #         return
        #     else:
        #         self.log(f"Full Searching failed for {meta['ticker']}. Something went wrong.")
        
        # processed_ids = set()
        
        # for row in response.css('table.type5 tr'):
        #     content_url = row.css('td.title a::attr(href)').extract_first()
        #     title = row.css('td.title a::text').get()
        #     source = row.css('td.info::text').get()
        #     date = row.css('td.date::text').get()

        #     article_id = None
        #     office_id = None
        #     if content_url:
        #         article_id, office_id = self._extract_article_and_office_ids(content_url)
        #         if article_id and office_id:
        #             if f"{office_id}{article_id}" in processed_ids:
        #                 self.log(f"Skipping duplicate article: {title}")
        #                 self.log(f'------' * 5)
        #                 continue
        #             else:
        #                 processed_ids.add(f"{office_id}{article_id}")
        #             self.log(f"Article ID: {article_id}, Office ID: {office_id}")
        #     else:
        #         self.log(f"Failed to extract article_id and office_id from content_url: {content_url}")
            
        #     row_class = row.attrib.get('class', '')
        #     is_relation_origin = False
        #     is_related = False
        #     if 'relation_tit' in row_class:
        #         is_relation_origin = True
        #     elif 'relation_lst' in row_class:
        #         is_related = True

        #     relation_origin_id = ''
        #     self.log(f"Content URL: {content_url}")
        #     if is_related:
        #         self.log(f"Related article found: {title}")
        #         rel_office_id, rel_article_id = self._extract_cluster_ids(row_class)
        #         if rel_office_id and rel_article_id:
        #             self.log(f"Office ID: {rel_office_id}, News ID: {rel_article_id}")
        #         relation_origin_id = f"{rel_office_id}{rel_article_id}"
        #     else:
        #         self.log(f"Main article found: {title}")
            
        #     yield ArticleItem(
        #         ticker=response.meta['ticker'],
        #         article_id=article_id,
        #         media_id=office_id,
        #         media_name=source,
        #         title=title,
        #         link=content_url,
        #         article_published_at=date,
        #         is_origin=is_relation_origin,
        #         origin_id=relation_origin_id if is_related else None,
        #     )
        #     self.log(f'------' * 5)

        # await asyncio.sleep(100)

        # yield scrapy.Request(
        #     self._get_target_url(meta['ticker']),
        #     meta=dict(
        #         ticker=meta['ticker'], 
        #         page=current_page + 1, 
        #         playwright=True, 
        #         playwright_include_page=True
        #     ),
        #     callback=self.parse, 
        #     errback=self.errback,
        # )

    def _is_related_article(self, row_class: str) -> bool:
        return 'relation_tit' in row_class or 'relation_lst' in row_class

    def _extract_cluster_ids(self, row_class: str):
        # Extract clusterId
        # "<tr class="relation_lst _clusterId0310000829596">" 이런 형식인데 _clusterId0310000829596 에서 
        # 0310000829596 이부분을 추출하고 싶어, 이 부분의 앞의 3자리는 언론사 고유 id 이고 뒷자리는 모두 뉴스 기사 고유 ID야.
        match = re.search(r'_clusterId(\d{3})(\d+)', row_class)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def _extract_article_and_office_ids(self, content_url: str):
        # "/item/news_read.naver?article_id=0000365184&office_id=374&code=060310&page=1&sm=" 
        # 에서 office_id와 article_id를 추출하고 싶어.
        match = re.search(r'article_id=(\d+)&office_id=(\d+)', content_url)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    async def errback(self, failure):
        self.log(type(failure))
        _ = failure.request.meta