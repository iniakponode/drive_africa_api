"""Change alcohol Questionnaire Model userId to driverProfileId

Revision ID: 54ff87bff66e
Revises: ba5ad2d9bb18
Create Date: 2025-01-16 15:07:02.622884

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54ff87bff66e'
down_revision: Union[str, None] = 'ba5ad2d9bb18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###