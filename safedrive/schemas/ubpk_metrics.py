from pydantic import BaseModel
from typing import List
from datetime import date

class TripUBPKResponse(BaseModel):
    tripId: str
    driverProfileId: str
    week: str             # e.g. "2025-W25"
    weekStart: date       # Monday
    weekEnd: date         # Next Monday
    totalUnsafeCount: int
    distanceKm: float
    ubpk: float

class DriverWeekUBPKResponse(BaseModel):
    driverProfileId: str
    week: str
    weekStart: date
    weekEnd: date
    numTrips: int
    ubpkValues: List[float]
    meanUBPK: float

class DriverImprovementResponse(BaseModel):
    driverProfileId: str
    week: str
    previousWeek: str
    previousWeekStart: date
    previousWeekEnd: date
    pValue: float
    meanDifference: float
