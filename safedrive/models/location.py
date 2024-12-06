from sqlalchemy import Column, Float, DateTime, Boolean, BINARY, Integer
from sqlalchemy.orm import relationship
from safedrive.database.base import Base
from uuid import uuid4, UUID

def generate_uuid_binary():
    return uuid4().bytes

class Location(Base):
    """
    Location model representing the geographical information captured during a trip.

    Attributes:
    - **id**: Unique identifier for each location.
    - **latitude**: Latitude of the recorded location.
    - **longitude**: Longitude of the recorded location.
    - **timestamp**: The epoch timestamp when the location was recorded (milliseconds).
    - **date**: The date the location was recorded.
    - **altitude**: Altitude of the recorded location.
    - **speed**: Speed at the recorded location.
    - **distance**: The distance covered from the previous recorded point.
    - **sync**: Status to indicate whether the data has been synced to the server.

    Relationships:
    - **raw_sensor_data**: Relationship with RawSensorData model.
    - **unsafe_behaviours**: Relationship with UnsafeBehaviour model.
    """

    __tablename__ = 'location'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid_binary)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(Integer, nullable=False)  # Epoch milliseconds
    date = Column(DateTime, nullable=False)
    altitude = Column(Float, nullable=False)
    speed = Column(Float, nullable=False)
    distance = Column(Float, nullable=False)
    sync = Column(Boolean, default=False, nullable=False)

    # Relationships
    raw_sensor_data = relationship("RawSensorData", back_populates="location", cascade="all, delete-orphan")
    unsafe_behaviours = relationship("UnsafeBehaviour", back_populates="location", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<Location(id={self.id.hex()}, latitude={self.latitude}, longitude={self.longitude}, "
            f"timestamp={self.timestamp}, date={self.date}, altitude={self.altitude}, "
            f"speed={self.speed}, distance={self.distance}, sync={self.sync})>"
        )

    @property
    def id_uuid(self) -> UUID:
        """Return the UUID representation of the binary ID."""
        return UUID(bytes=self.id)