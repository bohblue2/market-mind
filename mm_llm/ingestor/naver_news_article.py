import asyncio
from typing import Any, List

from datetime import datetime
from langchain_openai import OpenAIEmbeddings 
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymilvus import MilvusClient
from sqlalchemy.orm.session import Session

from mm_crawler.database.models import (NaverArticleContentOrm)
from mm_crawler.database.session import SessionLocal
from mm_llm.config import settings
from mm_llm.ingestor.commons import process_chunk
from mm_llm.vectorstore.milvus import get_milvus_client, get_naver_news_article_collection
from langchain_core.documents import Document


async def ingest_news_articles_to_milvus(
    sess: Session,
    ticker: str, 
    from_datetime: str,
    to_datetime: str,
    vec_client: MilvusClient,
    vec_collection_flush_size: int = 1000,
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

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
    collection = get_naver_news_article_collection()

    for article in articles: 
        document_content = f"Title: {article.title} \nContent: {article.content}"
        chunk_documents: List[Document] = text_splitter.create_documents(
            texts=[document_content],
            metadatas=[{"doc_id": article.article_id}]
        )
        enhanced_chunks: list[str] = []
        enhanced_embeddings: list[Any] = []
        tasks = [
            process_chunk(
                whole_document=document_content,
                chunk_content=chunk.page_content,
            )
            for chunk in chunk_documents
        ]
        results = await asyncio.gather(*tasks)
        enhanced_chunks, enhanced_embeddings = map(list, zip(*results))
        enhanced_chunks = list(enhanced_chunks)
        enhanced_embeddings = list(enhanced_embeddings)
                
        data = []
        for chunk_num, (content, content_embedding) in enumerate(zip(enhanced_chunks, enhanced_embeddings)):
            tags: List[str] = []
            data.append(
                dict(
                    article_id=int(article.article_id), # type: ignore
                    chunk_num=chunk_num,
                    ticker=article.ticker,
                    media_id=article.media_id,
                    title=article.title,
                    content=content,
                    content_embedding=content_embedding,
                    language=article.language,
                    tags=tags,
                    article_published_at=int(article.article_published_at.timestamp()),
                )
            )
            if len(data) >= vec_collection_flush_size:
                print(f"Upserting {len(data)} documents to Milvus collection {collection.name}.")
                result = vec_client.upsert(
                    collection_name=collection.name,
                    data=data,
                )
                data.clear()
        if data:
            result = vec_client.upsert(
                collection_name=collection.name, 
                data=data
            )
        print(result)
        print(f"Upserted {len(result.keys())} documents to Milvus collection {collection.name}.")

if __name__ == "__main__":
    sess = SessionLocal()
    milvus_client = get_milvus_client(uri=settings.MILVUS_URI)
    asyncio.run(ingest_news_articles_to_milvus(
        sess=sess, 
        ticker="005930",
        from_datetime="2024-12-02 00:00:00",
        to_datetime="2024-12-03 23:59:59",
        vec_client=milvus_client
    ))