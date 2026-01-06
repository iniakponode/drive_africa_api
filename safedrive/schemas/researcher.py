from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from safedrive.schemas.alcohol_questionnaire import AlcoholQuestionnaireResponseSchema
from safedrive.schemas.behaviour_metrics import DriverUBPK, TripUBPK


class UnsafeBehaviourSummary(BaseModel):
    behaviour_type: str
    total: int
    avg_severity: float
    min_severity: float
    max_severity: float


class RawSensorSummary(BaseModel):
    sensor_type: int
    sensor_type_name: str
    total: int
    min_timestamp: Optional[int]
    max_timestamp: Optional[int]
    avg_accuracy: float


class ResearcherTripMetadata(BaseModel):
    id: UUID
    driverProfileId: UUID
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    start_time: Optional[int] = Field(None, alias="startTime")
    end_time: Optional[int] = None
    influence: Optional[str] = None
    trip_notes: Optional[str] = Field(None, alias="tripNotes")
    alcohol_probability: Optional[float] = Field(None, alias="alcoholProbability")
    user_alcohol_response: Optional[str] = Field(None, alias="userAlcoholResponse")
    matched_questionnaire: Optional[AlcoholQuestionnaireResponseSchema] = Field(
        None, alias="matchedQuestionnaire"
    )
    sync: Optional[bool] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class ResearcherTripAlcoholBundle(BaseModel):
    driverProfileId: Optional[UUID] = None
    start_date: Optional[datetime] = Field(None, alias="startDate")
    end_date: Optional[datetime] = Field(None, alias="endDate")
    matching_rule: str = Field(..., alias="matchingRule")
    matching_timezone: str = Field(..., alias="matchingTimezone")
    total_trips: int
    total_questionnaires: int
    trips: List[ResearcherTripMetadata]
    questionnaires: List[AlcoholQuestionnaireResponseSchema]

    class Config:
        from_attributes = True
        populate_by_name = True


class IngestionStatusItem(BaseModel):
    dataset: str
    total: int
    synced: int
    unsynced: int
    latest_record_at: Optional[datetime] = None


class IngestionStatusResponse(BaseModel):
    generated_at: datetime
    datasets: List[IngestionStatusItem]


class AggregatedSnapshotResponse(BaseModel):
    generated_at: datetime
    ubpk_per_driver: List[DriverUBPK]
    ubpk_per_trip: List[TripUBPK]
    unsafe_behaviour_summary: List[UnsafeBehaviourSummary]
    raw_sensor_summary: List[RawSensorSummary]
