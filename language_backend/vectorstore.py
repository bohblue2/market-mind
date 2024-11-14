from pymilvus import Collection, CollectionSchema, DataType, FieldSchema

from dataclasses import dataclass
import os
from typing import Any, List, Optional
from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, MilvusClient, utility
from language_backend.constant import DEFAULT_EMBEDDING_DIM, MILVUS_METRIC_TYPE, MILVUS_NLIST, MILVUS_NPROBE, MILVUS_TOP_K, MILVUS_INDEX_TYPE
from pymilvus import connections

def get_client() -> MilvusClient:   
    client = MilvusClient(uri=os.getenv("MILVUS_URI"), token=os.getenv("MILVUS_API_KEY"))
    connections.connect(uri=os.getenv("MILVUS_URI"), token=os.getenv("MILVUS_API_KEY"))
    return client

def get_naver_news_article_collection() -> Collection:
    fields = [
        FieldSchema(name="article_id", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="ticker", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=20000),
        FieldSchema(name="content_embedding", dtype=DataType.FLOAT_VECTOR, dim=DEFAULT_EMBEDDING_DIM), # NOTE: This is a vector field
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
    ...