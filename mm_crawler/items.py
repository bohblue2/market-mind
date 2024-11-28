# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html


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
    article_published_at = scrapy.Field()


class ArticleContentItem(ItemBase):
    ticker = scrapy.Field()
    article_id = scrapy.Field()
    media_id = scrapy.Field()
    html = scrapy.Field()
    content = scrapy.Field()
    title = scrapy.Field()
    language = scrapy.Field()
    article_published_at = scrapy.Field()
    article_modified_at = scrapy.Field()

class NaverReportItem(ItemBase):
    category = scrapy.Field()
    security_company_id = scrapy.Field()
    date = scrapy.Field()
    report_type = scrapy.Field()
    report_id = scrapy.Field()
    target_company = scrapy.Field()
    target_industry = scrapy.Field()

class NaverResearchItem(ItemBase):
    category = scrapy.Field()
    company = scrapy.Field()
    title = scrapy.Field()
    date_str = scrapy.Field()
    date_obj = scrapy.Field()
    file_url = scrapy.Field()
    securities_company_name = scrapy.Field()
    report_item: NaverReportItem = scrapy.Field() # type: ignore
