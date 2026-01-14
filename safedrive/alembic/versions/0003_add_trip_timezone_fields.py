"""Add timezone metadata to trips

Revision ID: 0003_add_trip_timezone_fields
Revises: 0002_fix_trip_time_fields
Create Date: 2026-01-14 01:05:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_add_trip_timezone_fields"
down_revision = "0002_fix_trip_time_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trip", sa.Column("time_zone_id", sa.String(length=64), nullable=True))
    op.add_column("trip", sa.Column("time_zone_offset_minutes", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("trip", "time_zone_offset_minutes")
    op.drop_column("trip", "time_zone_id")
