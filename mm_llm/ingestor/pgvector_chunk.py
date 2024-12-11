from langchain_core.documents import Document
from langchain_postgres import PGVector
from mm_crawler.database.session import SessionLocal
from mm_crawler.database.models import NaverArticleChunkOrm, NaverResearchReportChunkOrm
from datetime import datetime
from mm_llm.constant import KST
from typing import List, Type, Any, Dict

from mm_llm.pgvector_retriever import init_vector_store


def process_chunks(
    chunk_orm: Type[Any],
    vector_store: PGVector,
    metadata_mapping: Dict[str, str],
    batch_size: int = 100,
    is_upsert: bool = False
) -> None:
    with SessionLocal() as sess:
        # Add stream_results=True and set execution options
        chunks = sess.query(chunk_orm).filter(
            chunk_orm.embedded_at == None if not is_upsert else chunk_orm.embedded_at != None,  # noqa: E711
            chunk_orm.chunk_num != -1
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

if __name__ == "__main__":
    # Process article chunks
    article_vector_store = init_vector_store("naver_news_articles")
    process_chunks(
        NaverArticleChunkOrm,
        article_vector_store,
        metadata_mapping={"article_id": "article_id", "chunk_num": "chunk_num"},
        is_upsert=False
    )
    # # Process report chunks
    report_vector_store = init_vector_store("naver_research_reports")
    process_chunks(
        NaverResearchReportChunkOrm,
        report_vector_store,
        metadata_mapping={"report_id": "report_id", "chunk_num": "chunk_num"},
        is_upsert=False
    )