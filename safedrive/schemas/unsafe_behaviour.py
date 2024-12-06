from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class UnsafeBehaviourBase(BaseModel):
    """
    Base schema for Unsafe Behaviour data.

    Attributes:
    - **id**: Unique identifier for the unsafe behaviour.
    - **trip_id**: UUID of the trip associated with this unsafe behaviour.
    - **location_id**: UUID of the location associated with this behaviour.
    - **behaviour_type**: Type of unsafe behaviour observed (e.g., speeding, harsh braking).
    - **severity**: Severity level of the unsafe behaviour.
    - **timestamp**: Epoch timestamp when the behaviour was recorded.
    - **date**: Date when the behaviour occurred.
    - **updated_at**: Timestamp when the record was last updated.
    - **updated**: Indicator of whether the record has been updated.
    - **synced**: Indicator whether the data has been synced.
    - **alcohol_influence**: Indicator if alcohol influence was detected.
    """
    id: UUID = Field(..., description="Unique identifier for the unsafe behaviour.")
    trip_id: UUID = Field(..., description="UUID of the trip associated with this unsafe behaviour.")
    location_id: Optional[UUID] = Field(None, description="UUID of the location associated with this behaviour.")
    driver_profile_id: UUID = Field(..., description="UUID of the driving profile associated with this unsafe behaviour.")
    behaviour_type: str = Field(..., description="Type of unsafe behaviour observed.")
    severity: float = Field(..., description="Severity level of the unsafe behaviour.")
    timestamp: int = Field(..., description="Epoch timestamp when the behaviour was recorded.")
    date: Optional[datetime] = Field(None, description="Date when the behaviour occurred.")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the record was last updated.")
    updated: bool = Field(False, description="Indicator of whether the record has been updated.")
    synced: bool = Field(False, description="Indicator whether the data has been synced.")
    alcohol_influence: bool = Field(False, description="Indicator if alcohol influence was detected.")
    synced: bool = Field(False, description="Indicates whether the data has been synced.")

    class Config:
        from_attributes = True  # For Pydantic v2

class UnsafeBehaviourCreate(BaseModel):
    """
    Schema for creating a new Unsafe Behaviour record.
    """
    trip_id: UUID = Field(..., description="UUID of the trip associated with this unsafe behaviour.")
    location_id: Optional[UUID] = Field(None, description="UUID of the location associated with this behaviour.")
    driver_profile_id: UUID = Field(..., description="UUID of the driving profile associated with this unsafe behaviour.")
    behaviour_type: str = Field(..., description="Type of unsafe behaviour observed.")
    severity: float = Field(..., description="Severity level of the unsafe behaviour.")
    timestamp: int = Field(..., description="Epoch timestamp when the behaviour was recorded.")
    date: Optional[datetime] = Field(None, description="Date when the behaviour occurred.")
    alcohol_influence: bool = Field(False, description="Indicator if alcohol influence was detected.")
    synced: Optional[bool] = Field(False, description="Indicates whether the data has been synced.")

    class Config:
        from_attributes = True

class UnsafeBehaviourUpdate(BaseModel):
    """
    Schema for updating an existing Unsafe Behaviour record.

    All fields are optional.
    """
    location_id: Optional[UUID] = Field(None, description="Optionally update the location associated with this behaviour.")
    trip_id: UUID = Field(..., description="UUID of the trip associated with this unsafe behaviour.")
    driver_profile_id: UUID = Field(..., description="UUID of the driving profile associated with this unsafe behaviour.")
    behaviour_type: Optional[str] = Field(None, description="Optionally update the type of unsafe behaviour.")
    severity: Optional[float] = Field(None, description="Optionally update the severity level.")
    timestamp: Optional[int] = Field(None, description="Optionally update the timestamp when the behaviour was recorded.")
    date: Optional[datetime] = Field(None, description="Optionally update the date when the behaviour occurred.")
    updated_at: Optional[datetime] = Field(None, description="Optionally update the last updated timestamp.")
    updated: Optional[bool] = Field(None, description="Optionally update the updated indicator.")
    synced: Optional[bool] = Field(None, description="Optionally update the sync status.")
    alcohol_influence: Optional[bool] = Field(None, description="Optionally update the alcohol influence indicator.")
    synced: Optional[bool] = Field(None, description="Optionally update the sync status.")

    class Config:
        from_attributes = True

class UnsafeBehaviourResponse(UnsafeBehaviourBase):
    """
    Schema for the response format of Unsafe Behaviour data.
    """
    pass