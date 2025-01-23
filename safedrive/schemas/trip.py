from pydantic import BaseModel, Field
import sqlalchemy
from typing import Optional
from uuid import UUID
from datetime import datetime

class TripBase(BaseModel):
    """
    Base schema for the Trip model.

    Attributes:
    - **id**: The unique identifier for the trip.
    - **driverProfileId**: The foreign key reference to the driver's profile.
    - **start_date**: The start date of the trip.
    - **end_date**: The end date of the trip.
    - **start_time**: The start time of the trip in epoch milliseconds.
    - **end_time**: The end time of the trip in epoch milliseconds.
    - **synced**: Indicator whether the trip data has been synced.
    """
    id: UUID = Field(..., description="The unique identifier for the trip.")
    driverProfileId: UUID = Field(..., description="The UUID of the driver's profile.")
    start_date: Optional[datetime] = Field(None, description="The start date of the trip.")
    end_date: Optional[datetime] = Field(None, description="The end date of the trip.")
    start_time: Optional[int] = Field(..., description="The start time of the trip in epoch milliseconds.")
    end_time: Optional[int] = Field(None, description="The end time of the trip in epoch milliseconds.")
    sync: bool = Field(False, description="Indicates whether the trip data has been synced.")

    class Config:
        from_attributes = True  # For Pydantic v2

class TripCreate(BaseModel):
    """
    Schema for creating a new Trip record.
    """
    id: UUID=Field(..., description="The UUID of the trip's profile.")
    driverProfileId: UUID = Field(..., description="The UUID of the driver's profile.")
    start_date: Optional[datetime] = Field(None, description="The start date of the trip.")
    end_date: Optional[datetime] = Field(None, description="The end date of the trip.")
    start_time: int = Field(..., description="The start time of the trip in epoch milliseconds.")
    end_time: Optional[int] = Field(None, description="The end time of the trip in epoch milliseconds.")
    sync: Optional[bool] = Field(False, description="Indicates whether the trip data has been synced.")

    class Config:
        from_attributes = True

class TripUpdate(BaseModel):
    """
    Schema for updating an existing Trip record.

    All fields are optional.
    """
    driverProfileId: Optional[UUID] = Field(None, description="Optionally update the driver's profile reference.")
    start_date: Optional[datetime] = Field(None, description="Optionally update the start date of the trip.")
    end_date: Optional[datetime] = Field(None, description="Optionally update the end date of the trip.")
    start_time: Optional[int] = Field(None, description="Optionally update the start time of the trip in epoch milliseconds.")
    end_time: Optional[int] = Field(None, description="Optionally update the end time of the trip in epoch milliseconds.")
    sync: Optional[bool] = Field(None, description="Optionally update the sync status.")

    class Config:
        from_attributes = True

class TripResponse(TripBase):
    """
    Schema for the response format of a Trip record.
    """
    pass