
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from mm_llm.config import settings
from langchain_community.cache import SQLiteCache
from langchain.globals import set_llm_cache

def init_vector_store(
    collection_name: str,
    cache_database_path: str =".cache/langchain.db",
    embeddings_model: str = "text-embedding-3-large"
) -> PGVector:
    set_llm_cache(SQLiteCache(database_path=cache_database_path))
    embeddings = OpenAIEmbeddings(model=embeddings_model)
    return PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=str(settings.SQLALCHEMY_DATABASE_URL),
        use_jsonb=True,
        create_extension=True
    )