from typing import Optional
from sqlalchemy import JSON, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.orm import relationship
from safedrive.database.base import Base
from uuid import uuid4, UUID
import json

def generate_uuid_binary():
    return uuid4().bytes

class RawSensorData(Base):
    """
    Represents raw sensor data collected from sensors.

    Attributes:
    - **id**: Unique identifier for the raw sensor data.
    - **sensor_type**: Type of the sensor (e.g., accelerometer, gyroscope).
    - **sensor_type_name**: Name of the sensor type.
    - **values**: Sensor readings, stored as a JSON-encoded string.
    - **timestamp**: Timestamp of the sensor reading.
    - **date**: Date when the sensor reading was recorded.
    - **accuracy**: Accuracy level of the sensor reading.
    - **location_id**: Reference to the associated location.
    - **trip_id**: Reference to the associated trip.
    - **sync**: Indicates if the data has been synced.
    """

    __tablename__ = "raw_sensor_data"

    id = Column(BINARY(16), primary_key=True, unique=True, default=generate_uuid_binary)
    sensor_type = Column(Integer, nullable=False)
    sensor_type_name = Column(String(255), nullable=False)
    values = Column(JSON, nullable=False)  # Use JSON to store list data
    timestamp = Column(Integer, nullable=False)
    date = Column(DateTime)
    accuracy = Column(Integer, nullable=False)
    location_id = Column(BINARY(16), ForeignKey('location.id'))
    trip_id = Column(BINARY(16), ForeignKey('trip.id'))
    sync = Column(Boolean, nullable=False)

    # Relationships
    location = relationship("Location", back_populates="raw_sensor_data")
    trip = relationship("Trip", back_populates="raw_sensor_data")

    def __repr__(self):
        return f"<RawSensorData(id={self.id.hex()}, sensor_type={self.sensor_type}, sensor_type_name='{self.sensor_type_name}')>"

    @property
    def id_uuid(self) -> UUID:
        """Return the UUID representation of the binary ID."""
        return UUID(bytes=self.id)

    @property
    def location_id_uuid(self) -> Optional[UUID]:
        """Return the UUID representation of the binary location_id."""
        return UUID(bytes=self.location_id) if self.location_id else None

    @property
    def trip_id_uuid(self) -> Optional[UUID]:
        """Return the UUID representation of the binary trip_id."""
        return UUID(bytes=self.trip_id) if self.trip_id else None

    def to_dict(self):
        """Converts the RawSensorData object to a dictionary representation."""
        return {
            "id": self.id.hex(),
            "sensor_type": self.sensor_type,
            "sensor_type_name": self.sensor_type_name,
            "values": json.loads(self.values),
            "timestamp": self.timestamp,
            "date": self.date.isoformat() if self.date else None,
            "accuracy": self.accuracy,
            "location_id": self.location_id.hex() if self.location_id else None,
            "trip_id": self.trip_id.hex() if self.trip_id else None,
            "sync": self.sync,
        }