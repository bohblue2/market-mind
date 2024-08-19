"""Add columns(ArticleContentOrm) _at

Revision ID: 0bd6fbec0ed9
Revises: 5941b683ecd6
Create Date: 2024-05-17 02:24:03.348723

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0bd6fbec0ed9'
down_revision: Union[str, None] = '5941b683ecd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('article_contents', sa.Column('article_published_at', sa.DateTime(timezone=True), nullable=False))
    op.add_column('article_contents', sa.Column('article_modified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('article_contents', sa.Column('created_at', sa.DateTime(timezone=True), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('article_contents', 'created_at')
    op.drop_column('article_contents', 'article_modified_at')
    op.drop_column('article_contents', 'article_published_at')
    # ### end Alembic commands ###
