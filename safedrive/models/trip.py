from sqlalchemy import Column, DateTime, ForeignKey, Integer, Boolean, BINARY, BigInteger, String, Float, Text
from sqlalchemy.orm import relationship, object_session
from uuid import uuid4, UUID
from sqlalchemy_utils import UUIDType
from safedrive.database.base import Base
from safedrive.models.raw_sensor_data import RawSensorData


def generate_uuid_binary():
    return uuid4().bytes

class Trip(Base):
    __tablename__ = "trip"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    driverProfileId = Column(UUIDType(binary=True), ForeignKey('driver_profile.driverProfileId', ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    start_time = Column(BigInteger, nullable=True)  # Changed to BigInteger
    end_time = Column(BigInteger, nullable=True)
    influence = Column(String(50), nullable=True)
    trip_notes = Column(Text, nullable=True)
    sync = Column(Boolean, nullable=False)
    alcohol_probability = Column(Float, nullable=True)
    user_alcohol_response = Column(String(50), nullable=True)

    # Relationships
    ai_model_inputs = relationship("AIModelInput", back_populates="trip", cascade="all, delete-orphan")
    driver_profile = relationship("DriverProfile", back_populates="trips")
    raw_sensor_data = relationship("RawSensorData", back_populates="trip", cascade="all, delete-orphan")
    unsafe_behaviours = relationship("UnsafeBehaviour", back_populates="trip")
    
    # "Limited" relationship: you'd need a separate technique,
    # e.g. a property that queries the top N sensor data.
    @property
    def limited_raw_sensor_data(self):
        session = object_session(self)
        if not session:
            return []

        return (session.query(RawSensorData)
                       .filter(RawSensorData.trip_id == self.id)
                       .limit(10)
                       .all())

    def __repr__(self):
        return f"<Trip(id={self.id}, driver_profile_id={self.driverProfileId})>"

    @property
    def id_uuid(self) -> UUID:
        """
        If self.id is already a uuid.UUID, just return it.
        Otherwise, treat it as raw bytes and convert to a UUID object.
        """
        if isinstance(self.id, UUID):
            return self.id
        return UUID(bytes=self.id)

    @property
    def driver_profile_id_uuid(self) -> UUID:
        if isinstance(self.driverProfileId, UUID):
            return self.driverProfileId
        return UUID(bytes=self.driverProfileId)
