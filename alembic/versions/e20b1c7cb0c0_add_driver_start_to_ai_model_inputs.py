"""add driver and start time to ai model inputs

Revision ID: e20b1c7cb0c0
Revises: df0f97cfaeae
Create Date: 2025-05-01 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils.types import UUIDType

revision: str = 'e20b1c7cb0c0'
down_revision: Union[str, None] = 'df0f97cfaeae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('ai_model_inputs', sa.Column('driverProfileId', UUIDType(), nullable=False))
    op.add_column('ai_model_inputs', sa.Column('start_time', sa.BigInteger(), nullable=False))
    op.create_foreign_key('fk_ai_inputs_driver', 'ai_model_inputs', 'driver_profile', ['driverProfileId'], ['driverProfileId'], ondelete='CASCADE')

def downgrade() -> None:
    op.drop_constraint('fk_ai_inputs_driver', 'ai_model_inputs', type_='foreignkey')
    op.drop_column('ai_model_inputs', 'start_time')
    op.drop_column('ai_model_inputs', 'driverProfileId')
