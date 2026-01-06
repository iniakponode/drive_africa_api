"""Add admin settings table.

Revision ID: d4e5f6a7b8c9
Revises: c2a1b3d4e5f6
Create Date: 2026-01-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType


revision = "d4e5f6a7b8c9"
down_revision = "c2a1b3d4e5f6"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.Inspector, name: str) -> bool:
    return name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "admin_setting"):
        op.create_table(
            "admin_setting",
            sa.Column("id", UUIDType(binary=True), primary_key=True),
            sa.Column("key", sa.String(length=100), nullable=False, unique=True),
            sa.Column("value", sa.JSON(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _table_exists(inspector, "admin_setting"):
        op.drop_table("admin_setting")
