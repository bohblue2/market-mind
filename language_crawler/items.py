# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from datetime import datetime
import scrapy

class ItemBase(scrapy.Item):
    response = scrapy.Field()

class ArticleItem(ItemBase):
    ticker = scrapy.Field()
    article_id = scrapy.Field()
    media_id = scrapy.Field()
    media_name = scrapy.Field()
    title = scrapy.Field()
    link = scrapy.Field()
    is_origin = scrapy.Field()
    origin_id = scrapy.Field()
    article_published_at: str = scrapy.Field()


class ArticleContentItem(ItemBase):
    ticker = scrapy.Field()
    article_id = scrapy.Field()
    media_id = scrapy.Field()
    html = scrapy.Field()
    content = scrapy.Field()
    title = scrapy.Field()
    language = scrapy.Field()
    article_published_at: str = scrapy.Field()
    article_modified_at: str = scrapy.Field()

    def __repr__(self):
        return self.__str__()
    
    def __str__(self) -> str:
        return ""

class NaverResearchReportItem(ItemBase):
    category = scrapy.Field()
    company_id = scrapy.Field()
    date = scrapy.Field()
    report_type = scrapy.Field()
    report_id = scrapy.Field()

class NaverResearchMarketInfoItem(ItemBase):
    # category, and company
    title = scrapy.Field()
    date_str = scrapy.Field()
    date_obj: datetime = scrapy.Field()
    file_url = scrapy.Field()
    securities_company_name = scrapy.Field()
    report_item: NaverResearchReportItem = scrapy.Field()


class NaverResearchCompanyItem(ItemBase):
    company = scrapy.Field
    title = scrapy.Field()
    date_str = scrapy.Field()
    date_obj: datetime = scrapy.Field()
    file_url = scrapy.Field()
    securities_company_name = scrapy.Field()
    report_item: NaverResearchReportItem = scrapy.Field()