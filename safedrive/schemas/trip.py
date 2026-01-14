from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from safedrive.schemas.raw_sensor_data import RawSensorDataOut

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
    - **sync**: Indicator whether the trip data has been synced.
    """
    id: UUID = Field(..., description="The unique identifier for the trip.")
    driverProfileId: UUID = Field(..., description="The UUID of the driver's profile.")
    start_date: Optional[datetime] = Field(
        None,
        alias="startDate",
        description="The start date of the trip."
    )
    end_date: Optional[datetime] = Field(
        None,
        alias="endDate",
        description="The end date of the trip."
    )
    start_time: Optional[int] = Field(
        None,
        alias="startTime",
        description="Trip start time in epoch milliseconds."
    )
    end_time: Optional[int] = Field(
        None,
        alias="endTime",
        description="Trip end time in epoch milliseconds."
    )
    sync: bool = Field(False, description="Indicates whether the trip data has been synced.")
    influence: Optional[str] = Field(None, description="records the type of driving influence for the trip.")
    trip_notes: Optional[str] = Field(
        None,
        alias="tripNotes",
        description="Optional driver notes or annotations for the trip."
    )
    alcohol_probability: Optional[float] = Field(
        None,
        alias="alcoholProbability",
        description="Probability score (0.0-1.0) that alcohol influenced the trip."
    )
    user_alcohol_response: Optional[str] = Field(
        None,
        alias="userAlcoholResponse",
        description="User-provided alcohol questionnaire response for the trip day."
    )

    class Config:
        from_attributes = True
        populate_by_name = True


class TripOut(BaseModel):
    id: UUID
    driverProfileId: UUID
    # We'll store a limited set of raw sensor data here
    raw_sensor_data: List[RawSensorDataOut] = []

    class Config:
        from_attributes = True
        populate_by_name = True


class TripCreate(BaseModel):
    """
    Schema for creating a new Trip record.
    """
    id: UUID = Field(..., description="The UUID of the trip's profile.")
    driverProfileId: UUID = Field(..., description="The UUID of the driver's profile.")
    start_date: Optional[datetime] = Field(
        None,
        alias="startDate",
        description="The start date of the trip."
    )
    end_date: Optional[datetime] = Field(
        None,
        alias="endDate",
        description="The end date of the trip."
    )
    start_time: int = Field(
        ..., alias="startTime", description="Trip start time in epoch milliseconds."
    )
    end_time: Optional[int] = Field(
        None, alias="endTime", description="Trip end time in epoch milliseconds."
    )
    sync: Optional[bool] = Field(False, description="Indicates whether the trip data has been synced.")
    influence: Optional[str] = Field(None, description="records the type of driving influence for the trip.")
    trip_notes: Optional[str] = Field(
        None,
        alias="tripNotes",
        description="Optional driver notes or annotations for the trip."
    )
    alcohol_probability: Optional[float] = Field(
        None,
        alias="alcoholProbability",
        description="Probability score that alcohol influenced the trip."
    )
    user_alcohol_response: Optional[str] = Field(
        None,
        alias="userAlcoholResponse",
        description="Calendar day alcohol questionnaire response."
    )

    class Config:
        from_attributes = True
        populate_by_name = True


class TripUpdate(BaseModel):
    """
    Schema for updating an existing Trip record.

    All fields are optional.
    """
    driverProfileId: Optional[UUID] = Field(None, description="Optionally update the driver's profile reference.")
    start_date: Optional[datetime] = Field(
        None,
        alias="startDate",
        description="Optionally update the start date of the trip."
    )
    end_date: Optional[datetime] = Field(
        None,
        alias="endDate",
        description="Optionally update the end date of the trip."
    )
    start_time: Optional[int] = Field(
        None,
        alias="startTime",
        description="Optionally update the trip start time in epoch milliseconds."
    )
    end_time: Optional[int] = Field(
        None,
        alias="endTime",
        description="Optionally update the end time in epoch milliseconds."
    )
    sync: Optional[bool] = Field(None, description="Optionally update the sync status.")
    influence: Optional[str] = Field(None, description="records the type of driving influence for the trip.")
    trip_notes: Optional[str] = Field(
        None,
        alias="tripNotes",
        description="Optional driver notes or annotations for the trip."
    )
    alcohol_probability: Optional[float] = Field(
        None, alias="alcoholProbability", description="Updated alcohol probability score."
    )
    user_alcohol_response: Optional[str] = Field(
        None, alias="userAlcoholResponse", description="Updated alcohol response."
    )

    class Config:
        from_attributes = True
        populate_by_name = True


class TripResponse(TripBase):
    """Schema for the response format of a Trip record."""
    pass
