import time
from typing import List
from bs4 import BeautifulSoup
import scrapy
import pandas as pd
import os
import re
from datetime import datetime
import pytz

from scrapy.http.response.html import HtmlResponse

from language_crawler.items import ArticleItem, NaverResearchCompanyItem, NaverResearchMarketInfoItem, NaverResearchReportItem

import re
from urllib.parse import urlparse

def parse_report_url(url):
    """
    Parses a report URL and extracts relevant information.

    Args:
        url (str): The URL of the report.

    Returns:
        dict: A dictionary containing extracted information from the URL.
              Returns None if the URL doesn't match the expected pattern.

    Example:
        >>> url = "http://stock.pstatic.net/stock-research/market/64/20241014_market_675091000.pdf"
        >>> parse_report_url(url)
        {
            "category": "market",
            "company_id": "64",
            "date": "20241014",
            "report_type": "market",
            "report_id": "675091000"
        }
    """
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Extract the path
    path = parsed_url.path
    
    # Use regex to extract components
    pattern = r"/stock-research/(\w+)/(\d+)/(\d{8})_(\w+)_(\d+)\.pdf"
    match = re.search(pattern, path)
    
    if match:
        category, company_id, date, report_type, report_id = match.groups()
        
        return NaverResearchReportItem(
            category=category,
            company_id=company_id,
            date=date,
            report_type=report_type,
            report_id=report_id
        )
    else:
        return None


class NaverResearchMarketInfo(scrapy.Spider):
    name = os.path.basename(__file__).replace('.py', '')
    allowed_domains = ['naver.com']
    custom_settings =dict(
        ITEM_PIPELINES = {"language_crawler.pipelines.ResearchMarketinfoListPipeline": 1}
    )
    start_page = 1
    end_page = 3

    def start_requests(self):
        for page in range(
            self.start_page,
            self.end_page,
            1
        ):
            target_url = self._get_target_url(page)

            yield scrapy.Request(
                target_url,
                meta=dict(page=page, url=target_url,),
                callback=self.parse, 
                errback=self.errback,
            )
        
    def _get_target_url(self, page:int):
        return f"https://finance.naver.com/research/company_list.naver?&page={page}"

    async def parse(self, response: HtmlResponse):
        pass
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

        # time.sleep(0.5)

        # yield scrapy.Request(
        #     self._get_target_url(meta['ticker'], current_page + 1),
        #     meta=dict(ticker=meta['ticker'], page=current_page + 1),
        #     callback=self.parse, 
        #     errback=self.errback,
        # )

    async def errback(self, failure):
        self.log(type(failure))
        meta = failure.request.meta