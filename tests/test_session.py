import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from mm_crawler.database.models import ArticleOrm

@pytest.fixture(scope='module')
def session():
    DATABASE_URL = 'sqlite:///examples/datasets/test.db'
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_query_all_articles(session):
    articles = session.query(ArticleOrm).all()
    assert len(articles) == 0  # Assuming there are no articles in the test database

def test_insert_article(session):
    article = ArticleOrm(title='Test Article', content='This is a test article')
    session.add(article)
    session.commit()

    articles = session.query(ArticleOrm).all()
    assert len(articles) == 1
    assert articles[0].title == 'Test Article'
    assert articles[0].content == 'This is a test article'