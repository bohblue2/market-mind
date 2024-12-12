"""init

Revision ID: 2c9c354b4c6b
Revises: 
Create Date: 2024-12-13 00:57:22.881262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c9c354b4c6b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('naver_article_contents',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('article_id', sa.String(), nullable=False),
    sa.Column('ticker', sa.String(), nullable=True),
    sa.Column('media_id', sa.String(), nullable=False),
    sa.Column('html', sa.LargeBinary(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('content', sa.String(), nullable=True),
    sa.Column('language', sa.String(), nullable=False),
    sa.Column('chunked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('article_published_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('article_modified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('article_id')
    )
    op.create_table('naver_article_failures',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('error_code', sa.String(), nullable=False),
    sa.Column('ticker', sa.String(), nullable=False),
    sa.Column('article_id', sa.String(), nullable=True),
    sa.Column('media_id', sa.String(), nullable=True),
    sa.Column('link', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('naver_article_list',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('article_id', sa.String(), nullable=False),
    sa.Column('ticker', sa.String(), nullable=True),
    sa.Column('media_id', sa.String(), nullable=False),
    sa.Column('media_name', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('link', sa.String(), nullable=False),
    sa.Column('category', sa.Enum('MAIN', 'OUTLOOK', 'ANALYSIS', 'GLOBAL', 'DERIVATIVES', 'DISCLOSURES', 'FOREX', 'CODE', name='naverarticlecategoryenum'), nullable=False),
    sa.Column('is_origin', sa.Boolean(), nullable=False),
    sa.Column('original_id', sa.String(), nullable=True),
    sa.Column('article_published_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('latest_scraped_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('naver_research_reports',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('report_id', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('file_url', sa.String(), nullable=False),
    sa.Column('issuer_company_name', sa.String(), nullable=False),
    sa.Column('issuer_company_id', sa.String(), nullable=False),
    sa.Column('report_category', sa.String(), nullable=False),
    sa.Column('target_company', sa.String(), nullable=True),
    sa.Column('target_industry', sa.String(), nullable=True),
    sa.Column('downloaded', sa.Boolean(), nullable=True),
    sa.Column('chunked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('naver_article_chunks',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('article_id', sa.String(), nullable=False),
    sa.Column('chunk_num', sa.Integer(), nullable=False),
    sa.Column('content', sa.String(), nullable=False),
    sa.Column('embedded_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tags', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['article_id'], ['naver_article_contents.article_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('naver_research_report_chunks',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('report_id', sa.Integer(), nullable=False),
    sa.Column('chunk_num', sa.Integer(), nullable=False),
    sa.Column('content', sa.String(), nullable=False),
    sa.Column('embedded_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tags', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['report_id'], ['naver_research_reports.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('naver_research_report_files',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('report_id', sa.Integer(), nullable=False),
    sa.Column('file_data', sa.LargeBinary(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['report_id'], ['naver_research_reports.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('naver_research_report_files')
    op.drop_table('naver_research_report_chunks')
    op.drop_table('naver_article_chunks')
    op.drop_table('naver_research_reports')
    op.drop_table('naver_article_list')
    op.drop_table('naver_article_failures')
    op.drop_table('naver_article_contents')
    # ### end Alembic commands ###