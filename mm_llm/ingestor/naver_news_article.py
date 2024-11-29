import asyncio
from typing import List

from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymilvus import MilvusClient
from sqlalchemy.orm.session import Session

from mm_crawler.database.models import (NaverArticleContentOrm)
from mm_crawler.database.session import SessionLocal
from mm_llm.config import settings
from mm_llm.vectorstore.milvus import get_milvus_client, get_naver_news_article_collection
from langchain_core.documents import Document

async def ingest_research_report_to_milvus(
    sess: Session,
    ticker: str, 
    from_datetime: str,
    to_datetime: str,
    vec_client: MilvusClient,
    yield_size: int = 1000
) -> None:
    from_datetime_obj = datetime.strptime(from_datetime, "%Y-%m-%d %H:%M:%S")
    to_datetime_obj = datetime.strptime(to_datetime, "%Y-%m-%d %H:%M:%S")

    articles: List[NaverArticleContentOrm] = sess.query(
        NaverArticleContentOrm
    ).filter(
        NaverArticleContentOrm.ticker == ticker,
        NaverArticleContentOrm.article_published_at.between(from_datetime_obj, to_datetime_obj)
    ).yield_per(yield_size).all() 

    embeddings = OpenAIEmbeddings(model=settings.DEFAULT_EMBEDDING_MODEL)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
    collection = get_naver_news_article_collection()
    for article in articles: 
        document_content = f"Title: {article.title} \nContent: {article.content}"
        documents: List[Document] = text_splitter.create_documents(
            texts=[document_content],
            metadatas=[{"doc_id": article.article_id}]
        )
        doc_embeddings = await embeddings.aembed_documents(texts=[doc.page_content for doc in documents])
        
        data = []
        for chunk_num, (doc, embedding) in enumerate(zip(documents, doc_embeddings)):
            tags: List[str] = []
            data.append(
                dict(
                    doc_id=article.article_id,
                    chunk_num=chunk_num,
                    content=doc.page_content,
                    content_embedding=embedding,
                    title=article.title,
                    article_id=article.article_id,
                    ticker=article.ticker,
                    media_id=article.media_id,
                    language=article.language,
                    tags=tags,
                    article_published_at=article.article_published_at,
                    latest_scraped_at=article.latest_scraped_at,
                )
            )
        result = vec_client.upsert(
            collection_name=collection.name, 
            data=data
        )
        print(result)
        print(f"Upserted {len(result.keys())} documents to Milvus collection {collection.name}.")

if __name__ == "__main__":
    sess = SessionLocal()
    milvus_client = get_milvus_client(uri=settings.MILVUS_URI)
    asyncio.run(ingest_research_report_to_milvus(
        sess=sess, 
        ticker="005930",
        from_datetime="2024-11-27 00:00:00",
        to_datetime="2024-11-29 23:59:59",
        vec_client=milvus_client
    ))