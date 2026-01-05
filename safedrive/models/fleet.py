from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from safedrive.database.base import Base


class Fleet(Base):
    __tablename__ = "fleet"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    region = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    vehicle_groups = relationship("VehicleGroup", back_populates="fleet", cascade="all, delete-orphan")
    assignments = relationship("DriverFleetAssignment", back_populates="fleet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Fleet(id={self.id}, name={self.name})>"


class VehicleGroup(Base):
    __tablename__ = "vehicle_group"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    fleet_id = Column(UUIDType(binary=True), ForeignKey("fleet.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    fleet = relationship("Fleet", back_populates="vehicle_groups")
    assignments = relationship("DriverFleetAssignment", back_populates="vehicle_group")

    def __repr__(self):
        return f"<VehicleGroup(id={self.id}, name={self.name}, fleet_id={self.fleet_id})>"


class DriverFleetAssignment(Base):
    __tablename__ = "driver_fleet_assignment"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    driverProfileId = Column(UUIDType(binary=True), ForeignKey("driver_profile.driverProfileId"), nullable=False)
    fleet_id = Column(UUIDType(binary=True), ForeignKey("fleet.id", ondelete="CASCADE"), nullable=False)
    vehicle_group_id = Column(UUIDType(binary=True), ForeignKey("vehicle_group.id", ondelete="SET NULL"), nullable=True)
    onboarding_completed = Column(Boolean, nullable=False, default=False)
    compliance_note = Column(Text, nullable=True)
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    driver_profile = relationship("DriverProfile", back_populates="fleet_assignments")
    fleet = relationship("Fleet", back_populates="assignments")
    vehicle_group = relationship("VehicleGroup", back_populates="assignments")

    def __repr__(self):
        return f"<DriverFleetAssignment(driver={self.driverProfileId}, fleet={self.fleet_id})>"


class DriverTripEvent(Base):
    __tablename__ = "driver_trip_event"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    driverProfileId = Column(UUIDType(binary=True), ForeignKey("driver_profile.driverProfileId"), nullable=False)
    trip_id = Column(UUIDType(binary=True), ForeignKey("trip.id"), nullable=True)
    event_type = Column(String(50), nullable=False)
    message = Column(String(255), nullable=True)
    gps_health = Column(String(100), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    driver_profile = relationship("DriverProfile", back_populates="trip_events")

    def __repr__(self):
        return f"<DriverTripEvent(driver={self.driverProfileId}, event_type={self.event_type})>"
