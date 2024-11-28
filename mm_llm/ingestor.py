from mm_llm.config import settings

from mm_crawler.database.session import SessionLocal
from mm_crawler.database.models import NaverArticleListOrm

sess = SessionLocal()
articles = sess.query(NaverArticleListOrm).filter(NaverArticleListOrm.latest_scraped_at == None).all()
print(articles[0])