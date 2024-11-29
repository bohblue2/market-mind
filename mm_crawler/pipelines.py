# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import lzma
from datetime import datetime
from typing import Any, Dict, Optional

import pytz  # type: ignore
from scrapy.exceptions import DropItem

from mm_crawler.commons import async_download_pdf, async_load_to_buffer
from mm_crawler.database.models import (NaverArticleContentOrm,
                                        NaverArticleListOrm,
                                        NaverResearchReportFileOrm,
                                        NaverResearchReportOrm)
from mm_crawler.database.session import SessionLocal
from mm_crawler.items import ArticleContentItem, ArticleItem

kst = pytz.timezone('Asia/Seoul')

class MarketMindPipeline:
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

    def process_item(self, item: Optional[ArticleItem], spider):
        if item is None:
            # TODO: Handle this case 
            raise DropItem("Item is None")

        article = NaverArticleListOrm(
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
        article = self.sess.query(NaverArticleListOrm).filter_by(
            article_id=response.meta['article_id'],
            media_id=response.meta['media_id']
        ).first()

        if article is not None:
            article.latest_scraped_at = datetime.now(kst) # type: ignore
            self.sess.add(article)
            self.sess.commit()
        else:
            raise DropItem(f"Article not found: {response.meta['article_id']}")
                
        article_content = NaverArticleContentOrm(
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
    
class ResearchMarketinfoListPipeline:
    def open_spider(self, spider): 
        self.sess = SessionLocal()   
        
    def close_spider(self, spider): 
        self.sess.close()

    async def process_item(self, item: Dict[str, Any], spider):
        """
        {
            'title': '불거지는 중동 사태와 크레딧 시장 영향은?', 
            'date_str': '24.10.07', 
            'date_obj': datetime.datetime(2024, 10, 7, 0, 0, tzinfo=<DstTzInfo 'Asia/Seoul' KST+9:00:00 STD>), 
            'file_url': 'https://stock.pstatic.net/stock-research/debenture/61/20241007_debenture_545326000.pdf', 
            'securities_company_name': 'iM증권', 
            'report_item': 
                {'category': 'debenture', 
                'date': '20241007',
                'report_id': '545326000',
                'report_type': 'debenture',
                'security_company_id': '61'}
            }
        """
        research_report = NaverResearchReportOrm(
            title=item.get('title'),
            date=item.get('date_obj'),
            file_url=item.get('file_url'),
            issuer_company_name=item.get('securities_company_name'),
            issuer_company_id=item['report_item'].get('security_company_id'),
            report_category=item['report_item'].get('category'),
            report_id=item['report_item'].get('report_id'),
            target_company=item['report_item'].get('target_company', None),    # Not provided in the input data
            target_industry=item['report_item'].get('target_industry', None),  # Not provided in the input data
            updated_at=datetime.now(pytz.UTC),
        )
        self.sess.add(research_report)
        self.sess.commit()
        await fetch_and_store_report(self.sess, research_report, item)
        return item

async def fetch_and_store_report(sess, report_orm: NaverResearchReportOrm, item: Dict[str, Any]):
    report_item: Dict[str, Any] = item.get('report_item', {})
    print(
        f"Fetching and storing: "
        f"research_report/"
        f"{report_item['date']}/"
        f"{report_item['category']}/"
        f"{report_item['report_id']}.pdf"
    )
    try:
        buffer = bytearray()
        await async_load_to_buffer(url=str(report_orm.file_url), buffer=buffer)
        report_file = NaverResearchReportFileOrm(report_id=report_orm.id, file_data=buffer)
        sess.add(report_file)
        sess.commit()
    except Exception as e:
        raise DropItem(f"Failed to download and store report: {e}") 
    else:
        report_orm.downloaded = True # type: ignore
        sess.add(report_orm)
        sess.commit()
        
        