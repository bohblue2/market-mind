from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from mm_llm.config import settings
from mm_crawler.database.session import SessionLocal
from mm_crawler.database.models import NaverArticleChunkOrm, NaverResearchReportChunkOrm
from datetime import datetime
from mm_llm.constant import KST
from langchain_community.cache import SQLiteCache
from langchain.globals import set_llm_cache
from typing import List, Type, Any, Dict

def init_vector_store(collection_name: str) -> PGVector:
    set_llm_cache(SQLiteCache(database_path=".cache/langchain.db"))
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    return PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=str(settings.SQLALCHEMY_DATABASE_URL),
        use_jsonb=True,
        create_extension=True
    )

def process_chunks(
    chunk_orm: Type[Any],
    vector_store: PGVector,
    metadata_mapping: Dict[str, str],
    batch_size: int = 100
) -> None:
    with SessionLocal() as sess:
        # Add stream_results=True and set execution options
        chunks = sess.query(chunk_orm).filter(
            chunk_orm.embedded_at != None  # Changed from != to == to process unembedded chunks
        ).execution_options(stream_results=True).yield_per(batch_size)

        docs = []
        chunk_ids = []
        db_chunks = []

        try:
            for chunk in chunks:
                metadata = {
                    key: getattr(chunk, value)
                    for key, value in metadata_mapping.items()
                }
                
                doc = Document(
                    page_content=chunk.content,
                    metadata=metadata
                )
                
                docs.append(doc)
                chunk_ids.append(chunk.id)
                db_chunks.append(chunk)
                
                if len(docs) >= batch_size:
                    save_batch(vector_store, docs, chunk_ids, db_chunks, sess)
                    docs, chunk_ids, db_chunks = [], [], []

            if docs:
                save_batch(vector_store, docs, chunk_ids, db_chunks, sess)
                
        except Exception as e:
            sess.rollback()
            raise e
        else:
            sess.commit()

def save_batch(
    vector_store: PGVector,
    docs: List[Document],
    chunk_ids: List[int],
    db_chunks: List[Any],
    session: Any
) -> None:
    vector_store.add_documents(docs, ids=chunk_ids)
    current_time = datetime.now(tz=KST)
    for chunk in db_chunks:
        chunk.embedded_at = current_time
    session.bulk_save_objects(db_chunks)

def main():
    # Process article chunks
    article_vector_store = init_vector_store("my_docs3")
    process_chunks(
        NaverArticleChunkOrm,
        article_vector_store,
        metadata_mapping={"article_id": "article_id", "chunk_num": "chunk_num"}
    )
    retriever = article_vector_store.as_retriever()
    print(retriever.invoke("Title: 환매부조건채권"))

    # # Process report chunks
    report_vector_store = init_vector_store("my_docs4")
    process_chunks(
        NaverResearchReportChunkOrm,
        report_vector_store,
        metadata_mapping={"report_id": "report_id", "chunk_num": "chunk_num"}
    )

if __name__ == "__main__":
    main()