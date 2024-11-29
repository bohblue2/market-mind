import json
from typing import List

import requests
from sqlalchemy import LargeBinary, Result
from sqlalchemy.orm.session import Session

from mm_crawler.database.models import (NaverArticleContentOrm,
                                        NaverResearchReportFileOrm)
from mm_crawler.database.session import SessionLocal
from mm_llm.commons import report_id_formatter
from mm_llm.config import settings
from mm_llm.spliter import split_pdf
from mm_llm.vectorstore.milvus import get_naver_news_article_collection


def ingest_research_report_to_milvus(sess: Session, yield_size: int = 1000) -> None:
    articles: List[NaverArticleContentOrm] = sess.query(
        NaverArticleContentOrm
    ).yield_per(yield_size).all() 

    collection = get_naver_news_article_collection()
    
    for article in articles: 
        ...