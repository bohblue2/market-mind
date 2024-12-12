from datetime import datetime
from typing import Any, Dict, List, Type

from langchain_core.documents import Document
from langchain_postgres import PGVector

from mm_crawler.database.session import SessionLocal
from mm_llm.constant import KST


def pg_process_chunks(
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