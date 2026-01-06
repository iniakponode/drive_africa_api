"""Add trip notes and NLG report date range columns.

Revision ID: f3c2a1b4d9e8
Revises: e20b1c7cb0c0
Create Date: 2026-01-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f3c2a1b4d9e8"
down_revision = "e20b1c7cb0c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trip", sa.Column("trip_notes", sa.Text(), nullable=True))
    op.add_column("nlg_report", sa.Column("start_date", sa.DateTime(), nullable=True))
    op.add_column("nlg_report", sa.Column("end_date", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("nlg_report", "end_date")
    op.drop_column("nlg_report", "start_date")
    op.drop_column("trip", "trip_notes")
