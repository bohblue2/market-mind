import os
import re
from datetime import datetime
from typing import Dict, Optional

import scrapy
from bs4 import BeautifulSoup

from mm_crawler.constant import KST
from mm_crawler.items import ArticleItem


def _get_target_url(date: str, page: int) -> str:
    return f"https://finance.naver.com/news/mainnews.naver?date={date}&page={str(page)}"

def extract_ids(url: str) -> Optional[Dict[str, str]]:
    """
    Extracts article_id and office_id from the given URL.

    Parameters:
    url (str): The URL string to extract IDs from.

    Returns:
    Optional[Dict[str, str]]: A dictionary with 'article_id' and 'office_id' if found, otherwise None.
    """
    pattern = r"article_id=(\d+)&office_id=(\d+)"
    match = re.search(pattern, url)
    
    if match:
        return {
            "article_id": match.group(1),
            "office_id": match.group(2)
        }
    return None

class NaverMainNewsArticleList(scrapy.Spider):
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

    def __init__(self, target_date, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_date = KST.localize(datetime.strptime(target_date.strip(), "%Y-%m-%d"))
        self.is_done = False
        self._current_page = 1
    
    def start_requests(self):
        date = self.target_date.strftime("%Y-%m-%d")
        while not self.is_done:
            yield scrapy.Request(
                _get_target_url(date, self._current_page),
                headers=self._get_headers(),
                meta=dict(date=date, page=self._current_page),
                callback=self.parse,
                errback=self.errback,
            )
            self._current_page += 1
    
    @classmethod
    def _get_headers(cls) -> Dict[str, str]:
        return {
            "Referer": "https://finance.naver.com/news/mainnews.naver",
            "Accept": "application/json, text/plain, */*",
        }    
        
    def parse(self, response):
        meta = response.meta
        current_page = meta['page']
        if current_page >= 11:
            self.is_done = True
            return 

        html_content = response.css("#contentarea_left > div.mainNewsList._replaceNewsLink > ul").extract().pop()
        soup = BeautifulSoup(html_content, 'html.parser')
        articles = soup.find_all('li', class_='block1')
        
        for idx, article in enumerate(articles):                
            press = article.find('span', class_='press').get_text(strip=True)
            _ = article.find('dd', class_='articleSummary').get_text(strip=True)
            title = article.find('dd', class_='articleSubject').get_text(strip=True)
            link = article.find('a')['href']
            wdate_str = article.find('span', class_='wdate').get_text(strip=True)
            wdate = datetime.strptime(wdate_str, "%Y-%m-%d %H:%M:%S")

            ids = extract_ids(link)
            if ids is None:
                self.log(f"Failed to extract article_id and office_id from {link}")
                continue

            yield ArticleItem(
                ticker=None,
                article_id=ids['article_id'],
                media_id=ids['office_id'],
                media_name=press,
                title=title,
                link=link,
                is_main=True,
                is_origin=True,
                origin_id=None,
                article_published_at=wdate,
            )

    def errback(self, failure):
        self.is_done = True
        self.log(f"Failed to fetch data: {failure}")
