"""Add auth and insurance partner tables.

Revision ID: c2a1b3d4e5f6
Revises: f3c2a1b4d9e8
Create Date: 2026-01-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType


revision = "c2a1b3d4e5f6"
down_revision = "f3c2a1b4d9e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "insurance_partner",
        sa.Column("id", UUIDType(binary=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False, unique=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "insurance_partner_driver",
        sa.Column("id", UUIDType(binary=True), primary_key=True),
        sa.Column(
            "partner_id",
            UUIDType(binary=True),
            sa.ForeignKey("insurance_partner.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "driverProfileId",
            UUIDType(binary=True),
            sa.ForeignKey("driver_profile.driverProfileId"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "partner_id",
            "driverProfileId",
            name="uq_partner_driver",
        ),
    )

    op.create_table(
        "api_client",
        sa.Column("id", UUIDType(binary=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("api_key_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "driverProfileId",
            UUIDType(binary=True),
            sa.ForeignKey("driver_profile.driverProfileId"),
            nullable=True,
        ),
        sa.Column(
            "fleet_id",
            UUIDType(binary=True),
            sa.ForeignKey("fleet.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "insurance_partner_id",
            UUIDType(binary=True),
            sa.ForeignKey("insurance_partner.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("api_client")
    op.drop_table("insurance_partner_driver")
    op.drop_table("insurance_partner")
