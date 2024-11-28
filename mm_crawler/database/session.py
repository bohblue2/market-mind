
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mm_crawler.config import settings

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from mm_crawler.database.models import Base
    Base.metadata.create_all(bind=engine)

init_db()