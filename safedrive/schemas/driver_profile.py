from pydantic import BaseModel, Field, validator, field_validator
from typing import List, Optional
from uuid import UUID

from safedrive.models.trip import Trip
from safedrive.schemas.trip import TripOut

class DriverProfileBase(BaseModel):
    """
    Base schema for DriverProfile, including common attributes.
    """
    driverProfileId: UUID
    email: str
    sync: bool

    class Config:
        from_attributes = True
        
class DriverProfileOut(BaseModel):
    driverProfileId: UUID
    email: str
    # A list of trips, each containing raw sensor data
    trips: List[TripOut] = []

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
    

# class DriverProfileOut(BaseModel):
#     driverProfileId: UUID = Field(...)
#     email: str
#     trips: List[TripOut] = []

#     class Config:
#         from_attributes = True

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
    
    @field_validator("driverProfileId", mode="before")
    def convert_driver_profile_id(cls, v):
        if isinstance(v, bytes):
            return UUID(bytes=v)
        return v
    
    class Config:
        from_attributes = True