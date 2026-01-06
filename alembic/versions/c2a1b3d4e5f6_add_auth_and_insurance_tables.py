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


def _table_exists(inspector: sa.Inspector, name: str) -> bool:
    return name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "fleet"):
        op.create_table(
            "fleet",
            sa.Column("id", UUIDType(binary=True), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("region", sa.String(length=100), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    if not _table_exists(inspector, "vehicle_group"):
        op.create_table(
            "vehicle_group",
            sa.Column("id", UUIDType(binary=True), primary_key=True),
            sa.Column(
                "fleet_id",
                UUIDType(binary=True),
                sa.ForeignKey("fleet.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    if not _table_exists(inspector, "driver_fleet_assignment"):
        op.create_table(
            "driver_fleet_assignment",
            sa.Column("id", UUIDType(binary=True), primary_key=True),
            sa.Column(
                "driverProfileId",
                UUIDType(binary=True),
                sa.ForeignKey("driver_profile.driverProfileId"),
                nullable=False,
            ),
            sa.Column(
                "fleet_id",
                UUIDType(binary=True),
                sa.ForeignKey("fleet.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "vehicle_group_id",
                UUIDType(binary=True),
                sa.ForeignKey("vehicle_group.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "onboarding_completed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
            sa.Column("compliance_note", sa.Text(), nullable=True),
            sa.Column(
                "assigned_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    if not _table_exists(inspector, "driver_trip_event"):
        op.create_table(
            "driver_trip_event",
            sa.Column("id", UUIDType(binary=True), primary_key=True),
            sa.Column(
                "driverProfileId",
                UUIDType(binary=True),
                sa.ForeignKey("driver_profile.driverProfileId"),
                nullable=False,
            ),
            sa.Column(
                "trip_id",
                UUIDType(binary=True),
                sa.ForeignKey("trip.id"),
                nullable=True,
            ),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("message", sa.String(length=255), nullable=True),
            sa.Column("gps_health", sa.String(length=100), nullable=True),
            sa.Column(
                "timestamp",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    if not _table_exists(inspector, "insurance_partner"):
        op.create_table(
            "insurance_partner",
            sa.Column("id", UUIDType(binary=True), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("label", sa.String(length=100), nullable=False, unique=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    if not _table_exists(inspector, "insurance_partner_driver"):
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
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.UniqueConstraint(
                "partner_id",
                "driverProfileId",
                name="uq_partner_driver",
            ),
        )

    if not _table_exists(inspector, "api_client"):
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
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table in (
        "api_client",
        "insurance_partner_driver",
        "insurance_partner",
        "driver_trip_event",
        "driver_fleet_assignment",
        "vehicle_group",
        "fleet",
    ):
        if _table_exists(inspector, table):
            op.drop_table(table)
