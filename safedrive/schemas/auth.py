from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


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
