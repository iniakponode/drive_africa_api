from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    driverProfileId: UUID
    ubpk: float
    unsafe_count: int
    distance_km: float


class LeaderboardResponse(BaseModel):
    period: str
    start_date: datetime
    end_date: datetime
    total_drivers: int
    best: List[LeaderboardEntry]
    worst: List[LeaderboardEntry]


class DriverPeriodUBPK(BaseModel):
    period_start: datetime
    period_end: datetime
    ubpk: float
    unsafe_count: int
    distance_km: float


class DriverUBPKSeriesResponse(BaseModel):
    driverProfileId: UUID
    period: str
    start_date: datetime
    end_date: datetime
    series: List[DriverPeriodUBPK]


class BadDaysThresholds(BaseModel):
    day: float
    week: float
    month: float


class BadDaysSummary(BaseModel):
    driverProfileId: UUID
    bad_days: int
    bad_weeks: int
    bad_months: int
    last_day_delta: Optional[float]
    last_week_delta: Optional[float]
    last_month_delta: Optional[float]


class BadDaysResponse(BaseModel):
    thresholds: BadDaysThresholds
    drivers: List[BadDaysSummary]


class DriverKpiSummary(BaseModel):
    driverProfileId: UUID
    ubpk: float
    unsafe_count: int
    distance_km: float
    bad_days: int
    bad_weeks: int
    bad_months: int


class DriverKpiResponse(BaseModel):
    period: str
    start_date: datetime
    end_date: datetime
    drivers: List[DriverKpiSummary]
