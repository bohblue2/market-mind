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

from language_crawler.items import ArticleItem, NaverResearchMarketInfoItem, NaverResearchReportItem

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

def extract_info_from_soup(soup):
    """
    Extracts information from a BeautifulSoup object containing market research reports.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object containing the HTML of the market research reports table.

    Returns:
        list: A list of dictionaries, each containing information about a single report.
        Example return value:
        [
            {
                'title': '[DS Daily 시황] 2024-10-16',
                'date_str': '24.10.16',
                'date_obj': datetime.datetime(2024, 10, 16, 0, 0, tzinfo=<DstTzInfo 'Asia/Seoul' KST+9:00:00 STD>),
                'file_url': 'https://stock.pstatic.net/stock-research/market/66/20241016_market_806778000.pdf',
                'securities_company_name': 'DS투자증권'
            }
        ]
    """
    rows = soup.find_all('tr')
    results = []
    kst = pytz.timezone('Asia/Seoul')
    
    for row in rows[2:]:  # Skip the header and blank rows
        cells = row.find_all('td')
        if len(cells) == 5:
            title = cells[0].find('a').text.strip()
            securities_company = cells[1].text.strip()
            file_url = cells[2].find('a')['href'] if cells[2].find('a') else None
            date_str = cells[3].text.strip()
            
            # Parse the date string and set the timezone to KST
            date_obj = datetime.strptime(date_str, '%y.%m.%d')
            date_obj = kst.localize(date_obj)
            
            results.append(NaverResearchMarketInfoItem(
                title=title,
                date_str=date_str,
                date_obj=date_obj,
                file_url=file_url,
                securities_company_name=securities_company,
                report_item=parse_report_url(file_url)
            ))
    
    return results

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
        return f"https://finance.naver.com/research/market_info_list.naver?&page={page}"


    async def parse(self, response: HtmlResponse):
        meta = response.meta
        current_page = meta['page']
    
        reports_list_xpath = response.xpath('/html/body/div[3]/div[2]/div[2]/div[1]/div[2]/table[1]').get()
        reports_list_soup = BeautifulSoup(reports_list_xpath, 'html.parser')
        reports: List[NaverResearchMarketInfoItem] = extract_info_from_soup(reports_list_soup)
        self.log(f"Extracted {len(reports)} reports from page {current_page}")

        for _reports in reports:
            file_url = _reports.get('file_url', None)
            yield _reports

        time.sleep(10)

    async def errback(self, failure):
        self.log(type(failure))
        meta = failure.request.meta