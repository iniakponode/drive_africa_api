from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class InsurancePartnerCreate(BaseModel):
    name: str
    label: str
    active: bool = True


class InsurancePartnerResponse(InsurancePartnerCreate):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class InsurancePartnerDriverCreate(BaseModel):
    driverProfileId: UUID


class InsurancePartnerDriverResponse(BaseModel):
    id: UUID
    partner_id: UUID
    driverProfileId: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class InsuranceTelematicsTrip(BaseModel):
    trip_id: UUID
    driverProfileId: UUID
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    influence: Optional[str]
    distance_km: float
    unsafe_count: int
    avg_severity: float
    speeding_events: int
    speed_compliance_ratio: float


class InsuranceTelematicsResponse(BaseModel):
    total: int
    trips: List[InsuranceTelematicsTrip]


class InsuranceAlert(BaseModel):
    driverProfileId: UUID
    trip_id: Optional[UUID]
    alert_type: str
    severity: Optional[float]
    timestamp: Optional[int]
    message: str


class InsuranceAggregateDriverSummary(BaseModel):
    driverProfileId: UUID
    trip_count: int
    distance_km: float
    unsafe_count: int
    avg_severity: float
    speeding_events: int
    alcohol_positive: int
    latest_trip_start: Optional[datetime]


class InsuranceAggregateReport(BaseModel):
    generated_at: datetime
    partner_id: Optional[UUID]
    partner_label: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    total_drivers: int
    total_trips: int
    total_distance_km: float
    total_unsafe_events: int
    avg_unsafe_severity: float
    total_speeding_events: int
    alcohol_positive_responses: int
    drivers: List[InsuranceAggregateDriverSummary]
