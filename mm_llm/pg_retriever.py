from typing import Any, Dict
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from pydantic import BaseModel
from mm_llm.config import settings
from langchain_community.cache import SQLiteCache
from langchain.globals import set_llm_cache

from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain_text_splitters import CharacterTextSplitter
from langchain_teddynote.document_compressors import LLMChainExtractor
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors.base import DocumentCompressorPipeline
from langchain.retrievers.document_compressors.embeddings_filter import EmbeddingsFilter

from langchain_openai import ChatOpenAI

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=0)
relevant_filter = EmbeddingsFilter(embeddings=embeddings, similarity_threshold=0.1)
redundant_filter = EmbeddingsRedundantFilter(embeddings=embeddings)
llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
pipeline_compressor = DocumentCompressorPipeline(
    transformers=[
        splitter,
        relevant_filter,
        redundant_filter,
        LLMChainExtractor.from_llm(llm),
    ]
)


def init_vector_store(
    collection_name: str,
    cache_database_path: str = ".cache/langchain.db",
    embeddings_model: str = "text-embedding-3-large",
) -> PGVector:
    set_llm_cache(SQLiteCache(database_path=cache_database_path))
    embeddings = OpenAIEmbeddings(model=embeddings_model)
    return PGVector( 
        embeddings=embeddings,
        collection_name=collection_name,
        connection=str(settings.SQLALCHEMY_DATABASE_URL),
        use_jsonb=True,
        create_extension=True,
    )


class PgvectorRetrieverSearchKwargs(BaseModel):
    search_type: str = "similarity_score_threshold"
    search_kwargs: Dict[str, Any] = {"top_k": 5, "score_threshold": 0.5}


if __name__ == "__main__":
    vector_store = init_vector_store(collection_name="naver_research_reports")
    retriever = vector_store.as_retriever(
        **PgvectorRetrieverSearchKwargs(
            search_kwargs={"score_threshold": 0.1}
        ).model_dump()
    )
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=pipeline_compressor,
        base_retriever=retriever,
    )
    ret = compression_retriever.invoke("중국 투자전략")
    print(ret)
