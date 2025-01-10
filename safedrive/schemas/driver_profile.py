from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class DriverProfileBase(BaseModel):
    """
    Base schema for DriverProfile, including common attributes.
    """
    driverProfileId: UUID
    email: str
    sync: bool

    class Config:
        from_attributes = True

class DriverProfileCreate(BaseModel):
    """
    Schema for creating a new DriverProfile.
    
    Attributes:
    - **driverProfileId**: The driver's profile Id
    - **email**: The driver's email (unique).
    - **sync**: Indicates if data is synced (optional).
    """
    driverProfileId: UUID
    email: str
    sync: Optional[bool] = False

class DriverProfileUpdate(BaseModel):
    """
    Schema for updating a DriverProfile.

    Attributes:
    - **email**: Optionally updated email.
    - **sync**: Optionally updated sync status.
    """
    email: Optional[str] = None
    sync: Optional[bool] = None

class DriverProfileResponse(DriverProfileBase):
    """
    Response schema for DriverProfile, with UUID conversion for JSON responses.
    """
    driverProfileId: UUID
    email: str
    sync: bool
    
    class Config:
        from_attributes = True