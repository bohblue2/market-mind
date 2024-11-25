"""Change column names(is_related to is_origin)

Revision ID: f30e11e332a4
Revises: 7146fdf88168
Create Date: 2024-05-16 17:09:27.765403

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f30e11e332a4'
down_revision: Union[str, None] = '7146fdf88168'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('articles', sa.Column('is_origin', sa.Boolean(), nullable=False))
    op.drop_column('articles', 'is_related')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('articles', sa.Column('is_related', sa.BOOLEAN(), nullable=False))
    op.drop_column('articles', 'is_origin')
    # ### end Alembic commands ###
