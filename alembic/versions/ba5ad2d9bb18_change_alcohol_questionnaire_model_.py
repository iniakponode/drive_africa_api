"""Change alcohol Questionnaire Model fields to Camel Case

Revision ID: ba5ad2d9bb18
Revises: 5345e3d93918
Create Date: 2025-01-16 13:33:33.503574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba5ad2d9bb18'
down_revision: Union[str, None] = '5345e3d93918'
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
