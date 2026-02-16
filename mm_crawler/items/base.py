import scrapy


class ItemBase(scrapy.Item):
    response = scrapy.Field()
