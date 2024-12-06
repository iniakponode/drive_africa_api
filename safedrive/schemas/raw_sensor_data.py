from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class RawSensorDataBase(BaseModel):
    """
    Base schema for the Raw Sensor Data model.

    Attributes:
    - **id**: The unique identifier for the sensor data record.
    - **sensor_type**: The type of sensor (e.g., accelerometer, gyroscope).
    - **sensor_type_name**: The name of the sensor type.
    - **values**: A list of sensor readings.
    - **timestamp**: The timestamp when the data was recorded.
    - **date**: The date when the data was recorded.
    - **accuracy**: The accuracy level of the sensor data.
    - **location_id**: The foreign key reference to the location where the data was recorded.
    - **trip_id**: The foreign key reference to the trip associated with the data.
    - **sync**: Indicator whether the data has been synced.
    """
    id: UUID = Field(..., description="The unique identifier for the sensor data record.")
    sensor_type: int = Field(..., description="The type of sensor (e.g., accelerometer, gyroscope).")
    sensor_type_name: str = Field(..., description="The name of the sensor type.")
    values: List[float] = Field(..., description="A list of sensor readings.")
    timestamp: int = Field(..., description="The timestamp when the data was recorded.")
    date: Optional[datetime] = Field(None, description="The date when the data was recorded.")
    accuracy: int = Field(..., description="The accuracy level of the sensor data.")
    location_id: Optional[UUID] = Field(None, description="The UUID of the location associated with the data.")
    trip_id: Optional[UUID] = Field(None, description="The UUID of the trip associated with the data.")
    sync: bool = Field(False, description="Indicates whether the data has been synced.")

    class Config:
        from_attributes = True  # For Pydantic v2

class RawSensorDataCreate(BaseModel):
    """
    Schema for creating a new Raw Sensor Data record.
    """
    sensor_type: int = Field(..., description="The type of sensor (e.g., accelerometer, gyroscope).")
    sensor_type_name: str = Field(..., description="The name of the sensor type.")
    values: List[float] = Field(..., description="A list of sensor readings.")
    timestamp: int = Field(..., description="The timestamp when the data was recorded.")
    date: Optional[datetime] = Field(None, description="The date when the data was recorded.")
    accuracy: int = Field(..., description="The accuracy level of the sensor data.")
    location_id: Optional[UUID] = Field(None, description="The UUID of the location associated with the data.")
    trip_id: Optional[UUID] = Field(None, description="The UUID of the trip associated with the data.")
    sync: Optional[bool] = Field(False, description="Indicates whether the data has been synced.")

    class Config:
        from_attributes = True

class RawSensorDataUpdate(BaseModel):
    """
    Schema for updating an existing Raw Sensor Data record.

    All fields are optional.
    """
    sensor_type: Optional[int] = Field(None, description="Optionally update the type of sensor.")
    sensor_type_name: Optional[str] = Field(None, description="Optionally update the name of the sensor type.")
    values: Optional[List[float]] = Field(None, description="Optionally update the sensor readings.")
    timestamp: Optional[int] = Field(None, description="Optionally update the timestamp when the data was recorded.")
    date: Optional[datetime] = Field(None, description="Optionally update the date when the data was recorded.")
    accuracy: Optional[int] = Field(None, description="Optionally update the accuracy level of the sensor data.")
    location_id: Optional[UUID] = Field(None, description="Optionally update the location reference.")
    trip_id: Optional[UUID] = Field(None, description="Optionally update the trip reference.")
    sync: Optional[bool] = Field(None, description="Optionally update the sync status.")

    class Config:
        from_attributes = True

class RawSensorDataResponse(RawSensorDataBase):
    """
    Schema for the response format of a Raw Sensor Data record.
    """
    pass