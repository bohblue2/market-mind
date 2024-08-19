"""Move data to new table

Revision ID: d97e0641bd1e
Revises: 70d0aacbc475
Create Date: 2024-05-31 16:17:34.125099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = 'd97e0641bd1e'
down_revision: Union[str, None] = '3a152b61bffb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)

    # 테이블이 이미 존재하는지 확인
    if 'kosdaq_articles_last_year' not in inspector.get_table_names():
        # kosdaq_articles_last_year 테이블 생성
        op.create_table(
            'kosdaq_articles_last_year',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('article_id', sa.String, nullable=False),
            sa.Column('media_id', sa.String, nullable=False),
            sa.Column('media_name', sa.String, nullable=False),
            sa.Column('title', sa.String, nullable=False),
            sa.Column('link', sa.String, nullable=False),
            sa.Column('original_id', sa.String),
            sa.Column('is_origin', sa.Boolean, nullable=False),
            sa.Column('article_published_at', sa.DateTime, nullable=False),
            sa.Column('created_at', sa.DateTime),
            sa.Column('latest_scraped_at', sa.DateTime, nullable=False),
            sa.Column('ticker', sa.String, nullable=True)
        )

    # articles 테이블에서 kosdaq_articles_last_year 테이블로 데이터 복사
    op.execute("""
        INSERT INTO kosdaq_articles_last_year (
            id, article_id, media_id, media_name, title, link, original_id,
            is_origin, article_published_at, created_at, latest_scraped_at, ticker
        )
        SELECT
            id, article_id, media_id, media_name, title, link, original_id,
            is_origin, article_published_at, created_at, latest_scraped_at, ticker
        FROM articles
        WHERE DATE(created_at) = '2024-05-30'
    """)

    # articles 테이블에서 2024-05-30 데이터를 삭제
    op.execute("""
        DELETE FROM articles
        WHERE DATE(created_at) = '2024-05-30'
    """)

def downgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)

    # 테이블이 이미 존재하는지 확인
    if 'kosdaq_articles_last_year' in inspector.get_table_names():
        # kosdaq_articles_last_year 테이블에서 articles 테이블로 데이터 복원
        op.execute("""
            INSERT INTO articles (
                id, article_id, media_id, media_name, title, link, original_id,
                is_origin, article_published_at, created_at, latest_scraped_at, ticker
            )
            SELECT
                id, article_id, media_id, media_name, title, link, original_id,
                is_origin, article_published_at, created_at, latest_scraped_at, ticker
            FROM kosdaq_articles_last_year
        """)

        # kosdaq_articles_last_year 테이블 삭제
        op.drop_table('kosdaq_articles_last_year')
