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

from language_crawler.items import ArticleItem, NaverResearchItem, NaverResearchMarketInfoItem
from language_crawler.spiders.commons import parse_report_url


class NaverResearchBase(scrapy.Spider):
    allowed_domains = ['naver.com']
    custom_settings =dict(
        ITEM_PIPELINES = {"language_crawler.pipelines.ResearchMarketinfoListPipeline": 1}
    )

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
        
    async def errback(self, failure):
        self.log(type(failure))
        meta = failure.request.meta

class NaverResearchMarketInfo(NaverResearchBase):
    name = 'naver_research_market_info'
    start_page = 1
    end_page = 3
    _get_target_url = lambda page: f"https://finance.naver.com/research/market_info_list.naver?&page={page}"

    async def parse(self, response: HtmlResponse):
        def parse_market_info(soup):
            """
            Extracts market research report information from a BeautifulSoup object.

            Args:
                soup (BeautifulSoup): BeautifulSoup object containing the HTML of the market research reports table.

            Returns:
                list: List of dictionaries, each containing information about a single report.
                Example:
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

        meta = response.meta
        current_page = meta['page']
    
        reports_list_xpath = response.xpath('/html/body/div[3]/div[2]/div[2]/div[1]/div[2]/table[1]').get()
        reports_list_soup = BeautifulSoup(reports_list_xpath, 'html.parser')
        reports: List[NaverResearchItem] = parse_market_info(reports_list_soup)
        self.log(f"Extracted {len(reports)} reports from page {current_page}")
        
        for report in reports:
            yield report

        time.sleep(10)

class NaverResearchCompanyList(NaverResearchBase):
    name = 'naver_research_company_list'
    start_page = 1
    end_page = 3
    _get_target_url = lambda page: f"https://finance.naver.com/research/company_list.naver?&page={page}"

    async def parse(self, response: HtmlResponse):
        def parse_company_list(soup):
            rows = soup.find_all('tr')
            results = []
            kst = pytz.timezone('Asia/Seoul')
            
            for row in rows[2:]:  # Skip the header and blank rows
                cells = row.find_all('td')
                if len(cells) == 6:
                    company = cells[0].find('a').text.strip()
                    title = cells[1].find('a').text.strip()
                    securities_company = cells[2].text.strip()
                    file_url = cells[3].find('a')['href'] if cells[3].find('a') else None
                    date_str = cells[4].text.strip()

                    # Parse the date string and set the timezone to KST
                    date_obj = datetime.strptime(date_str, '%y.%m.%d')
                    date_obj = kst.localize(date_obj)
                    
                    results.append(NaverResearchCompanyItem(
                        company=company, 
                        title=title,
                        date_str=date_str,
                        date_obj=date_obj,
                        file_url=file_url,
                        securities_company_name=securities_company,
                        report_item=parse_report_url(file_url)
                    ))
            
            return results
        
        meta = response.meta
        current_page = meta['page']
    
        reports_list_xpath = response.xpath('/html/body/div[3]/div[2]/div[2]/div[1]/div[2]/table[1]').get()
        reports_list_soup = BeautifulSoup(reports_list_xpath, 'html.parser')
        reports: List[NaverResearchMarketInfoItem] = parse_company_list(reports_list_soup)
        self.log(f"Extracted {len(reports)} reports from page {current_page}")

        for _reports in reports:
            yield _reports
        
        time.sleep(10)

class NaverResearchDenbentureList(NaverResearchBase):
    name = 'naver_research_debenture_list'
    start_page = 1
    end_page = 3
    _get_target_url = lambda page: f"https://finance.naver.com/research/debenture_list.naver?&page={page}"

    async def parse(self, response: HtmlResponse):
        pass

class NaverResearchEconomyList(NaverResearchBase):
    name = 'naver_research_economy_list'
    start_page = 1
    end_page = 3
    _get_target_url = lambda page: f"https://finance.naver.com/research/economy_list.naver?&page={page}"

    async def parse(self, response: HtmlResponse):
        pass

class NaverResearchIndustryList(NaverResearchBase):
    name = 'naver_research_industry_list'
    start_page = 1
    end_page = 3
    _get_target_url = lambda page: f"https://finance.naver.com/research/industry_list.naver?&page={page}"


    async def parse(self, response: HtmlResponse):
        pass

class NaverResearchInvestList(NaverResearchBase):
    name = 'naver_research_invest_list'
    start_page = 1
    end_page = 3
    _get_target_url = lambda page: f"https://finance.naver.com/research/invest_list.naver?&page={page}"

    async def parse(self, response: HtmlResponse):
        pass