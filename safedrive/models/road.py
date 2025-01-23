from sqlalchemy import Boolean, Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
from safedrive.database.base import Base
from uuid import uuid4, UUID

class Road(Base):
    __tablename__ = "roads"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    driverProfileId = Column(UUIDType(binary=True), ForeignKey('driver_profile.driverProfileId'), nullable=False)
    name = Column(String(255), nullable=False)
    roadType = Column(String(100), nullable=False)
    speedLimit = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius=Column(Float, nullable=False)
    sync=Column(Boolean, nullable=False)
    
    # Define relationship with DriverProfile if needed
    driver_profile = relationship("DriverProfile", back_populates="roads")

    def __repr__(self):
        return f"<Road(id={self.id}, name={self.name}, type={self.roadType}, speedLimit={self.speedLimit})>"

    @property
    def id_uuid(self) -> UUID:
        return UUID(bytes=self.id)