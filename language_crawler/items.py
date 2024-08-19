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

