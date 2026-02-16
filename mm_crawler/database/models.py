from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from mm_crawler.constant import NaverArticleCategoryEnum
from mm_crawler.database.base import Base


class NaverArticleListOrm(Base):
    __tablename__ = "naver_article_list"
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String, nullable=False)
    ticker = Column(String, nullable=True)
    media_id = Column(String, nullable=False)
    media_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    category = Column(Enum(NaverArticleCategoryEnum), nullable=False)  # type: ignore
    is_origin = Column(Boolean, nullable=False)
    original_id = Column(String, nullable=True)
    article_published_at = Column(DateTime(timezone=True), nullable=False)
    latest_scraped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=True)

    def __repr__(self):
        attributes = [
            f"id={self.id}",
            f"article_id='{self.article_id}'",
            f"ticker='{self.ticker}'",
            f"media_id='{self.media_id}'",
            f"media_name='{self.media_name}'",
            f"title='{self.title}'",
            f"link='{self.link}'",
            f"category='{self.category}'",
            f"is_origin={self.is_origin}",
            f"original_id='{self.original_id}'",
            f"article_published_at='{self.article_published_at}'",
            f"latest_scraped_at='{self.latest_scraped_at}'",
            f"created_at='{self.created_at}'",
        ]
        return f"<NaverArticleListOrm({', '.join(attributes)})>"


class NaverArticleContentOrm(Base):
    __tablename__ = "naver_article_contents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String, unique=True, nullable=False)
    ticker = Column(String, nullable=True)
    media_id = Column(String, nullable=False)
    html = Column(LargeBinary, nullable=False)
    title = Column(String, nullable=True)
    content = Column(String, nullable=True)
    language = Column(String, nullable=False)
    chunks = relationship(
        "NaverArticleChunkOrm", backref="article_content", cascade="all, delete-orphan"
    )
    chunked_at = Column(DateTime(timezone=True), nullable=True, default=None)
    article_published_at = Column(DateTime(timezone=True), nullable=False)
    article_modified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=True)

    def __repr__(self):
        attributes = {
            "id": self.id,
            "article_id": self.article_id,
            "ticker": self.ticker,
            "media_id": self.media_id,
            "title": self.title,
            "language": self.language,
            "chunked_at": self.chunked_at,
            "article_published_at": self.article_published_at,
            "article_modified_at": self.article_modified_at,
            "created_at": self.created_at,
        }
        attr_str = ", ".join(f"{key}='{value}'" for key, value in attributes.items())
        return f"<NaverArticleContentOrm({attr_str})>"


class NaverArticleChunkOrm(Base):
    __tablename__ = "naver_article_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(
        String, ForeignKey("naver_article_contents.article_id"), nullable=False
    )
    chunk_num = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    embedded_at = Column(DateTime(timezone=True), nullable=True, default=None)
    tags = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    def __repr__(self):
        attributes = {
            "id": self.id,
            "article_id": self.article_id,
            "chunk_num": self.chunk_num,
            "content": self.content,
            "embedded_at": self.embedded_at,
            "tags": self.tags,
            "created_at": self.created_at,
        }
        attr_str = ", ".join(f"{key}='{value}'" for key, value in attributes.items())
        return f"<NaverArticleChunkOrm({attr_str})>"


class NaverArticleFailureOrm(Base):
    __tablename__ = "naver_article_failures"
    id = Column(Integer, primary_key=True, autoincrement=True)
    error_code = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    article_id = Column(String, nullable=True)
    media_id = Column(String, nullable=True)
    link = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=True)

    def __repr__(self):
        return (
            f"<NaverArticleFailureOrm(id={self.id}, ticker='{self.ticker}', article_id='{self.article_id}', "
            f"media_id='{self.media_id}', link='{self.link}', created_at='{self.created_at}')>"
        )


class NaverResearchReportOrm(Base):
    __tablename__ = "naver_research_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    file_url = Column(String, nullable=False)
    issuer_company_name = Column(String, nullable=False)
    issuer_company_id = Column(String, nullable=False)
    report_category = Column(String, nullable=False)
    target_company = Column(String, nullable=True)
    target_industry = Column(String, nullable=True)
    downloaded = Column(Boolean, nullable=True)
    files = relationship(
        "NaverResearchReportFileOrm",
        backref="naver_research_report",
        cascade="all, delete-orphan",
    )
    chunks = relationship(
        "NaverResearchReportChunkOrm",
        backref="naver_research_report",
        cascade="all, delete-orphan",
    )
    chunked_at = Column(DateTime(timezone=True), nullable=True, default=None)
    updated_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    def __repr__(self):
        attributes = (
            f"id={self.id}",
            f"report_id='{self.report_id}'",
            f"title='{self.title}'",
            f"date='{self.date}'",
            f"file_url='{self.file_url}'",
            f"issuer_company_name='{self.issuer_company_name}'",
            f"issuer_company_id='{self.issuer_company_id}'",
            f"report_category='{self.report_category}'",
            f"target_company='{self.target_company}'",
            f"target_industry='{self.target_industry}'",
            f"downloaded={self.downloaded}",
            f"updated_at='{self.updated_at}'",
            f"created_at='{self.created_at}'",
        )
        return f"<NaverResearchReportOrm({', '.join(attributes)})>"


class NaverResearchReportFileOrm(Base):
    __tablename__ = "naver_research_report_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("naver_research_reports.id"), nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    def __repr__(self):
        return f"<NaverResearchReportFileOrm(id={self.id}, report_id={self.report_id}, created_at='{self.created_at}')>"


class NaverResearchReportChunkOrm(Base):
    __tablename__ = "naver_research_report_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("naver_research_reports.id"), nullable=False)
    chunk_num = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    embedded_at = Column(DateTime(timezone=True), nullable=True, default=None)
    tags = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    def __repr__(self):
        attributes = (
            f"id={self.id}",
            f"report_id={self.report_id}",
            f"chunk_num={self.chunk_num}",
            f"content='{self.content}'",
            f"embedded_at='{self.embedded_at}'",
            f"tags='{self.tags}'",
            f"created_at='{self.created_at}'",
        )
        return f"<NaverResearchReportChunkOrm({', '.join(attributes)})>"


class IngestionSourceOrm(Base):
    __tablename__ = "ingestion_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_code = Column(String, nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


class SourceCursorOrm(Base):
    __tablename__ = "source_cursors"
    __table_args__ = (
        UniqueConstraint(
            "source_code", "stream_key", name="uq_source_cursor_source_stream"
        ),
        Index("idx_source_cursor_next_run", "next_run_at"),
        Index("idx_source_cursor_lease_until", "lease_until"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_code = Column(String, nullable=False)
    stream_key = Column(String, nullable=False)
    cursor_type = Column(String, nullable=False, default="time")
    cursor_value = Column(String, nullable=True)
    state_json = Column(JSON, nullable=True)
    lookback_sec = Column(Integer, nullable=False, default=0)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    last_started_at = Column(DateTime(timezone=True), nullable=True)
    last_completed_at = Column(DateTime(timezone=True), nullable=True)
    lease_owner = Column(String, nullable=True)
    lease_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


class CrawlRunOrm(Base):
    __tablename__ = "crawl_runs"
    __table_args__ = (
        Index(
            "idx_crawl_run_source_stream_started",
            "source_code",
            "stream_key",
            "started_at",
        ),
        Index("idx_crawl_run_status_started", "status", "started_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_code = Column(String, nullable=False)
    stream_key = Column(String, nullable=False)
    run_type = Column(String, nullable=False, default="POLL")
    status = Column(String, nullable=False, default="RUNNING")
    started_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    discovered_count = Column(Integer, nullable=False, default=0)
    fetched_count = Column(Integer, nullable=False, default=0)
    inserted_count = Column(Integer, nullable=False, default=0)
    updated_count = Column(Integer, nullable=False, default=0)
    skipped_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)


class IngestionEventOrm(Base):
    __tablename__ = "ingestion_events"
    __table_args__ = (
        Index(
            "idx_ingestion_event_source_stream_created",
            "source_code",
            "stream_key",
            "created_at",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("crawl_runs.id"), nullable=True)
    source_code = Column(String, nullable=False)
    stream_key = Column(String, nullable=False)
    external_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    payload_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)


class DocumentOrm(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint(
            "source_code", "external_id", name="uq_documents_source_external_id"
        ),
        Index("idx_documents_source_published", "source_code", "published_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_code = Column(String, nullable=False)
    stream_key = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    canonical_url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    content_text = Column(Text, nullable=True)
    content_hash = Column(String, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    last_seen_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    versions = relationship(
        "DocumentVersionOrm", backref="document", cascade="all, delete-orphan"
    )


class DocumentVersionOrm(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "content_hash", name="uq_document_versions_doc_hash"
        ),
        Index("idx_document_versions_document_created", "document_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    content_hash = Column(String, nullable=False)
    content_text = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
