from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class AIModelInputBase(BaseModel):
    """
    Base schema for AI Model Input entity.

    Attributes:
    - **trip_id**: UUID of the associated trip.
    - **timestamp**: Timestamp of the AI model input.
    - **date**: Date of the AI model input.
    - **hour_of_day_mean**: Mean hour of the day.
    - **day_of_week_mean**: Mean day of the week.
    - **speed_std**: Standard deviation of speed.
    - **course_std**: Standard deviation of course.
    - **acceleration_y_original_mean**: Mean of original Y-axis acceleration.
    """
    trip_id: UUID = Field(..., description="UUID of the associated trip.")
    timestamp: datetime = Field(..., description="Timestamp of the AI model input.")
    date: datetime = Field(..., description="Date of the AI model input.")
    hour_of_day_mean: float = Field(..., description="Mean hour of the day.")
    day_of_week_mean: float = Field(..., description="Mean day of the week.")
    speed_std: float = Field(..., description="Standard deviation of speed.")
    course_std: float = Field(..., description="Standard deviation of course.")
    acceleration_y_original_mean: float = Field(..., description="Mean of original Y-axis acceleration.")
    synced: Optional[bool] = Field(False, description="Indicates whether the AI model input has been synced.")

    class Config:
        from_attributes = True  # For Pydantic v2

class AIModelInputCreate(AIModelInputBase):
    """
    Schema for creating a new AI Model Input.
    """
    pass

class AIModelInputUpdate(BaseModel):
    """
    Schema for updating an existing AI Model Input.

    All fields are optional.
    """
    timestamp: Optional[datetime] = Field(None, description="Timestamp of the AI model input.")
    date: Optional[datetime] = Field(None, description="Date of the AI model input.")
    hour_of_day_mean: Optional[float] = Field(None, description="Mean hour of the day.")
    day_of_week_mean: Optional[float] = Field(None, description="Mean day of the week.")
    speed_std: Optional[float] = Field(None, description="Standard deviation of speed.")
    course_std: Optional[float] = Field(None, description="Standard deviation of course.")
    acceleration_y_original_mean: Optional[float] = Field(None, description="Mean of original Y-axis acceleration.")
    synced: Optional[bool] = Field(None, description="Indicates whether the AI model input has been synced.")

    class Config:
        from_attributes = True

class AIModelInputResponse(AIModelInputBase):
    """
    Schema for representing an AI Model Input response.

    Inherits from AIModelInputBase and adds the `id` field.
    """
    id: UUID = Field(..., description="UUID of the AI model input.")

    class Config:
        from_attributes = True