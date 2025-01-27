"""added radius to road model

Revision ID: 4951d9a0fb5c
Revises: 391abecaf0e0
Create Date: 2025-01-22 13:49:39.827372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4951d9a0fb5c'
down_revision: Union[str, None] = '391abecaf0e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('roads', sa.Column('radius', sa.Float(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('roads', 'radius')
    # ### end Alembic commands ###
