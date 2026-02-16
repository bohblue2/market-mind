import scrapy

from mm_crawler.items.canonical import CanonicalDocumentItem


class HankyungConsensusItem(CanonicalDocumentItem):
    skin_type = scrapy.Field()
