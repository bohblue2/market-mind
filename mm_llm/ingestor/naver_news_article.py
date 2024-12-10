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
        enhanced_embeddings = processed_chunks.enhanced_embeddings
        for idx, (content, content_embedding) in enumerate(zip(enhanced_chunks, enhanced_embeddings)):
            chunk_orm = NaverArticleChunkOrm(
                article_id=article.article_id,
                chunk_num=idx,
                content=content,
                content_embedding=content_embedding,
                tags=[]
            )
            article.embedded_at = datetime.now(tz=KST) # type: ignore
            article.chunks.append(chunk_orm)
        
    def ingest_news_articles(
        self,
        ticker: str, 
        from_datetime: str,
        to_datetime: str,
        yield_size: int = 1000
    ) -> None:
        sess: Session = self._sess
        try:
            from_dt = self._parse_datetime(from_datetime)
            to_dt = self._parse_datetime(to_datetime)

            articles = sess.query(NaverArticleContentOrm).filter(
                NaverArticleContentOrm.ticker == ticker,
                NaverArticleContentOrm.article_published_at.between(from_dt, to_dt),
                NaverArticleContentOrm.embedded_at == None  # noqa: E711
            ).yield_per(yield_size).all()

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

if __name__ == "__main__":
    # 인스턴스 생성
    ingestor = NaverNewsIngestor(chunk_size=1500, chunk_overlap=150)
    
    # 실행 파라미터
    ticker = "005930"  # 예: 삼성전자
    from_date = "2024-12-07"
    to_date = "2024-12-09"
    
    try:
        ingestor.ingest_news_articles(
            ticker=ticker,
            from_datetime=from_date,
            to_datetime=to_date,
            yield_size=1000
        )
        print(f"Successfully processed news articles for ticker {ticker}")
    except Exception as e:
        print(f"Error processing news articles: {str(e)}")
        raise e