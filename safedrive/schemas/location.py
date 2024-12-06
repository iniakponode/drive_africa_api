from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class LocationBase(BaseModel):
    """
    Base schema for the Location model.

    Attributes:
    - **id**: The unique identifier for each location entry.
    - **latitude**: The latitude coordinate of the location.
    - **longitude**: The longitude coordinate of the location.
    - **timestamp**: The timestamp indicating when the location data was recorded (epoch milliseconds).
    - **date**: The date corresponding to the location data.
    - **altitude**: The altitude of the location in meters.
    - **speed**: The speed at the given location.
    - **distance**: The distance traveled from the previous location.
    - **sync**: Indicator whether the data has been synced.
    """
    id: UUID = Field(..., description="The unique identifier for each location entry.")
    latitude: float = Field(..., description="The latitude coordinate of the location.")
    longitude: float = Field(..., description="The longitude coordinate of the location.")
    timestamp: int = Field(..., description="The timestamp when the location data was recorded (epoch milliseconds).")
    date: datetime = Field(..., description="The date corresponding to the location data.")
    altitude: float = Field(..., description="The altitude of the location in meters.")
    speed: float = Field(..., description="The speed at the given location.")
    distance: float = Field(..., description="The distance traveled from the previous location.")
    sync: bool = Field(False, description="Indicates whether the data has been synced.")

    class Config:
        from_attributes = True  # For Pydantic v2

class LocationCreate(BaseModel):
    """
    Schema for creating a new Location record.
    """
    latitude: float = Field(..., description="The latitude coordinate of the location.")
    longitude: float = Field(..., description="The longitude coordinate of the location.")
    timestamp: int = Field(..., description="The timestamp when the location data was recorded (epoch milliseconds).")
    date: datetime = Field(..., description="The date corresponding to the location data.")
    altitude: float = Field(..., description="The altitude of the location in meters.")
    speed: float = Field(..., description="The speed at the given location.")
    distance: float = Field(..., description="The distance traveled from the previous location.")
    sync: Optional[bool] = Field(False, description="Indicates whether the data has been synced.")

    class Config:
        from_attributes = True

class LocationUpdate(BaseModel):
    """
    Schema for updating an existing Location record.

    All fields are optional.
    """
    latitude: Optional[float] = Field(None, description="Optionally update the latitude of the location.")
    longitude: Optional[float] = Field(None, description="Optionally update the longitude of the location.")
    timestamp: Optional[int] = Field(None, description="Optionally update the timestamp of the location.")
    date: Optional[datetime] = Field(None, description="Optionally update the date of the location.")
    altitude: Optional[float] = Field(None, description="Optionally update the altitude.")
    speed: Optional[float] = Field(None, description="Optionally update the speed at the given location.")
    distance: Optional[float] = Field(None, description="Optionally update the distance traveled from the previous location.")
    sync: Optional[bool] = Field(None, description="Optionally update the sync status.")

    class Config:
        from_attributes = True

class LocationResponse(LocationBase):
    """
    Schema for the response format of a Location record.
    """
    pass