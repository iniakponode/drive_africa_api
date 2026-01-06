from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class FleetBase(BaseModel):
    name: str
    description: Optional[str] = None
    region: Optional[str] = None


class FleetCreate(FleetBase):
    pass


class FleetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    region: Optional[str] = None


class FleetResponse(FleetBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True


class VehicleGroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    fleet_id: UUID


class VehicleGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    fleet_id: Optional[UUID] = None


class VehicleGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class VehicleGroupResponse(VehicleGroupBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True


class DriverFleetAssignmentCreate(BaseModel):
    driverProfileId: UUID
    fleet_id: UUID
    vehicle_group_id: Optional[UUID] = None
    onboarding_completed: Optional[bool] = False
    compliance_note: Optional[str] = None


class DriverFleetAssignmentResponse(DriverFleetAssignmentCreate):
    id: UUID
    assigned_at: datetime
    fleet: Optional[FleetResponse] = None
    vehicle_group: Optional[VehicleGroupResponse] = None

    class Config:
        orm_mode = True


class AlcoholQuestionnaireSummary(BaseModel):
    id: UUID
    driverProfileId: UUID
    drankAlcohol: bool
    plansToDrive: bool
    impairmentLevel: int
    date: Optional[datetime]

    class Config:
        orm_mode = True


class DriverAssignmentWithCompliance(BaseModel):
    assignment: DriverFleetAssignmentResponse
    questionnaire: Optional[AlcoholQuestionnaireSummary]


class DriverTripEventCreate(BaseModel):
    driverProfileId: UUID
    event_type: str
    trip_id: Optional[UUID] = None
    message: Optional[str] = None
    gps_health: Optional[str] = None


class DriverTripEventResponse(DriverTripEventCreate):
    id: UUID
    timestamp: datetime

    class Config:
        orm_mode = True


class DriverTripEventListResponse(BaseModel):
    events: List[DriverTripEventResponse]


class DrivingTipSummary(BaseModel):
    tip_id: UUID
    title: str
    summary_tip: Optional[str]
    llm: Optional[str]
    date: datetime

    class Config:
        from_attributes = True


class SeverityFinding(BaseModel):
    id: UUID
    behaviour_type: str
    severity: float
    timestamp: int

    class Config:
        from_attributes = True


class NLGSummary(BaseModel):
    id: UUID
    report_text: str
    generated_at: datetime

    class Config:
        from_attributes = True


class TripContextResponse(BaseModel):
    trip_id: UUID
    driverProfileId: UUID
    tips: List[DrivingTipSummary]
    severity_findings: List[SeverityFinding]
    nlg_reports: List[NLGSummary]


class TripSummary(BaseModel):
    trip_id: UUID
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    influence: Optional[str]
    distance_km: float
    unsafe_count: int
    avg_severity: float
    speeding_events: int

    class Config:
        from_attributes = True


class UnsafeBehaviourLog(BaseModel):
    id: UUID
    trip_id: UUID
    behaviour_type: str
    severity: float
    timestamp: int

    class Config:
        from_attributes = True


class AlcoholResponseSummary(BaseModel):
    id: UUID
    drankAlcohol: bool
    plansToDrive: bool
    impairmentLevel: int
    date: Optional[datetime]

    class Config:
        from_attributes = True


class SpeedComplianceSummary(BaseModel):
    total_records: int
    speeding_events: int
    compliance_ratio: float


class FleetReportResponse(BaseModel):
    driverProfileId: UUID
    report_generated_at: datetime
    trips: List[TripSummary]
    unsafe_behaviour_logs: List[UnsafeBehaviourLog]
    alcohol_responses: List[AlcoholResponseSummary]
    speed_compliance: SpeedComplianceSummary
