from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


# API Client schemas (existing)
class ApiClientBase(BaseModel):
    name: str
    role: str
    active: bool = True
    driverProfileId: Optional[UUID] = None
    fleet_id: Optional[UUID] = None
    insurance_partner_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class ApiClientCreate(ApiClientBase):
    api_key: Optional[str] = Field(
        default=None, description="Optional API key to store (generated if omitted)."
    )


class ApiClientResponse(ApiClientBase):
    id: UUID
    created_at: datetime


class ApiClientCreated(ApiClientResponse):
    api_key: str


class ApiClientUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None
    driverProfileId: Optional[UUID] = None
    fleet_id: Optional[UUID] = None
    insurance_partner_id: Optional[UUID] = None


class AuthMeResponse(BaseModel):
    id: UUID
    name: str
    role: str
    driverProfileId: Optional[UUID] = None
    fleet_id: Optional[UUID] = None
    insurance_partner_id: Optional[UUID] = None


# JWT Authentication schemas (new for mobile app)
class DriverRegister(BaseModel):
    """Schema for driver registration from mobile app."""
    driverProfileId: UUID
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    sync: bool = False


class DriverLogin(BaseModel):
    """Schema for driver login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
    driver_profile_id: UUID
    email: str
    fleet_assignment: Optional[dict] = None  # Added for registration response
    fleet_status: Optional[dict] = None  # Added for login response

