import asyncio
from typing import Any, List

from datetime import datetime
from langchain_openai import ChatOpenAI, OpenAI, OpenAIEmbeddings 
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymilvus import MilvusClient
from sqlalchemy.orm.session import Session

from mm_crawler.database.models import (NaverArticleContentOrm)
from mm_crawler.database.session import SessionLocal
from mm_llm.config import settings
from mm_llm.vectorstore.milvus import get_milvus_client, get_naver_news_article_collection
from langchain_core.documents import Document


async def generate_chunk_context(
    whole_document: str, 
    chunk_content: str,
    model: ChatOpenAI 
) -> str:
    prompt = f"""
    <document>
    {whole_document}
    </document>
    Here is the chunk we want to situate within the whole document
    <chunk>
    {chunk_content}
    </chunk>
    Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else.

    please answer in korean.
    """
    response = await model.ainvoke(prompt, max_tokens=5_000, temperature=0.5)

    # Assuming response.content is a list, join the strings if they are present
    if isinstance(response.content, list):
        content = ''.join(
            item if isinstance(item, str) else '' for item in response.content
        )
    else:
        content = response.content
    return content.strip()

async def process_chunk(
    chunk_text: str,
    whole_document: str,
    embeddings: OpenAIEmbeddings
) -> tuple[str, list[float]]:
    model = ChatOpenAI(model="gpt-4o")
    context = await generate_chunk_context(whole_document, chunk_text, model)
    enhanced_chunk = f"""
<context>
{context} 
</context>

<chunk>
{chunk_text}
</chunk>
"""
    enhanced_embeddings = await embeddings.aembed_query(enhanced_chunk)
    return enhanced_chunk, enhanced_embeddings 

async def ingest_research_report_to_milvus(
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

    embeddings = OpenAIEmbeddings(model=settings.DEFAULT_EMBEDDING_MODEL)
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
                chunk_text=chunk.page_content,
                whole_document=document_content,
                embeddings=embeddings
            )
            for chunk in chunk_documents
        ]
        results = await asyncio.gather(*tasks)
        enhanced_chunks, enhanced_embeddings = map(list, zip(*results))
        enhanced_chunks = list(enhanced_chunks)
        enhanced_embeddings = list(enhanced_embeddings)
                
        data = []
        for chunk_num, (content, embedding) in enumerate(zip(enhanced_chunks, enhanced_embeddings)):
            tags: List[str] = []
            data.append(
                dict(
                    article_id=int(article.article_id), # type: ignore
                    chunk_num=chunk_num,
                    ticker=article.ticker,
                    media_id=article.media_id,
                    title=article.title,
                    content=content,
                    content_embedding=embedding,
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
    asyncio.run(ingest_research_report_to_milvus(
        sess=sess, 
        ticker="005930",
        from_datetime="2024-12-02 00:00:00",
        to_datetime="2024-12-03 23:59:59",
        vec_client=milvus_client
    ))