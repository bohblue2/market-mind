# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pytz
import lzma
from datetime import datetime

from sqlalchemy import inspect
from language_crawler.database.models import ArticleContentOrm, ArticleOrm
from language_crawler.database.session import SessionLocal
from language_crawler.database.session import engine
from language_crawler.items import ArticleContentItem, ArticleItem


kst = pytz.timezone('Asia/Seoul')

class LanguageCrawlerPipeline:
    """
    Typical uses of item pipelines are:
    - cleansing HTML data
    - validating scraped data (checking that the items contain certain fields)
    - checking for duplicates (and dropping them)
    - storing the scraped item in a database
    """
    def open_spider(self, spider): ...
    def close_spider(self, spider): ...
    def process_item(self, item, spider):
        return item

class FinanceNewsListPipeline:
    """
    Typical uses of item pipelines are:
    - cleansing HTML data
    - validating scraped data (checking that the items contain certain fields)
    - checking for duplicates (and dropping them)
    - storing the scraped item in a database
    """
    def open_spider(self, spider): 
        self.sess = SessionLocal()   
        
    def close_spider(self, spider): 
        self.sess.close()

    def process_item(self, item: ArticleItem, spider):
        if item.get('article_id') is None:
            # TODO: This should be handled by the spider
            return item

        article = ArticleOrm(
            ticker=item['ticker'],
            article_id=item['article_id'],
            media_id=item['media_id'],
            media_name=item['media_name'],
            title=item['title'],
            link=item['link'],
            is_origin=item['is_origin'],
            original_id=item.get('origin_id'),
            article_published_at=kst.localize(
                datetime.strptime(item['article_published_at'].strip(), "%Y.%m.%d %H:%M")
            )
        )
        self.sess.add(article)
        self.sess.commit()
        return item

class FinanceNewsContentPipeline:
    def open_spider(self, spider): 
        self.sess = SessionLocal()   
        
    def close_spider(self, spider): 
        self.sess.close()

    def process_item(self, item: ArticleContentItem, spider):
        response = item['response']
        article = self.sess.query(ArticleOrm).filter_by(
            article_id=response.meta['article_id'],
            media_id=response.meta['media_id']
        ).first()
        article.latest_scraped_at = datetime.now(kst)
                
        article_content = ArticleContentOrm(
            ticker=item['ticker'],
            article_id=item['article_id'],
            media_id=item['media_id'],
            html=lzma.compress(item['html'].encode('utf-8')),
            content=item['content'],
            title=item['title'],
            language='ko',
            article_published_at=kst.localize(
                datetime.strptime(item['article_published_at'].strip(), "%Y-%m-%d %H:%M:%S")
            ),
            article_modified_at=kst.localize(
                datetime.strptime(item['article_modified_at'].strip(), "%Y-%m-%d %H:%M:%S")
            ) if item.get('article_modified_at') else None
        )
        self.sess.add(article_content)
        self.sess.commit()
        self.sess.close()
        return item
    