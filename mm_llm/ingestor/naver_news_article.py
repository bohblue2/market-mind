from datetime import datetime
from typing import List

import pytz  # type: ignore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm.session import Session

from mm_crawler.database.models import (NaverArticleChunkOrm,
                                        NaverArticleContentOrm)
from mm_crawler.database.session import SessionLocal
from mm_llm.ingestor.commons import process_chunk

KST = pytz.timezone("Asia/Seoul")

class NaverNewsIngestor:
    def __init__(
        self, 
        chunk_size: int = 1500, 
        chunk_overlap: int = 150,
        *,
        sess = None
    ):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap
        )
        self._sess = SessionLocal() if sess is None else sess

    def _parse_datetime(self, date_str: str) -> datetime:
        return datetime.strptime(date_str, "%Y-%m-%d")

    def _create_document(self, article: NaverArticleContentOrm) -> str:
        return f"Title: {article.title}\nContent: {article.content}"

    def _process_article(self, article: NaverArticleContentOrm) -> None:
        whole_document = self._create_document(article)
        chunk_contents: List[Document] = self.text_splitter.create_documents(
            texts=[whole_document],
            metadatas=[{"article_id": article.article_id}]
        )
        
        processed_chunks = process_chunk(
            whole_document=whole_document, 
            chunk_contents=[str(chunk) for chunk in chunk_contents]
        )
        enhanced_chunks = processed_chunks.enhanced_chunks
        # process: 1. whole_document
        whole_chunks = "\n".join(enhanced_chunks)
        whole_chunk_orm = NaverArticleChunkOrm(
            article_id=article.article_id,
            chunk_num=-1,
            content=whole_chunks,
            tags=[]
        )
        article.chunks.append(whole_chunk_orm)
        # process: 2. chunks
        for idx, content in enumerate(enhanced_chunks):
            chunk_orm = NaverArticleChunkOrm(
                article_id=article.article_id,
                chunk_num=idx,
                content=content,
                tags=[]
            )
            article.chunks.append(chunk_orm)
        article.chunked_at = datetime.now(tz=KST) # type: ignore
        
    def ingest_news_articles(
        self,
        ticker: str | None, 
        from_datetime: str,
        to_datetime: str,
        yield_size: int = 1000,
        is_upsert: bool = True 
    ) -> None:
        sess: Session = self._sess
        try:
            from_dt = self._parse_datetime(from_datetime)
            to_dt = self._parse_datetime(to_datetime)
            
            print(f"Processing articles for ticker {ticker} from {from_dt} to {to_dt}")

            articles = (sess.query(NaverArticleContentOrm)
                .outerjoin(NaverArticleChunkOrm)  # left outer join으로 변경
                .filter(
                    NaverArticleContentOrm.ticker == ticker if ticker is not None \
                        else NaverArticleContentOrm.ticker == None,
                    NaverArticleContentOrm.article_published_at.between(from_dt, to_dt),
                    # chunk가 없거나 chunked_at이 조건에 맞는 경우 필터
                    (
                        ~NaverArticleContentOrm.chunks.any() |  # chunks가 비어있는 경우
                        (
                            NaverArticleContentOrm.chunked_at.is_(None) if not is_upsert 
                            else NaverArticleContentOrm.chunked_at.isnot(None)
                        )
                    )
                )
                .yield_per(yield_size)
                .all())
            
            if len(articles) == 0:
                raise ValueError("No articles found for the given ticker and date range")

            for idx, article in enumerate(articles):
                self._process_article(article)
                sess.add(article)
                if idx % 10 == 0:
                    sess.commit()
            sess.commit()
        except Exception as e:
            sess.rollback()
            raise e
        finally:
            sess.close()

