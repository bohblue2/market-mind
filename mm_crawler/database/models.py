
from typing import Optional
from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer,
                        LargeBinary, String)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector  
from sqlalchemy.types import TypeEngine 

from mm_crawler.database.base import Base


class NaverArticleListOrm(Base):
    __tablename__ = 'naver_article_list'
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    media_id = Column(String, nullable=False)
    media_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    is_origin = Column(Boolean, nullable=False)
    original_id = Column(String, nullable=True)
    chunks = relationship('NaverArticleChunkOrm', backref='article_content', cascade='all, delete-orphan')
    article_published_at = Column(DateTime(timezone=True), nullable=False)
    latest_scraped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=True)

    def __repr__(self):
        return (f"<NaverArticleListOrm(id={self.id}, article_id='{self.article_id}', ticker='{self.ticker}', "
                f"media_id='{self.media_id}', media_name='{self.media_name}', title='{self.title}', "
                f"link='{self.link}', is_origin={self.is_origin}, original_id='{self.original_id}', "
                f"article_published_at='{self.article_published_at}', latest_scraped_at='{self.latest_scraped_at}', "
                f"created_at='{self.created_at}')>")

class NaverArticleContentOrm(Base):
    __tablename__ = 'naver_article_contents'
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    media_id = Column(String, nullable=False)
    html = Column(LargeBinary, nullable=False)
    title = Column(String, nullable=True)
    content = Column(String, nullable=True)
    language = Column(String, nullable=False)

    article_published_at = Column(DateTime(timezone=True), nullable=False)
    article_modified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=True)

    def __repr__(self):
        return (f"<NaverArticleContentOrm(id={self.id}, article_id='{self.article_id}', ticker='{self.ticker}', "
                f"media_id='{self.media_id}', title='{self.title}', language='{self.language}', "
                f"article_published_at='{self.article_published_at}', article_modified_at='{self.article_modified_at}', "
                f"created_at='{self.created_at}')>")

class NaverArticleChunkOrm(Base):
    __tablename__ = 'naver_article_chunks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String, ForeignKey('naver_article_contents.article_id'), nullable=False)
    chunk_num = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    content_embedding: Column[TypeEngine] = Column(Vector(3072), nullable=False)
    tags = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    def __repr__(self):
        return (f"<NaverArticleChunkOrm(id={self.id}, article_id='{self.article_id}', chunk_num={self.chunk_num}, "
                f"content='{self.content}', content_embedding={self.content_embedding}, tags='{self.tags}', "
                f"created_at='{self.created_at}')>")

class NaverArticleFailureOrm(Base):
    __tablename__ = 'naver_article_failures'
    id = Column(Integer, primary_key=True, autoincrement=True)
    error_code = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    article_id = Column(String, nullable=True)
    media_id = Column(String, nullable=True)
    link = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=True)

    def __repr__(self):
        return (f"<NaverArticleFailureOrm(id={self.id}, ticker='{self.ticker}', article_id='{self.article_id}', "
                f"media_id='{self.media_id}', link='{self.link}', created_at='{self.created_at}')>")

class NaverResearchReportOrm(Base):
    __tablename__ = 'naver_research_reports'

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
    files = relationship('NaverResearchReportFileOrm', backref='naver_research_report', cascade='all, delete-orphan')
    chunks = relationship('NaverResearchReportChunkOrm', backref='naver_research_report', cascade='all, delete-orphan')
    updated_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    def __repr__(self):
        return (f"<NaverResearchReportOrm(id={self.id}, report_id='{self.report_id}', title='{self.title}', "
                f"date='{self.date}', file_url='{self.file_url}', issuer_company_name='{self.issuer_company_name}', "
                f"issuer_company_id='{self.issuer_company_id}', report_category='{self.report_category}', "
                f"target_company='{self.target_company}', target_industry='{self.target_industry}', "
                f"downloaded={self.downloaded}, updated_at='{self.updated_at}', created_at='{self.created_at}')>")

class NaverResearchReportFileOrm(Base):
    __tablename__ = 'naver_research_report_files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey('naver_research_reports.id'), nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    embedded_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<NaverResearchReportFileOrm(id={self.id}, report_id={self.report_id})>"

class NaverResearchReportChunkOrm(Base):
    __tablename__ = 'naver_research_report_chunks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey('naver_research_reports.id'), nullable=False)
    chunk_num = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    content_embedding = Column(Vector(3072), nullable=False) # type: ignore
    tags = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    def __repr__(self):
        return (f"<NaverResearchReportChunkOrm(id={self.id}, report_id={self.report_id}, chunk_num={self.chunk_num}, "
                f"content='{self.content}', content_embedding={self.content_embedding}, tags='{self.tags}', "
                f"created_at='{self.created_at}')>")