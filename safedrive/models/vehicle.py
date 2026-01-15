from datetime import datetime, date
from uuid import uuid4, UUID
from sqlalchemy import Column, String, Integer, Date, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
from safedrive.database.base import Base


class Vehicle(Base):
    """
    Vehicle model for tracking individual vehicles in fleets.
    """
    __tablename__ = "vehicle"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    fleet_id = Column(UUIDType(binary=True), ForeignKey("fleet.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_group_id = Column(UUIDType(binary=True), ForeignKey("vehicle_group.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Vehicle identification
    license_plate = Column(String(20), nullable=False, unique=True, index=True)
    vin = Column(String(17), nullable=True, unique=True)  # Vehicle Identification Number
    
    # Vehicle details
    make = Column(String(50), nullable=True)  # e.g., "Toyota"
    model = Column(String(50), nullable=True)  # e.g., "Hilux"
    year = Column(Integer, nullable=True)
    color = Column(String(30), nullable=True)
    vehicle_type = Column(String(30), nullable=True)  # car, motorcycle, truck, van
    
    # Status
    status = Column(String(20), default="active")  # active, maintenance, retired
    
    # Insurance (optional)
    insurance_policy_number = Column(String(50), nullable=True)
    insurance_partner_id = Column(UUIDType(binary=True), ForeignKey("insurance_partner.id", ondelete="SET NULL"), nullable=True)
    insurance_expiry_date = Column(Date, nullable=True)
    
    # Registration
    registration_expiry_date = Column(Date, nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    fleet = relationship("Fleet", back_populates="vehicles")
    vehicle_group = relationship("VehicleGroup", back_populates="vehicles")
    driver_assignments = relationship("DriverVehicleAssignment", back_populates="vehicle", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="vehicle")
    insurance_partner = relationship("InsurancePartner", back_populates="vehicles")

    def __repr__(self):
        return f"<Vehicle(id={self.id}, license_plate={self.license_plate}, status={self.status})>"

    @property
    def id_uuid(self) -> UUID:
        """Return UUID object from binary UUID."""
        return self.id


class DriverVehicleAssignment(Base):
    """
    Association table for driver-vehicle assignments with history tracking.
    Supports multiple drivers per vehicle and tracks assignment history.
    """
    __tablename__ = "driver_vehicle_assignment"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    driver_profile_id = Column(UUIDType(binary=True), ForeignKey("driver_profile.driverProfileId", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(UUIDType(binary=True), ForeignKey("vehicle.id", ondelete="CASCADE"), nullable=False, index=True)
    
    is_primary = Column(Boolean, default=False)  # Driver's default vehicle
    
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    unassigned_at = Column(DateTime, nullable=True)  # Null = still assigned
    
    # Relationships
    driver_profile = relationship("DriverProfile", back_populates="vehicle_assignments")
    vehicle = relationship("Vehicle", back_populates="driver_assignments")

    def __repr__(self):
        status = "active" if self.unassigned_at is None else "inactive"
        return f"<DriverVehicleAssignment(driver_id={self.driver_profile_id}, vehicle_id={self.vehicle_id}, status={status})>"

    @property
    def id_uuid(self) -> UUID:
        """Return UUID object from binary UUID."""
        return self.id

    @property
    def is_active(self) -> bool:
        """Check if assignment is currently active."""
        return self.unassigned_at is None
