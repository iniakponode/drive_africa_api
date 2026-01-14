from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from safedrive.database.base import Base


class Trip(Base):
    __tablename__ = "trip"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    driverProfileId = Column(String(36), nullable=False, index=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    start_time = Column(BigInteger, nullable=False)
    end_time = Column(BigInteger, nullable=True)
    influence = Column(String(64), nullable=True)
    state = Column(String(32), nullable=True)
    distance = Column(Float, nullable=True)
    averageSpeed = Column(Float, nullable=True)
    alcoholProbability = Column(Float, nullable=True)
    userAlcoholResponse = Column(String(4), nullable=True)
    timeZoneId = Column("time_zone_id", String(64), nullable=True)
    timeZoneOffsetMinutes = Column("time_zone_offset_minutes", Integer, nullable=True)
    sync = Column(Boolean, default=False)
    notes = Column(String, nullable=True)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Trip {self.id} for {self.driverProfileId}>"
