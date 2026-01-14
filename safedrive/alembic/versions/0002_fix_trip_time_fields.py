"""Fix trip time fields and backfill bad timestamps

Revision ID: 0002_fix_trip_time_fields
Revises: 0001_add_trip_alcohol_fields
Create Date: 2026-01-14 00:55:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_fix_trip_time_fields"
down_revision = "0001_add_trip_alcohol_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "trip",
        "start_time",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        nullable=False,
    )
    op.alter_column(
        "trip",
        "end_time",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        nullable=True,
    )

    op.execute(sa.text(
        "UPDATE trip "
        "SET start_time = UNIX_TIMESTAMP(start_date) * 1000 "
        "WHERE start_time IS NOT NULL "
        "AND start_time < 10000000000 "
        "AND start_date IS NOT NULL"
    ))
    op.execute(sa.text(
        "UPDATE trip "
        "SET end_time = UNIX_TIMESTAMP(end_date) * 1000 "
        "WHERE end_time IS NOT NULL "
        "AND end_time < 10000000000 "
        "AND end_date IS NOT NULL"
    ))
    op.execute(sa.text(
        "UPDATE trip "
        "SET start_time = start_time * 1000 "
        "WHERE start_time IS NOT NULL "
        "AND start_time BETWEEN 1000000000 AND 10000000000 "
        "AND start_date IS NULL"
    ))
    op.execute(sa.text(
        "UPDATE trip "
        "SET end_time = end_time * 1000 "
        "WHERE end_time IS NOT NULL "
        "AND end_time BETWEEN 1000000000 AND 10000000000 "
        "AND end_date IS NULL"
    ))


def downgrade() -> None:
    op.alter_column(
        "trip",
        "start_time",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "trip",
        "end_time",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        nullable=True,
    )
