"""mad datefeild of questionnaire nullable

Revision ID: 61044d328713
Revises: da45a384a8ac
Create Date: 2025-02-07 08:10:37.473908

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61044d328713'
down_revision: Union[str, None] = 'da45a384a8ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('driving_tips', 'date',
               existing_type=sa.DATE(),
               type_=sa.DateTime(),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('driving_tips', 'date',
               existing_type=sa.DateTime(),
               type_=sa.DATE(),
               existing_nullable=False)
    # ### end Alembic commands ###
