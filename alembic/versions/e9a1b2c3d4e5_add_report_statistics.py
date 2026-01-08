"""Add report_statistics table.

Revision ID: e9a1b2c3d4e5
Revises: d4e5f6a7b8c9
Create Date: 2026-01-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType


revision = "e9a1b2c3d4e5"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.Inspector, name: str) -> bool:
    return name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "report_statistics"):
        op.create_table(
            "report_statistics",
            sa.Column("id", UUIDType(binary=True), primary_key=True),
            sa.Column("driverProfileId", UUIDType(binary=True), nullable=False),
            sa.Column("tripId", UUIDType(binary=True), nullable=True),
            sa.Column("startDate", sa.JSON(), nullable=True),
            sa.Column("endDate", sa.JSON(), nullable=True),
            sa.Column("createdDate", sa.JSON(), nullable=True),
            sa.Column("totalIncidences", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("mostFrequentUnsafeBehaviour", sa.String(length=255), nullable=True),
            sa.Column("mostFrequentBehaviourCount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("mostFrequentBehaviourOccurrences", sa.JSON(), nullable=True),
            sa.Column("tripWithMostIncidences", sa.JSON(), nullable=True),
            sa.Column("tripsPerAggregationUnit", sa.JSON(), nullable=True),
            sa.Column("aggregationUnitWithMostIncidences", sa.JSON(), nullable=True),
            sa.Column("incidencesPerAggregationUnit", sa.JSON(), nullable=True),
            sa.Column("incidencesPerTrip", sa.JSON(), nullable=True),
            sa.Column("aggregationLevel", sa.String(length=50), nullable=True),
            sa.Column("aggregationUnitsWithAlcoholInfluence", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("tripsWithAlcoholInfluencePerAggregationUnit", sa.JSON(), nullable=True),
            sa.Column("sync", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("numberOfTrips", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("numberOfTripsWithIncidences", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("numberOfTripsWithAlcoholInfluence", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("lastTripDuration", sa.JSON(), nullable=True),
            sa.Column("lastTripDistance", sa.Float(), nullable=True),
            sa.Column("lastTripAverageSpeed", sa.Float(), nullable=True),
            sa.Column("lastTripStartLocation", sa.String(length=255), nullable=True),
            sa.Column("lastTripEndLocation", sa.String(length=255), nullable=True),
            sa.Column("lastTripStartTime", sa.JSON(), nullable=True),
            sa.Column("lastTripEndTime", sa.JSON(), nullable=True),
            sa.Column("lastTripInfluence", sa.String(length=255), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("report_statistics")
