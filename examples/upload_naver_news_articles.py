from dotenv import load_dotenv
load_dotenv('./.dev.env')

import pandas as pd
from sqlalchemy import create_engine
engine = create_engine('sqlite:///./datasets/naver_news.db')
query = "SELECT * FROM article_contents"
df = pd.read_sql(query, engine)

from mm_backend.constant import NAVER_NEWS_ARTICLE_COLLECTION 

from mm_vector.vectorstore import get_client


client = get_client()
if client.has_collection(NAVER_NEWS_ARTICLE_COLLECTION):
    client.drop_collection(NAVER_NEWS_ARTICLE_COLLECTION)

from langchain_openai import OpenAIEmbeddings


embedding = OpenAIEmbeddings(model="text-embedding-3-large")

from mm_vector.vectorstore import get_naver_news_article_collection
collection = get_naver_news_article_collection()
for row in df.itertuples():
    collection.insert([
        {
            "article_id": int(row.article_id),            
            "ticker": row.ticker,
            "title": row.title,
            "content": row.content,
            "content_embedding": embedding.embed_query(row.content),
            "article_published_at": row.article_published_at,
            "article_modified_at": row.article_modified_at if row.article_modified_at else "",
        }
    ])