import scrapy

from mm_crawler.items.base import ItemBase


class CanonicalDocumentItem(ItemBase):
    source_code = scrapy.Field()
    stream_key = scrapy.Field()
    external_id = scrapy.Field()
    canonical_url = scrapy.Field()
    title = scrapy.Field()
    published_at = scrapy.Field()
    content_text = scrapy.Field()
    content_hash = scrapy.Field()
    metadata_json = scrapy.Field()
