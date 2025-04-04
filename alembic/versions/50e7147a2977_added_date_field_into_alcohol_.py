"""Added date field into alcohol_questionnaire

Revision ID: 50e7147a2977
Revises: 408ff5ca4b2b
Create Date: 2025-01-21 10:05:27.426612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50e7147a2977'
down_revision: Union[str, None] = '408ff5ca4b2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('alcohol_questionnaire', sa.Column('date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('alcohol_questionnaire', 'date')
    # ### end Alembic commands ###
