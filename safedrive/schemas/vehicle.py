from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


# --- Vehicle Schemas ---

class VehicleBase(BaseModel):
    """Base schema for Vehicle data."""
    license_plate: str = Field(..., max_length=20, description="Vehicle license plate number")
    vin: Optional[str] = Field(None, max_length=17, description="Vehicle Identification Number")
    make: Optional[str] = Field(None, max_length=50, description="Vehicle manufacturer (e.g., Toyota)")
    model: Optional[str] = Field(None, max_length=50, description="Vehicle model (e.g., Hilux)")
    year: Optional[int] = Field(None, ge=1900, le=2100, description="Vehicle year")
    color: Optional[str] = Field(None, max_length=30, description="Vehicle color")
    vehicle_type: Optional[str] = Field(None, max_length=30, description="Vehicle type (car, motorcycle, truck, van)")
    status: str = Field("active", max_length=20, description="Vehicle status (active, maintenance, retired)")
    insurance_policy_number: Optional[str] = Field(None, max_length=50, description="Insurance policy number")
    insurance_partner_id: Optional[UUID] = Field(None, description="Insurance partner ID")
    insurance_expiry_date: Optional[date] = Field(None, description="Insurance expiry date")
    registration_expiry_date: Optional[date] = Field(None, description="Vehicle registration expiry date")
    notes: Optional[str] = Field(None, description="Additional notes about the vehicle")


class VehicleCreate(VehicleBase):
    """Schema for creating a new vehicle."""
    fleet_id: UUID = Field(..., description="Fleet ID this vehicle belongs to")
    vehicle_group_id: Optional[UUID] = Field(None, description="Vehicle group ID")


class VehicleUpdate(BaseModel):
    """Schema for updating a vehicle (all fields optional)."""
    vehicle_group_id: Optional[UUID] = None
    license_plate: Optional[str] = Field(None, max_length=20)
    vin: Optional[str] = Field(None, max_length=17)
    make: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    color: Optional[str] = Field(None, max_length=30)
    vehicle_type: Optional[str] = Field(None, max_length=30)
    status: Optional[str] = Field(None, max_length=20)
    insurance_policy_number: Optional[str] = Field(None, max_length=50)
    insurance_partner_id: Optional[UUID] = None
    insurance_expiry_date: Optional[date] = None
    registration_expiry_date: Optional[date] = None
    notes: Optional[str] = None


class PrimaryDriverInfo(BaseModel):
    """Basic info about primary driver."""
    driver_profile_id: UUID
    email: str

    class Config:
        from_attributes = True


class FleetInfo(BaseModel):
    """Basic fleet information."""
    id: UUID
    name: str

    class Config:
        from_attributes = True


class VehicleGroupInfo(BaseModel):
    """Basic vehicle group information."""
    id: UUID
    name: str

    class Config:
        from_attributes = True


class VehicleResponse(VehicleBase):
    """Schema for vehicle response."""
    id: UUID
    fleet_id: UUID
    vehicle_group_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    fleet: Optional[FleetInfo] = None
    vehicle_group: Optional[VehicleGroupInfo] = None
    primary_driver: Optional[PrimaryDriverInfo] = None

    class Config:
        from_attributes = True


class VehicleListResponse(BaseModel):
    """Paginated list of vehicles."""
    vehicles: List[VehicleResponse]
    total: int
    page: int
    page_size: int


class VehicleBulkCreateItem(BaseModel):
    """Schema for bulk vehicle creation."""
    fleet_id: UUID
    vehicle_group_id: Optional[UUID] = None
    license_plate: str
    vin: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    vehicle_type: Optional[str] = None


class VehicleBulkCreate(BaseModel):
    """Schema for bulk creating vehicles."""
    vehicles: List[VehicleBulkCreateItem]


class VehicleBulkCreateResponse(BaseModel):
    """Response for bulk vehicle creation."""
    created: int
    updated: int
    skipped: int
    errors: List[str]


# --- Driver Vehicle Assignment Schemas ---

class DriverVehicleAssignmentBase(BaseModel):
    """Base schema for driver-vehicle assignment."""
    driver_profile_id: UUID
    vehicle_id: UUID
    is_primary: bool = False


class DriverVehicleAssignmentCreate(BaseModel):
    """Schema for creating a driver-vehicle assignment."""
    driver_profile_id: UUID
    is_primary: bool = False


class DriverVehicleAssignmentResponse(DriverVehicleAssignmentBase):
    """Schema for driver-vehicle assignment response."""
    id: UUID
    assigned_at: datetime
    unassigned_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VehicleDriverInfo(BaseModel):
    """Driver information in vehicle context."""
    assignment_id: UUID
    driver_profile_id: UUID
    email: str
    is_primary: bool
    assigned_at: datetime

    class Config:
        from_attributes = True


class VehicleDriversResponse(BaseModel):
    """List of drivers assigned to a vehicle."""
    drivers: List[VehicleDriverInfo]


class DriverVehicleInfo(BaseModel):
    """Vehicle information in driver context."""
    id: UUID
    license_plate: str
    make: Optional[str] = None
    model: Optional[str] = None
    is_primary: bool
    assigned_at: datetime

    class Config:
        from_attributes = True


class DriverVehiclesResponse(BaseModel):
    """List of vehicles assigned to a driver."""
    vehicles: List[DriverVehicleInfo]


# --- Vehicle Statistics Schemas ---

class TripSummary(BaseModel):
    """Summary information about a trip."""
    id: UUID
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    distance_km: Optional[float] = None
    unsafe_count: int = 0

    class Config:
        from_attributes = True


class BusiestDriver(BaseModel):
    """Information about the busiest driver for a vehicle."""
    driver_profile_id: UUID
    email: str
    trip_count: int


class VehicleStats(BaseModel):
    """Statistics for a vehicle."""
    total_trips: int = 0
    total_distance_km: float = 0.0
    total_unsafe_behaviours: int = 0
    ubpk: float = 0.0


class VehicleStatsResponse(BaseModel):
    """Vehicle statistics response."""
    vehicle_id: UUID
    period: str
    total_trips: int = 0
    total_distance_km: float = 0.0
    total_duration_hours: float = 0.0
    total_unsafe_behaviours: int = 0
    ubpk: float = 0.0
    unique_drivers: int = 0
    busiest_driver: Optional[BusiestDriver] = None


class VehicleDetailResponse(VehicleResponse):
    """Detailed vehicle response with additional information."""
    assigned_drivers: List[VehicleDriverInfo] = []
    recent_trips: List[TripSummary] = []
    stats: VehicleStats

    class Config:
        from_attributes = True


class VehicleTripsResponse(BaseModel):
    """Paginated list of trips for a vehicle."""
    trips: List[TripSummary]
    total: int
    page: int
    page_size: int
