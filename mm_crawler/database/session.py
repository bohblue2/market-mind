import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mm_crawler import project_path
from mm_crawler.database.models import ArticleOrm

DATABASE_URL = f'sqlite:///datasets/naver_news.db'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from mm_crawler.database.models import Base
    Base.metadata.create_all(bind=engine)