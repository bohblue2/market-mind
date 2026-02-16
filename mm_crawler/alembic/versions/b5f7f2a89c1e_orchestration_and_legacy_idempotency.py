"""orchestration and legacy idempotency

Revision ID: b5f7f2a89c1e
Revises: 2c9c354b4c6b
Create Date: 2026-02-15 01:43:08.614905

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5f7f2a89c1e'
down_revision: Union[str, None] = '2c9c354b4c6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ingestion_sources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_code', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_code', name='uq_ingestion_sources_source_code'),
    )

    op.create_table(
        'source_cursors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_code', sa.String(), nullable=False),
        sa.Column('stream_key', sa.String(), nullable=False),
        sa.Column('cursor_type', sa.String(), nullable=False, server_default='time'),
        sa.Column('cursor_value', sa.String(), nullable=True),
        sa.Column('state_json', sa.JSON(), nullable=True),
        sa.Column('lookback_sec', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lease_owner', sa.String(), nullable=True),
        sa.Column('lease_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'source_code', 'stream_key', name='uq_source_cursor_source_stream'
        ),
    )
    op.create_index('idx_source_cursor_next_run', 'source_cursors', ['next_run_at'])
    op.create_index('idx_source_cursor_lease_until', 'source_cursors', ['lease_until'])

    op.create_table(
        'crawl_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_code', sa.String(), nullable=False),
        sa.Column('stream_key', sa.String(), nullable=False),
        sa.Column('run_type', sa.String(), nullable=False, server_default='POLL'),
        sa.Column('status', sa.String(), nullable=False, server_default='RUNNING'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('discovered_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fetched_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('inserted_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skipped_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_crawl_run_source_stream_started', 'crawl_runs', ['source_code', 'stream_key', 'started_at'])
    op.create_index('idx_crawl_run_status_started', 'crawl_runs', ['status', 'started_at'])

    op.create_table(
        'ingestion_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=True),
        sa.Column('source_code', sa.String(), nullable=False),
        sa.Column('stream_key', sa.String(), nullable=False),
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('payload_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['run_id'], ['crawl_runs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_ingestion_event_source_stream_created', 'ingestion_events', ['source_code', 'stream_key', 'created_at'])

    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_code', sa.String(), nullable=False),
        sa.Column('stream_key', sa.String(), nullable=False),
        sa.Column('external_id', sa.String(), nullable=False),
        sa.Column('canonical_url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_code', 'external_id', name='uq_documents_source_external_id'),
    )
    op.create_index('idx_documents_source_published', 'documents', ['source_code', 'published_at'])

    op.create_table(
        'document_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'content_hash', name='uq_document_versions_doc_hash'),
    )
    op.create_index('idx_document_versions_document_created', 'document_versions', ['document_id', 'created_at'])

    op.create_unique_constraint(
        'uq_naver_article_list_ticker_cat_media_article',
        'naver_article_list',
        ['ticker', 'category', 'media_id', 'article_id'],
    )
    op.create_index(
        'idx_naver_article_list_latest_scraped_at',
        'naver_article_list',
        ['latest_scraped_at'],
    )
    op.create_index(
        'idx_naver_article_list_published_at',
        'naver_article_list',
        ['article_published_at'],
    )
    op.create_index(
        'idx_naver_article_list_source_time',
        'naver_article_list',
        ['ticker', 'category', 'article_published_at'],
    )
    op.create_unique_constraint(
        'uq_naver_research_reports_category_issuer_report',
        'naver_research_reports',
        ['report_category', 'issuer_company_id', 'report_id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_naver_research_reports_category_issuer_report',
        'naver_research_reports',
        type_='unique',
    )
    op.drop_constraint(
        'uq_naver_article_list_ticker_cat_media_article',
        'naver_article_list',
        type_='unique',
    )
    op.drop_index('idx_naver_article_list_source_time', table_name='naver_article_list')
    op.drop_index('idx_naver_article_list_published_at', table_name='naver_article_list')
    op.drop_index('idx_naver_article_list_latest_scraped_at', table_name='naver_article_list')

    op.drop_index('idx_documents_source_published', table_name='documents')
    op.drop_table('document_versions')
    op.drop_table('documents')
    op.drop_index('idx_ingestion_event_source_stream_created', table_name='ingestion_events')
    op.drop_table('ingestion_events')
    op.drop_index('idx_crawl_run_status_started', table_name='crawl_runs')
    op.drop_index('idx_crawl_run_source_stream_started', table_name='crawl_runs')
    op.drop_table('crawl_runs')
    op.drop_index('idx_source_cursor_lease_until', table_name='source_cursors')
    op.drop_index('idx_source_cursor_next_run', table_name='source_cursors')
    op.drop_table('source_cursors')
    op.drop_table('ingestion_sources')

