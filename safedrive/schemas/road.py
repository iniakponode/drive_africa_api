from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class RoadBase(BaseModel):
    """
    Base schema for Road.
    
    Attributes:
    - **id**: Unique identifier for the road.
    - **driverProfileId**: Identifier for the driver profile.
    - **name**: The road's name.
    - **roadType**: The type of the road (e.g., residential, primary).
    - **speedLimit**: Speed limit of the road.
    - **latitude**: Geographic latitude.
    - **longitude**: Geographic longitude.
    """
    id: UUID
    driverProfileId: UUID
    name: str
    roadType: str
    speedLimit: int
    latitude: float
    longitude: float
    radius: float
    sync: bool

    class Config:
        from_attributes = True

class RoadCreate(RoadBase):
    """
    Schema for creating a new Road entry.
    """
    pass  # Inherits all fields from RoadBase; adjust if needed.

class RoadUpdate(BaseModel):
    """
    Schema for updating an existing Road entry.
    
    All fields are optional for partial updates.
    """
    name: Optional[str] = None
    roadType: Optional[str] = None
    speedLimit: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius: Optional[float]=None
    sync:Optional[float]=None

    class Config:
        from_attributes = True

class RoadResponse(RoadBase):
    """
    Schema for Road response format, inherits from RoadBase.
    """
