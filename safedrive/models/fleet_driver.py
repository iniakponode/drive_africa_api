"""Fleet driver management models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from safedrive.database.base import Base


class DriverInvite(Base):
    """Email-based driver invitation model."""

    __tablename__ = "driver_invites"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    fleet_id = Column(
        UUIDType(binary=True), ForeignKey("fleet.id"), nullable=False, index=True
    )
    email = Column(String(255), nullable=False, index=True)
    invite_token = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(
        Enum("pending", "claimed", "expired", "cancelled", name="invite_status"),
        nullable=False,
        default="pending",
        index=True,
    )
    vehicle_group_id = Column(
        UUIDType(binary=True), ForeignKey("vehicle_group.id"), nullable=True
    )
    created_by = Column(
        UUIDType(binary=True), ForeignKey("api_client.id"), nullable=False
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    claimed_at = Column(DateTime, nullable=True)
    driver_profile_id = Column(
        UUIDType(binary=True),
        ForeignKey("driver_profile.driverProfileId"),
        nullable=True,
    )
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    fleet = relationship("Fleet", backref="driver_invites")
    vehicle_group = relationship("VehicleGroup", backref="driver_invites")
    created_by_user = relationship(
        "ApiClient", foreign_keys=[created_by], backref="created_invites"
    )
    driver_profile = relationship("DriverProfile", backref="driver_invites")

    # Indexes for efficient querying (MySQL compatible)
    __table_args__ = (
        Index("ix_driver_invites_fleet_id", "fleet_id"),
        Index("ix_driver_invites_email", "email"),
        Index("ix_driver_invites_status", "status"),
        Index("ix_driver_invites_fleet_email_status", "fleet_id", "email", "status"),
    )

    def __repr__(self) -> str:
        return f"<DriverInvite(id={self.id}, email={self.email}, status={self.status})>"


class FleetInviteCode(Base):
    """Generic invite code model for fleet joining."""

    __tablename__ = "fleet_invite_codes"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    fleet_id = Column(
        UUIDType(binary=True), ForeignKey("fleet.id"), nullable=False, index=True
    )
    code = Column(String(32), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    max_uses = Column(Integer, nullable=True)
    use_count = Column(Integer, nullable=False, default=0)
    created_by = Column(
        UUIDType(binary=True), ForeignKey("api_client.id"), nullable=False
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    fleet = relationship("Fleet", backref="invite_codes")
    created_by_user = relationship(
        "ApiClient", foreign_keys=[created_by], backref="created_codes"
    )

    @property
    def is_active(self) -> bool:
        """Check if the invite code is still active."""
        if self.revoked_at is not None:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        if self.max_uses and self.use_count >= self.max_uses:
            return False
        return True

    def __repr__(self) -> str:
        return f"<FleetInviteCode(id={self.id}, code={self.code}, fleet_id={self.fleet_id})>"


class DriverJoinRequest(Base):
    """Driver request to join a fleet using an invite code."""

    __tablename__ = "driver_join_requests"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    fleet_id = Column(
        UUIDType(binary=True), ForeignKey("fleet.id"), nullable=False, index=True
    )
    driver_profile_id = Column(
        UUIDType(binary=True),
        ForeignKey("driver_profile.driverProfileId"),
        nullable=False,
        index=True,
    )
    invite_code_id = Column(
        UUIDType(binary=True), ForeignKey("fleet_invite_codes.id"), nullable=True
    )
    status = Column(
        Enum("pending", "approved", "rejected", name="join_request_status"),
        nullable=False,
        default="pending",
        index=True,
    )
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(
        UUIDType(binary=True), ForeignKey("api_client.id"), nullable=True
    )
    rejection_reason = Column(Text, nullable=True)

    # Relationships
    fleet = relationship("Fleet", backref="join_requests")
    driver_profile = relationship("DriverProfile", backref="join_requests")
    invite_code = relationship("FleetInviteCode", backref="join_requests")
    reviewed_by_user = relationship(
        "ApiClient", foreign_keys=[reviewed_by], backref="reviewed_requests"
    )

    def __repr__(self) -> str:
        return f"<DriverJoinRequest(id={self.id}, driver_id={self.driver_profile_id}, status={self.status})>"


class DriverFleetAssignment(Base):
    """Assignment of a driver to a fleet."""

    __tablename__ = "driver_fleet_assignments"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    fleet_id = Column(
        UUIDType(binary=True), ForeignKey("fleet.id"), nullable=False, index=True
    )
    driver_profile_id = Column(
        UUIDType(binary=True),
        ForeignKey("driver_profile.driverProfileId"),
        nullable=False,
        unique=True,  # A driver can only be in one fleet
        index=True,
    )
    vehicle_group_id = Column(
        UUIDType(binary=True), ForeignKey("vehicle_group.id"), nullable=True
    )
    onboarding_completed = Column(Boolean, nullable=False, default=False)
    compliance_note = Column(Text, nullable=True)
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    assigned_by = Column(
        UUIDType(binary=True), ForeignKey("api_client.id"), nullable=True
    )

    # Relationships
    fleet = relationship("Fleet", backref="driver_assignments")
    driver_profile = relationship(
        "DriverProfile", backref="fleet_assignment", uselist=False
    )
    vehicle_group = relationship("VehicleGroup", backref="assigned_drivers")
    assigned_by_user = relationship(
        "ApiClient", foreign_keys=[assigned_by], backref="assigned_drivers"
    )

    def __repr__(self) -> str:
        return f"<DriverFleetAssignment(id={self.id}, driver_id={self.driver_profile_id}, fleet_id={self.fleet_id})>"
