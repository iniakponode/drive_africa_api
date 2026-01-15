"""Fleet driver management schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- Fleet Invite Code Schemas ---


class FleetInviteCodeCreate(BaseModel):
    """Schema for creating a fleet invite code."""

    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")
    max_uses: Optional[int] = Field(None, description="Maximum number of uses")


class FleetInviteCodeResponse(BaseModel):
    """Schema for fleet invite code response."""

    id: UUID
    fleet_id: UUID
    code: str
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None
    use_count: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class FleetInviteCodeListResponse(BaseModel):
    """Schema for list of fleet invite codes."""

    invite_codes: List[FleetInviteCodeResponse]


# --- Driver Invite Schemas ---


class DriverInviteCreate(BaseModel):
    """Schema for creating a driver email invitation."""

    email: EmailStr = Field(..., description="Driver's email address")
    vehicle_group_id: Optional[UUID] = Field(
        None, description="Optional pre-assignment to vehicle group"
    )
    expires_at: Optional[datetime] = Field(None, description="Optional expiration")
    send_email: bool = Field(True, description="Whether to send invitation email")


class DriverInviteResponse(BaseModel):
    """Schema for driver invitation response."""

    id: UUID
    fleet_id: UUID
    email: str
    status: str
    invite_token: str
    vehicle_group_id: Optional[UUID] = None
    created_by: UUID
    created_at: datetime
    claimed_at: Optional[datetime] = None
    driver_profile_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DriverInviteListResponse(BaseModel):
    """Schema for paginated list of driver invitations."""

    invites: List[DriverInviteResponse]
    total: int
    page: int
    page_size: int


# --- Driver Join Request Schemas ---


class DriverJoinRequestSubmit(BaseModel):
    """Schema for submitting a join request."""

    invite_code: str = Field(..., description="Fleet invite code")


class DriverJoinRequestResponse(BaseModel):
    """Schema for join request response."""

    message: str
    request_id: UUID
    fleet_name: str
    status: str = "pending"


class JoinRequestInfo(BaseModel):
    """Schema for join request information."""

    id: UUID
    fleet_id: UUID
    driver_profile_id: UUID
    driver_email: Optional[str] = None
    driver_name: Optional[str] = None
    invite_code_used: Optional[str] = None
    status: str
    requested_at: datetime


class JoinRequestListResponse(BaseModel):
    """Schema for list of join requests."""

    requests: List[JoinRequestInfo]


class JoinRequestApprove(BaseModel):
    """Schema for approving a join request."""

    vehicle_group_id: Optional[UUID] = Field(
        None, description="Optional vehicle group assignment"
    )


class JoinRequestReject(BaseModel):
    """Schema for rejecting a join request."""

    reason: Optional[str] = Field(None, description="Reason for rejection")


# --- Fleet Assignment Schemas ---


class FleetAssignmentInfo(BaseModel):
    """Schema for fleet assignment information."""

    id: UUID
    vehicle_group_id: Optional[UUID] = None
    vehicle_group_name: Optional[str] = None
    onboarding_completed: bool
    assigned_at: datetime

    class Config:
        from_attributes = True


class VehicleInfo(BaseModel):
    """Schema for basic vehicle information."""

    id: UUID
    license_plate: str
    make: Optional[str] = None
    model: Optional[str] = None

    class Config:
        from_attributes = True


class FleetDriverInfo(BaseModel):
    """Schema for fleet driver information."""

    driverProfileId: UUID
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    assignment: Optional[FleetAssignmentInfo] = None
    vehicle: Optional[VehicleInfo] = None
    safety_score: Optional[float] = None
    total_trips: int = 0
    last_active: Optional[datetime] = None


class FleetDriverListResponse(BaseModel):
    """Schema for paginated list of fleet drivers."""

    drivers: List[FleetDriverInfo]
    total: int
    page: int
    page_size: int


class FleetDriverAdd(BaseModel):
    """Schema for manually adding a driver to a fleet (admin only)."""

    driver_profile_id: UUID
    vehicle_group_id: Optional[UUID] = None


class FleetDriverUpdate(BaseModel):
    """Schema for updating a driver's fleet assignment."""

    vehicle_group_id: Optional[UUID] = None
    onboarding_completed: Optional[bool] = None
    compliance_note: Optional[str] = None


# --- Fleet Status Schemas (for mobile app) ---


class FleetInfo(BaseModel):
    """Schema for basic fleet information."""

    id: UUID
    name: str

    class Config:
        from_attributes = True


class VehicleGroupInfo(BaseModel):
    """Schema for vehicle group information."""

    id: UUID
    name: str

    class Config:
        from_attributes = True


class PendingRequestInfo(BaseModel):
    """Schema for pending join request information."""

    id: UUID
    fleet_name: str
    requested_at: datetime


class FleetStatusResponse(BaseModel):
    """Schema for driver's fleet status (mobile app)."""

    status: str  # 'assigned', 'pending', 'none'
    fleet: Optional[FleetInfo] = None
    vehicle_group: Optional[VehicleGroupInfo] = None
    vehicle: Optional[VehicleInfo] = None
    pending_request: Optional[PendingRequestInfo] = None


# --- Auth Response Modifications ---


class FleetAssignmentDetail(BaseModel):
    """Schema for fleet assignment details in auth responses."""

    fleet_id: UUID
    fleet_name: str
    vehicle_group_id: Optional[UUID] = None
    vehicle_group_name: Optional[str] = None
    assigned_at: datetime


class UnassignedDriverInfo(BaseModel):
    """Schema for unassigned driver information (admin)."""

    driverProfileId: UUID
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UnassignedDriverListResponse(BaseModel):
    """Schema for list of unassigned drivers."""

    drivers: List[UnassignedDriverInfo]
