"""Add vehicle management tables and trip vehicle_id.

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9
Create Date: 2026-01-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType


revision = "e6f7a8b9c0d1"
down_revision = "d4e5f6a7b8c9"  # Update this to your latest migration
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.Inspector, name: str) -> bool:
    """Check if table exists in database."""
    return name in inspector.get_table_names()


def _column_exists(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    """Check if column exists in table."""
    if not _table_exists(inspector, table_name):
        return False
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Create vehicle table
    if not _table_exists(inspector, "vehicle"):
        op.create_table(
            "vehicle",
            sa.Column("id", UUIDType(binary=True), primary_key=True),
            sa.Column(
                "fleet_id",
                UUIDType(binary=True),
                sa.ForeignKey("fleet.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "vehicle_group_id",
                UUIDType(binary=True),
                sa.ForeignKey("vehicle_group.id", ondelete="SET NULL"),
                nullable=True,
                index=True,
            ),
            # Vehicle identification
            sa.Column("license_plate", sa.String(length=20), nullable=False, unique=True, index=True),
            sa.Column("vin", sa.String(length=17), nullable=True, unique=True),
            # Vehicle details
            sa.Column("make", sa.String(length=50), nullable=True),
            sa.Column("model", sa.String(length=50), nullable=True),
            sa.Column("year", sa.Integer(), nullable=True),
            sa.Column("color", sa.String(length=30), nullable=True),
            sa.Column("vehicle_type", sa.String(length=30), nullable=True),
            # Status
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            # Insurance
            sa.Column("insurance_policy_number", sa.String(length=50), nullable=True),
            sa.Column(
                "insurance_partner_id",
                UUIDType(binary=True),
                sa.ForeignKey("insurance_partner.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("insurance_expiry_date", sa.Date(), nullable=True),
            # Registration
            sa.Column("registration_expiry_date", sa.Date(), nullable=True),
            # Metadata
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        )

    # Create driver_vehicle_assignment table
    if not _table_exists(inspector, "driver_vehicle_assignment"):
        op.create_table(
            "driver_vehicle_assignment",
            sa.Column("id", UUIDType(binary=True), primary_key=True),
            sa.Column(
                "driver_profile_id",
                UUIDType(binary=True),
                sa.ForeignKey("driver_profile.driverProfileId", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "vehicle_id",
                UUIDType(binary=True),
                sa.ForeignKey("vehicle.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("assigned_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("unassigned_at", sa.DateTime(), nullable=True),
        )

    # Add vehicle_id to trip table
    if _table_exists(inspector, "trip") and not _column_exists(inspector, "trip", "vehicle_id"):
        op.add_column(
            "trip",
            sa.Column(
                "vehicle_id",
                UUIDType(binary=True),
                sa.ForeignKey("vehicle.id", ondelete="SET NULL"),
                nullable=True,
                index=True,
            )
        )

        # Create index on vehicle_id
        try:
            op.create_index("idx_trip_vehicle_id", "trip", ["vehicle_id"])
        except Exception:
            # Index might already exist
            pass


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Remove vehicle_id from trip table
    if _table_exists(inspector, "trip") and _column_exists(inspector, "trip", "vehicle_id"):
        try:
            op.drop_index("idx_trip_vehicle_id", table_name="trip")
        except Exception:
            pass
        op.drop_column("trip", "vehicle_id")

    # Drop driver_vehicle_assignment table
    if _table_exists(inspector, "driver_vehicle_assignment"):
        op.drop_table("driver_vehicle_assignment")

    # Drop vehicle table
    if _table_exists(inspector, "vehicle"):
        op.drop_table("vehicle")
