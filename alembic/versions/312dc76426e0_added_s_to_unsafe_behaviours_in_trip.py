"""added s to unsafe_behaviours in trip

Revision ID: 312dc76426e0
Revises: a281668694a0
Create Date: 2024-10-27 16:55:28.918556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '312dc76426e0'
down_revision: Union[str, None] = 'a281668694a0'
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
