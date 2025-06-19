from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date
from typing import List

class DriverUBPK(BaseModel):
    """UBPK metric for a driver."""
    driverProfileId: UUID = Field(..., description="Driver profile identifier")
    ubpk: float = Field(..., description="Unsafe behaviours per kilometre")

    class Config:
        from_attributes = True

class TripUBPK(BaseModel):
    """UBPK metric for a single trip."""
    trip_id: UUID
    driverProfileId: UUID
    ubpk: float

    class Config:
        from_attributes = True

class WeeklyDriverUBPK(BaseModel):
    """Weekly UBPK metric for a driver."""
    driverProfileId: UUID
    week_start: date
    ubpk: float

    class Config:
        from_attributes = True

class ImprovementSummary(BaseModel):
    """Result of improvement analysis for a driver."""
    driverProfileId: UUID
    improved: bool
    p_value: float

    class Config:
        from_attributes = True
