"""Add email and last_login_at to api_client table.

Revision ID: f8g9h0i1j2k3
Revises: e6f7a8b9c0d1
Create Date: 2026-01-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f8g9h0i1j2k3"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add email and last_login_at columns to api_client table."""
    # Add email column (nullable, unique)
    op.add_column(
        "api_client", sa.Column("email", sa.String(length=255), nullable=True)
    )
    op.create_index("ix_api_client_email", "api_client", ["email"], unique=True)

    # Add last_login_at column (nullable)
    op.add_column(
        "api_client", sa.Column("last_login_at", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Remove email and last_login_at columns from api_client table."""
    op.drop_index("ix_api_client_email", table_name="api_client")
    op.drop_column("api_client", "email")
    op.drop_column("api_client", "last_login_at")
