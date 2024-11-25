import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, LargeBinary, String

from mm_crawler.database.base import Base


class ArticleOrm(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    media_id = Column(String, nullable=False)
    media_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    is_origin = Column(Boolean, nullable=False)
    original_id = Column(String, nullable=True)
    article_published_at = Column(DateTime(timezone=True), nullable=False)
    latest_scraped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=True)

class ArticleContentOrm(Base):
    __tablename__ = 'article_contents'
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    media_id = Column(String, nullable=False)
    html = Column(LargeBinary, nullable=False)
    content = Column(String, nullable=True)
    title = Column(String, nullable=True)
    language = Column(String, nullable=False)
    article_published_at = Column(DateTime(timezone=True), nullable=False)
    article_modified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=True)

class ResearchReportOrm(Base):
    __tablename__ = 'research_reports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    file_url = Column(String, nullable=False)
    issuer_company_name = Column(String, nullable=False)
    issuer_company_id = Column(String, nullable=False)
    report_category = Column(String, nullable=False)
    target_company  = Column(String, nullable=True)
    target_industry = Column(String, nullable=True)
    downloaded = Column(Boolean, nullable=True)
    updated_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=False)

    def __repr__(self):
        return f"<ResearchReport(id={self.id}, title='{self.title}', date='{self.date}', securities_company='{self.issuer_company_name}')>"