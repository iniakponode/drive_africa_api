from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- User Account Schemas ---

class UserAccountBase(BaseModel):
    """Base schema for UserAccount data."""
    email: EmailStr = Field(..., description="User's email address")
    name: Optional[str] = Field(None, max_length=255, description="Display name")
    role: str = Field(..., description="User role (admin, driver, researcher, fleet_manager, insurance_partner)")
    active: bool = Field(True, description="Whether the account is active")


class UserAccountCreate(UserAccountBase):
    """Schema for creating a new user account."""
    password: Optional[str] = Field(None, description="Initial password (if None, user needs to reset)")
    fleet_id: Optional[UUID] = Field(None, description="Fleet ID for fleet_manager role")
    insurance_partner_id: Optional[UUID] = Field(None, description="Insurance partner ID for insurance_partner role")
    driver_profile_id: Optional[UUID] = Field(None, description="Driver profile ID for driver role")


class UserAccountUpdate(BaseModel):
    """Schema for updating a user account (all fields optional)."""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = None
    active: Optional[bool] = None
    fleet_id: Optional[UUID] = None
    insurance_partner_id: Optional[UUID] = None
    driver_profile_id: Optional[UUID] = None


class FleetInfo(BaseModel):
    """Basic fleet information."""
    id: UUID
    name: str
    description: Optional[str] = None
    region: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InsurancePartnerInfo(BaseModel):
    """Basic insurance partner information."""
    id: UUID
    name: str
    label: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserAccountResponse(UserAccountBase):
    """Schema for user account response."""
    id: UUID
    fleet_id: Optional[UUID] = None
    fleet: Optional[FleetInfo] = None
    insurance_partner_id: Optional[UUID] = None
    insurance_partner: Optional[InsurancePartnerInfo] = None
    driver_profile_id: Optional[UUID] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserAccountListResponse(BaseModel):
    """Paginated list of user accounts."""
    users: List[UserAccountResponse]
    total: int
    page: int
    page_size: int


class UserDeactivateResponse(BaseModel):
    """Response for user deactivation."""
    message: str
    user_id: UUID


# --- Manager Info for Fleet Display ---

class ManagerInfo(BaseModel):
    """Minimal manager info for fleet listings."""
    id: UUID
    email: str
    name: Optional[str] = None

    class Config:
        from_attributes = True
