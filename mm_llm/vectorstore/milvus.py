
import os
from dataclasses import dataclass
from typing import Any, List, Optional

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
        FieldSchema(name="chunk_num", dtype=DataType.INT64),
        FieldSchema(name="ticker", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="media_id", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=20000, description="Chunked content"),
        FieldSchema(name="content_embedding", dtype=DataType.FLOAT_VECTOR, dim=DEFAULT_EMBEDDING_DIM),
        FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=10),
        FieldSchema(name="tags", dtype=DataType.ARRAY, element_type=DataType.VARCHAR, max_capacity=20, max_length=50),
        FieldSchema(name="article_published_at", dtype=DataType.VARCHAR, max_length=30),
        FieldSchema(name="latest_scraped_at", dtype=DataType.VARCHAR, max_length=30),
    ]
    schema = CollectionSchema(fields=fields, description="Collection for Naver News Articles")
    collection = Collection(
        name="naver_news_articles",
        schema=schema,
        description=(
            "This collection is dedicated to storing Naver News Articles, "
            "including essential metadata such as article ID, ticker, media ID, "
            "title, content, and language. It also captures the publication and "
            "modification timestamps, along with content embeddings for advanced "
            "search and analysis. The collection is structured to support efficient "
            "retrieval and processing of news articles, facilitating comprehensive "
            "data analysis and insights extraction."
        )
    )
    return collection
    
def get_naver_research_report_collection() -> Collection:
    fields = [
        FieldSchema(name="report_id", dtype=DataType.VARCHAR, max_length=50, is_primary=True),  # Unique ID for each report
        FieldSchema(name="chunk_num", dtype=DataType.VARCHAR, max_length=64),  
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="issuer_company_name", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="issuer_company_id", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="report_category", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="target_company", dtype=DataType.VARCHAR, max_length=200, nullable=True),
        FieldSchema(name="target_industry", dtype=DataType.VARCHAR, max_length=200, nullable=True),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=20000, description="Chunked content"),  
        FieldSchema(name="content_embedding", dtype=DataType.FLOAT_VECTOR, dim=DEFAULT_EMBEDDING_DIM),
        FieldSchema(name="tags", dtype=DataType.ARRAY, element_type=DataType.VARCHAR, max_capacity=20, max_length=50),
        FieldSchema(name="date", dtype=DataType.VARCHAR, max_length=30, description="Report publication date"),
        FieldSchema(name="updated_at", dtype=DataType.VARCHAR, max_length=30 ),
        FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=30),
    ]
    schema = CollectionSchema(fields=fields, description="Collection for Naver Research Reports")
    collection = Collection(
        name="naver_research_reports",
        schema=schema,
        description=(
            "This collection stores chunks of research reports, "
            "including metadata such as report ID, title, issuer details, "
            "category, target information, and timestamps for creation and "
            "updates. It is designed to facilitate efficient storage and "
            "retrieval of segmented report content for analysis and search operations."
        )
    )
    return collection


def create_index(collection: Collection, field_name: str = "content_embeddin", wait_for_building:bool=True) -> None:
    collection.create_index(
        field_name=field_name, 
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