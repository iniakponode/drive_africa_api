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
