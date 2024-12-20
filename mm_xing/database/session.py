
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from mm_xing.config import settings

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from mm_xing.database.models import Base
    Base.metadata.create_all(bind=engine)

def get_db() -> Session: # type: ignore
    db = SessionLocal()
    try:
        yield db # type: ignore
    finally:
        db.close()