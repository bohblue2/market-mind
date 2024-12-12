from abc import abstractmethod
import abc
import os
import re
from datetime import datetime
from typing import Dict, Iterator, Optional

import scrapy
from bs4 import BeautifulSoup

from mm_crawler.constant import KST, NaverArticleCategoryEnum
from mm_crawler.items import ArticleItem



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

class BaseNaverNewsSpider(scrapy.Spider, abc.ABC):
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
    MAX_PAGES = 10

    def __init__(self, target_date: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_date = KST.localize(datetime.strptime(target_date.strip(), "%Y-%m-%d"))
        self.is_done = False
        self._current_page = 1

    def start_requests(self):
        date = self._format_date()
        while not self.is_done:
            yield scrapy.Request(
                self._get_target_url(date, self._current_page),
                headers=self._get_headers(date),
                meta={"date": date, "page": self._current_page},
                callback=self.parse,
                errback=self.errback,
            )
            self._current_page += 1
    
    @abstractmethod
    def _get_target_url(self, date: str, page: int) -> str: ...

    def _format_date(self) -> str:
        """Override in child classes if different date format is needed"""
        return self.target_date.strftime("%Y%m%d")

    @classmethod
    def _get_headers(cls, date: str) -> Dict[str, str]:
        """Override in child classes if different headers are needed"""
        return {
            "Referer": "https://finance.naver.com/news/mainnews.naver",
            "Accept": "application/json, text/plain, */*",
        }

    def errback(self, failure):
        self.is_done = True
        self.logger.error(f"Failed to fetch data: {failure}")

    def _check_page_limit(self, current_page: int) -> bool:
        if current_page >= self.MAX_PAGES:
            self.is_done = True
            return True
        return False

class NaverMainNewsArticleList(BaseNaverNewsSpider):
    name = os.path.basename(__file__).replace('.py', '')

    def _format_date(self) -> str:
        return self.target_date.strftime("%Y-%m-%d")

    @classmethod
    def _get_target_url(cls, date: str, page: int) -> str:
        return f"https://finance.naver.com/news/mainnews.naver?date={date}&page={str(page)}"

    def parse(self, response):
        if self._check_page_limit(response.meta['page']):
            return

        try:
            html_content = response.css("#contentarea_left > div.mainNewsList._replaceNewsLink > ul").extract().pop()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for article in soup.find_all('li', class_='block1'):
                yield self._parse_article(article)
        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            self.is_done = True

    def _parse_article(self, article) -> Optional[ArticleItem]:
        try:
            press = article.find('span', class_='press').get_text(strip=True)
            title = article.find('dd', class_='articleSubject').get_text(strip=True)
            link = article.find('a')['href']
            wdate_str = article.find('span', class_='wdate').get_text(strip=True)
            wdate = datetime.strptime(wdate_str, "%Y-%m-%d %H:%M:%S")

            ids = extract_ids(link)
            if not ids:
                self.logger.warning(f"Failed to extract IDs from {link}")
                return None

            return ArticleItem(
                ticker=None,
                article_id=ids['article_id'],
                media_id=ids['office_id'],
                media_name=press,
                title=title,
                link=link,
                category=NaverArticleCategoryEnum.MAIN,
                is_origin=True,
                origin_id=None,
                article_published_at=wdate,
            )
        except Exception as e:
            self.logger.error(f"Error parsing article: {e}")
            return None


# ... previous code with BaseNaverNewsSpider and NaverMainNewsArticleList ...

class BaseNaverSectionNewsSpider(BaseNaverNewsSpider):
    """Base class for section-specific news spiders (Outlook and Analysis)"""
    section_id3: str | None = None  # Override in child classes
    category: NaverArticleCategoryEnum | None = None  # Override in child classes

    @classmethod
    def _get_target_url(cls, date: str, page: int) -> str:
        return (f"https://finance.naver.com/news/news_list.naver?"
                f"mode=LSS3D&section_id=101&section_id2=258&"
                f"section_id3={cls.section_id3}&date={date}&page={page}")
    
    @classmethod
    def _get_headers(cls, date: str) -> Dict[str, str]:
        return {
            "Referer": cls._get_target_url(date, 1),
            "Accept": "application/json, text/plain, */*",
        }

    def parse(self, response):
        if self._check_page_limit(response.meta['page']):
            return

        try:
            html_content = response.css("#contentarea_left > ul").extract().pop()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            dl_tags = self._extract_dl_tags(soup)
            if not dl_tags:
                self.is_done = True
                return

            for dl_tag in dl_tags:
                yield from self._parse_dl_tag(dl_tag)
                
        except Exception as e:
            self.logger.error(f"Error parsing response: {e}", exc_info=True)
            self.is_done = True

    def _extract_dl_tags(self, soup: BeautifulSoup) -> list:
        """Extract all dl tags from the soup object"""
        li_tags_top = soup.find_all("li", class_="newsList")
        return [dl for li in li_tags_top for dl in li.find_all("dl")]

    def _parse_dl_tag(self, dl_tag) -> Iterator[Optional[ArticleItem]]:
        """Parse a single dl tag and yield ArticleItems"""
        subjects = dl_tag.find_all("dd", class_="articleSubject")
        for subject in subjects:
            try:
                article_data = self._extract_article_data(dl_tag, subject)
                if article_data:
                    yield self._create_article_item(article_data)
            except Exception as e:
                self.logger.error(f"Error processing article: {e}", exc_info=True)

    def _extract_article_data(self, dl_tag, subject) -> Optional[Dict]:
        """Extract article data from dl and subject tags"""
        link_tag = subject.find("a")
        if not link_tag:
            return None

        title = link_tag.get_text(strip=True)
        link = link_tag["href"]

        summary_tag = dl_tag.find("dd", class_="articleSummary")
        press_tag = summary_tag.find("span", class_="press") if summary_tag else None
        date_tag = summary_tag.find("span", class_="wdate") if summary_tag else None

        press = press_tag.get_text(strip=True) if press_tag else "No Press"
        wdate_str = date_tag.get_text(strip=True) if date_tag else None
        wdate = datetime.strptime(wdate_str, "%Y-%m-%d %H:%M") if wdate_str else None

        ids = extract_ids(link)
        if not ids:
            self.logger.warning(f"Failed to extract IDs from {link}")
            return None

        return {
            "title": title,
            "link": link,
            "press": press,
            "wdate": wdate,
            "ids": ids
        }

    def _create_article_item(self, data: Dict) -> ArticleItem:
        """Create ArticleItem from extracted data"""
        return ArticleItem(
            ticker=None,
            article_id=data['ids']['article_id'],
            media_id=data['ids']['office_id'],
            media_name=data['press'],
            title=data['title'],
            link=data['link'],
            category=self.category,
            is_origin=True,
            origin_id=None,
            article_published_at=data['wdate'],
        )

class NaverOutlookNewsArticleList(BaseNaverSectionNewsSpider):
    name = "naver_outlook_news_article_list"
    section_id3 = "401"
    category = NaverArticleCategoryEnum.OUTLOOK

class NaverAnalysisNewsArticleList(BaseNaverSectionNewsSpider):
    name = "naver_analysis_news_article_list"
    section_id3 = "402"
    category = NaverArticleCategoryEnum.ANALYSIS