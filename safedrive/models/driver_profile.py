from uuid import uuid4, UUID
from sqlalchemy import Column, String, Boolean, BINARY
from sqlalchemy.orm import relationship
from safedrive.database.base import Base
import logging

logger = logging.getLogger(__name__)

def generate_uuid_binary():
    """Generate a binary UUID."""
    return uuid4().bytes

class DriverProfile(Base):
    __tablename__ = "driver_profile"

    driver_profile_id = Column(BINARY(16), primary_key=True, unique=True, default=generate_uuid_binary)
    email = Column(String(50), unique=True, nullable=False)
    sync = Column(Boolean, nullable=False)

    # Relationships
    driving_tips = relationship("DrivingTip", back_populates="profile", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="driver_profile", cascade="all, delete-orphan")
    unsafe_behaviours= relationship("UnsafeBehaviour", back_populates="driver_profile", cascade="all, delete-orphan")
    nlg_reports=relationship("NLGReport", back_populates="driver_profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DriverProfile(driver_profile_id={self.driver_profile_id.hex()}, email={self.email})>"

    @property
    def id_uuid(self) -> UUID:
        uuid_value = UUID(bytes=self.driver_profile_id)
        logger.debug(f"Retrieved UUID for DriverProfile: {uuid_value}")
        return uuid_value