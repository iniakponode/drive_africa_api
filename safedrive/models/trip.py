from sqlalchemy import Column, DateTime, ForeignKey, Integer, Boolean, BINARY
from sqlalchemy.orm import relationship
from uuid import uuid4, UUID
from safedrive.database.base import Base

def generate_uuid_binary():
    return uuid4().bytes

class Trip(Base):
    __tablename__ = "trip"

    id = Column(BINARY(16), primary_key=True, default=generate_uuid_binary)
    driver_profile_id = Column(BINARY(16), ForeignKey('driver_profile.driver_profile_id'), nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    start_time = Column(Integer, nullable=False)
    end_time = Column(Integer)
    synced = Column(Boolean, nullable=False)

    # Relationships
    ai_model_inputs = relationship("AIModelInput", back_populates="trip", cascade="all, delete-orphan")
    driver_profile = relationship("DriverProfile", back_populates="trips")
    raw_sensor_data = relationship("RawSensorData", back_populates="trip")
    unsafe_behaviours = relationship("UnsafeBehaviour", back_populates="trip")

    def __repr__(self):
        return f"<Trip(id={self.id.hex()}, driver_profile_id={self.driver_profile_id.hex()})>"

    @property
    def id_uuid(self) -> UUID:
        return UUID(bytes=self.id)

    @property
    def driver_profile_id_uuid(self) -> UUID:
        return UUID(bytes=self.driver_profile_id)