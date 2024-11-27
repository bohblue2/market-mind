
import os
from dataclasses import dataclass
from typing import Any, List, Optional

from pydantic import AnyUrl
from pymilvus import (Collection, CollectionSchema, DataType, FieldSchema,
                      MilvusClient, connections, utility)

from mm_llm.constant import (DEFAULT_EMBEDDING_DIM, MILVUS_INDEX_TYPE,
                             MILVUS_METRIC_TYPE, MILVUS_NLIST)


def get_milvus_client(uri: str) -> MilvusClient:   
    client = MilvusClient(
        uri=uri,
        token=os.getenv("MILVUS_API_KEY", "")
    )
    connections.connect(
        uri=uri,
        token=os.getenv("MILVUS_API_KEY", "")
    )
    return client

def get_naver_news_article_collection() -> Collection:
    fields = [
        FieldSchema(name="article_id", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="ticker", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=20000),
        FieldSchema(name="content_embedding", dtype=DataType.FLOAT_VECTOR, dim=DEFAULT_EMBEDDING_DIM),
        FieldSchema(name="tags", dtype=DataType.ARRAY, element_type=DataType.VARCHAR, max_capacity=10, max_length=50),
        FieldSchema(name="article_published_at", dtype=DataType.VARCHAR, max_length=30),
        FieldSchema(name="article_modified_at", dtype=DataType.VARCHAR, max_length=30),
    ]
    schema = CollectionSchema(fields=fields, description="Collection for Naver News Articles")
    collection = Collection(
        name="naver_news_articles",
        schema=schema,
        description="Collection for Naver News Articles"
    )
    return collection
    
def get_research_report_collection() -> Collection:
    # TODO: Implement research report collection schema
    ...


def create_index(collection: Collection, wait_for_building:bool=True) -> None:
    collection.create_index(
        field_name="content_embedding", 
        index_params={
            "metric_type": MILVUS_METRIC_TYPE,
            "index_type": MILVUS_INDEX_TYPE,
            "params": { "nlist": MILVUS_NLIST }
        }
    )
    if wait_for_building:
        utility.wait_for_index_building_complete(
            collection.name, 
            index_name="content_embedding"
        )

@dataclass
class MilvusSearchParams:
    data: Any
    anns_field: str
    metric_type: str
    nprobe: int 
    limit: int
    expr: str = ""
    output_fields: Optional[List[str]] = None 
    
    def to_dict(self) -> dict:
        search_params = {
            "data": [self.data],
            "anns_field": self.anns_field,
            "param": {
                "metric_type": self.metric_type,
                "params": {"nprobe": self.nprobe}
            },
            "limit": self.limit,
            "output_fields": self.output_fields
        }
        
        if self.expr:
            search_params["expr"] = self.expr
            
        return search_params

def search(collection: Collection, search_params: MilvusSearchParams):
    return collection.search(**search_params.to_dict())