import logging
import os
from datetime import datetime
from typing import Any, Iterable, Union

import pytz  # type: ignore
import scrapy
from bs4 import BeautifulSoup
from scrapy.http import Request
from scrapy.http.response.html import HtmlResponse
from twisted.python.failure import Failure

from mm_crawler.constant import NaverArticleCategoryEnum
from mm_crawler.database.models import NaverArticleListOrm
from mm_crawler.database.session import SessionLocal
from mm_crawler.items import NaverArticleContentItem

ArticleId = Union[str, int, Any]
OfficeId = Union[str, int, Any]

def _get_target_url(article_id: ArticleId, office_id: OfficeId):
    article_id = int(article_id) if isinstance(article_id, str) else article_id
    office_id = int(office_id) if isinstance(office_id, str) else office_id
    return f"https://n.news.naver.com/mnews/article/{office_id:03d}/{article_id:010d}"


logging.getLogger('faker').setLevel(logging.WARNING)
kst = pytz.timezone('Asia/Seoul')

class NaverNewsArticleContents(scrapy.Spider):
    verbose = False
    name = os.path.basename(__file__).replace('.py', '')
    allowed_domains = ["naver.com"]
    custom_settings = dict( 
        ITEM_PIPELINES = {"mm_crawler.pipelines.FinanceNewsContentPipeline": 1},
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
    def __init__(self, from_date, to_date, ticker:str, category: NaverArticleCategoryEnum, *args, **kwargs):
        super(NaverNewsArticleContents, self).__init__(*args, **kwargs)
        self.from_date = kst.localize(datetime.strptime(from_date.strip(), "%Y-%m-%d"))
        self.to_date = kst.localize(datetime.strptime(to_date.strip(), "%Y-%m-%d"))
        self.ticker = ticker if ticker != "null" else None
        self.category = NaverArticleCategoryEnum(category) if category != "null" else None

    def start_requests(self) -> Iterable[Request]:
        session = SessionLocal()
        articles = session\
            .query(NaverArticleListOrm)\
            .filter(
                NaverArticleListOrm.latest_scraped_at == None,
                NaverArticleListOrm.ticker == self.ticker if self.ticker != None \
                    else NaverArticleListOrm.ticker == None,
                NaverArticleListOrm.category == self.category if self.category != None \
                    else NaverArticleListOrm.category == None, 
                NaverArticleListOrm.article_published_at.between(self.from_date, self.to_date)
            )\
            .yield_per(1000)\
            .all()
        
        for article in articles:
            yield Request(
                _get_target_url(article.article_id, article.media_id),
                meta=dict(
                    article_id=article.article_id,
                    media_id=article.media_id,
                    ticker=article.ticker,
                ),
                callback=self.parse,
                errback=self.errback,
            )
    
    async def parse(self, response: HtmlResponse):
        if self.verbose and response.request is not None:
            # Print out the user-agent of the request to check they are random
            self.log(response.request.headers.get("User-Agent"))
            self.log(response.url)

        title = response.xpath("/html/body/div[1]/div[2]/div/div[1]/div[1]/div[1]/div[2]/h2/span/text()").get()
        content_html = response.xpath("/html/body/div[1]/div[2]/div/div[1]/div[1]/div[2]/div[1]/article").get()
        if content_html is None:
            # TODO: Handle when content_html is not found.
            return 
        soup = BeautifulSoup(content_html, "html.parser")
        for tag in soup(['img', 'span', 'strong', 'em', 'div']):
            # decompose() 메소드는 해당 태그와 그 내용을 HTML 트리에서 완전히 제거합니다.
            tag.decompose()
        contnet_text = soup.get_text()
        
        media_end_head_info_datestamp = response.xpath("/html/body/div[1]/div[2]/div/div[1]/div[1]/div[1]/div[3]/div[1]")
        publish_date_html = media_end_head_info_datestamp.xpath("div[1]/span/@data-date-time").get()
        modified_date_html = media_end_head_info_datestamp.xpath("div[2]/span/@data-date-time").get()

        if self.verbose: 
            self.log(title)
            self.log(contnet_text)
            self.log(publish_date_html)
            self.log(modified_date_html)
        
        if not title or not content_html:
            # TODO: Handle when title or content_html is not found.
            self.log("Failed to extract title or content_html")
            return

        yield NaverArticleContentItem(
            ticker=response.meta['ticker'],
            article_id=response.meta['article_id'],
            media_id=response.meta['media_id'],
            html=response.text,
            content=contnet_text,
            title=title,
            language='ko',
            article_published_at=publish_date_html,
            article_modified_at=modified_date_html, 
            response=response
        )
        

    async def errback(self, failure: Failure):
        self.log(type(failure))
        self.log(failure)
