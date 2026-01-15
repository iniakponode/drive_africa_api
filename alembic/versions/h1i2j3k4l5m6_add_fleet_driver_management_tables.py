"""Add fleet driver management tables.

Revision ID: h1i2j3k4l5m6
Revises: f8g9h0i1j2k3
Create Date: 2026-01-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType


revision = "h1i2j3k4l5m6"
down_revision = "f8g9h0i1j2k3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add fleet driver management tables."""
    
    # Create driver_invites table
    op.create_table(
        "driver_invites",
        sa.Column("id", UUIDType(binary=True), primary_key=True),
        sa.Column("fleet_id", UUIDType(binary=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("invite_token", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "claimed", "expired", "cancelled", name="invite_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("vehicle_group_id", UUIDType(binary=True), nullable=True),
        sa.Column("created_by", UUIDType(binary=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        sa.Column("driver_profile_id", UUIDType(binary=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleet.id"], name="fk_driver_invites_fleet_id"),
        sa.ForeignKeyConstraint(
            ["vehicle_group_id"], ["vehicle_group.id"], name="fk_driver_invites_vehicle_group_id"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["api_client.id"], name="fk_driver_invites_created_by"),
        sa.ForeignKeyConstraint(
            ["driver_profile_id"],
            ["driver_profile.driverProfileId"],
            name="fk_driver_invites_driver_profile_id",
        ),
    )
    op.create_index("ix_driver_invites_fleet_id", "driver_invites", ["fleet_id"])
    op.create_index("ix_driver_invites_email", "driver_invites", ["email"])
    op.create_index("ix_driver_invites_invite_token", "driver_invites", ["invite_token"], unique=True)
    op.create_index("ix_driver_invites_status", "driver_invites", ["status"])
    
    # Create fleet_invite_codes table
    op.create_table(
        "fleet_invite_codes",
        sa.Column("id", UUIDType(binary=True), primary_key=True),
        sa.Column("fleet_id", UUIDType(binary=True), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", UUIDType(binary=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleet.id"], name="fk_fleet_invite_codes_fleet_id"),
        sa.ForeignKeyConstraint(["created_by"], ["api_client.id"], name="fk_fleet_invite_codes_created_by"),
    )
    op.create_index("ix_fleet_invite_codes_fleet_id", "fleet_invite_codes", ["fleet_id"])
    op.create_index("ix_fleet_invite_codes_code", "fleet_invite_codes", ["code"], unique=True)
    
    # Create driver_join_requests table
    op.create_table(
        "driver_join_requests",
        sa.Column("id", UUIDType(binary=True), primary_key=True),
        sa.Column("fleet_id", UUIDType(binary=True), nullable=False),
        sa.Column("driver_profile_id", UUIDType(binary=True), nullable=False),
        sa.Column("invite_code_id", UUIDType(binary=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", name="join_request_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("requested_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", UUIDType(binary=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleet.id"], name="fk_driver_join_requests_fleet_id"),
        sa.ForeignKeyConstraint(
            ["driver_profile_id"],
            ["driver_profile.driverProfileId"],
            name="fk_driver_join_requests_driver_profile_id",
        ),
        sa.ForeignKeyConstraint(
            ["invite_code_id"], ["fleet_invite_codes.id"], name="fk_driver_join_requests_invite_code_id"
        ),
        sa.ForeignKeyConstraint(["reviewed_by"], ["api_client.id"], name="fk_driver_join_requests_reviewed_by"),
    )
    op.create_index("ix_driver_join_requests_fleet_id", "driver_join_requests", ["fleet_id"])
    op.create_index("ix_driver_join_requests_driver_profile_id", "driver_join_requests", ["driver_profile_id"])
    op.create_index("ix_driver_join_requests_status", "driver_join_requests", ["status"])
    
    # Create driver_fleet_assignments table
    op.create_table(
        "driver_fleet_assignments",
        sa.Column("id", UUIDType(binary=True), primary_key=True),
        sa.Column("fleet_id", UUIDType(binary=True), nullable=False),
        sa.Column("driver_profile_id", UUIDType(binary=True), nullable=False),
        sa.Column("vehicle_group_id", UUIDType(binary=True), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("compliance_note", sa.Text(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("assigned_by", UUIDType(binary=True), nullable=True),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleet.id"], name="fk_driver_fleet_assignments_fleet_id"),
        sa.ForeignKeyConstraint(
            ["driver_profile_id"],
            ["driver_profile.driverProfileId"],
            name="fk_driver_fleet_assignments_driver_profile_id",
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_group_id"], ["vehicle_group.id"], name="fk_driver_fleet_assignments_vehicle_group_id"
        ),
        sa.ForeignKeyConstraint(["assigned_by"], ["api_client.id"], name="fk_driver_fleet_assignments_assigned_by"),
    )
    op.create_index("ix_driver_fleet_assignments_fleet_id", "driver_fleet_assignments", ["fleet_id"])
    op.create_index(
        "ix_driver_fleet_assignments_driver_profile_id",
        "driver_fleet_assignments",
        ["driver_profile_id"],
        unique=True,
    )


def downgrade() -> None:
    """Remove fleet driver management tables."""
    op.drop_table("driver_fleet_assignments")
    op.drop_table("driver_join_requests")
    op.drop_table("fleet_invite_codes")
    op.drop_table("driver_invites")
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS invite_status")
    op.execute("DROP TYPE IF EXISTS join_request_status")
