

from typing import List

from langchain_openai import OpenAIEmbeddings
from pymilvus import Hit, Hits, SearchResult

from mm_llm.constant import DEFAULT_EMBEDDING_MODEL
from mm_llm.vectorstore.milvus import (MilvusSearchParams, get_milvus_client,
                                       get_naver_news_article_collection)


class VectorService:
    def __init__(self):
        self._embeddings = OpenAIEmbeddings(model=DEFAULT_EMBEDDING_MODEL)
        self._client = get_milvus_client() 
        self._collection = get_naver_news_article_collection()
    
    def find_similar(self, content: str, limit: int) -> List[dict]:
        data = self._embeddings.embed_query(content)
        search_params = MilvusSearchParams(
            data=data,
            anns_field="content_embedding",
            metric_type="L2",
            nprobe=16,
            limit=limit,
            output_fields=["case_id", "content"]
        )
        results: SearchResult = self._collection.search(**search_params.to_dict())
        # TODO: Handle when no results are found.
        assert len(results) == 1
        hits: Hits = results[0]
        
        similar_cases = []
        for hit in hits:
            hit: Hit # type: ignore
            similar_cases.append(
                {
                    "case_id": hit.get("case_id"),
                    "content": hit.get("content"),
                    "similarity_score": hit
                }
            )
        return similar_cases
    
    def close(self): 
        self._client.close()