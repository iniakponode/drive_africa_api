"""add password_hash to driver_profile

Revision ID: a1b2c3d4e5f6
Revises: f762e9d9b0c9
Create Date: 2026-01-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f762e9d9b0c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password_hash column to driver_profile table
    op.add_column('driver_profile', sa.Column('password_hash', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove password_hash column from driver_profile table
    op.drop_column('driver_profile', 'password_hash')
