from typing import Any, Dict

from langchain.globals import set_llm_cache
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors.base import \
    DocumentCompressorPipeline
from langchain.retrievers.document_compressors.embeddings_filter import \
    EmbeddingsFilter
from langchain_community.cache import SQLiteCache
from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_teddynote.document_compressors import LLMChainExtractor
from langchain_text_splitters import CharacterTextSplitter
from pydantic import BaseModel

from mm_llm.config import settings

# Constants
DEFAULT_EMBEDDINGS_MODEL = "text-embedding-3-large"
DEFAULT_CACHE_DB_PATH = ".cache/langchain.db"
DEFAULT_COLLECTION_NAME = "naver_research_reports"
DEFAULT_SEARCH_TYPE = "similarity_score_threshold"
DEFAULT_SEARCH_KWARGS = {"top_k": 5, "score_threshold": 0.5}
DEFAULT_SCORE_THRESHOLD = 0.1

class PgvectorRetrieverSearchKwargs(BaseModel):
    search_type: str = DEFAULT_SEARCH_TYPE
    search_kwargs: Dict[str, Any] = DEFAULT_SEARCH_KWARGS

def create_embeddings(model: str = DEFAULT_EMBEDDINGS_MODEL) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=model)

def create_pipeline_compressor(
    embeddings: OpenAIEmbeddings, 
    llm: ChatOpenAI,
) -> DocumentCompressorPipeline:
    splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=0)
    relevant_filter = EmbeddingsFilter(embeddings=embeddings, similarity_threshold=0.1)
    redundant_filter = EmbeddingsRedundantFilter(embeddings=embeddings)
    return DocumentCompressorPipeline(
        transformers=[
            splitter,
            relevant_filter,
            redundant_filter,
            LLMChainExtractor.from_llm(llm),
        ]
    )

def init_vector_store(
    collection_name: str,
    cache_database_path: str = DEFAULT_CACHE_DB_PATH,
    embeddings_model: str = DEFAULT_EMBEDDINGS_MODEL,
) -> PGVector:
    set_llm_cache(SQLiteCache(database_path=cache_database_path))
    embeddings = create_embeddings(embeddings_model)
    return PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=str(settings.SQLALCHEMY_DATABASE_URL),
        use_jsonb=True,
        create_extension=True,
    )

def main():
    embeddings = create_embeddings()
    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
    pipeline_compressor = create_pipeline_compressor(embeddings, llm)

    vector_store = init_vector_store(collection_name=DEFAULT_COLLECTION_NAME)
    retriever = vector_store.as_retriever(
        **PgvectorRetrieverSearchKwargs(
            search_kwargs={"score_threshold": DEFAULT_SCORE_THRESHOLD}
        ).model_dump()
    )
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=pipeline_compressor,
        base_retriever=retriever,
    )
    ret = compression_retriever.invoke("중국 투자전략")
    print(ret)

if __name__ == "__main__":
    main()