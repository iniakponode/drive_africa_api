"""added driver_profile mapper in unsafe_behaviours

Revision ID: 360b0d5fe847
Revises: 312dc76426e0
Create Date: 2024-10-27 16:59:31.064607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '360b0d5fe847'
down_revision: Union[str, None] = '312dc76426e0'
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
