from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DriverProfileReference(BaseModel):
    driverProfileId: Optional[UUID] = None
    email: str
    displayName: Optional[str] = None


class DriverSyncTripPayload(BaseModel):
    id: UUID
    driverProfileId: Optional[UUID] = None
    start_time: int = Field(..., description="Epoch milliseconds.")
    end_time: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    influence: Optional[str] = None
    state: Optional[str] = None
    distance: Optional[float] = None
    averageSpeed: Optional[float] = None
    notes: Optional[str] = None
    sync: Optional[bool] = True


class DriverSyncAlcoholResponse(BaseModel):
    id: Optional[UUID] = None
    driverProfileId: Optional[UUID] = None
    drankAlcohol: Optional[str] = None
    submittedAt: Optional[str] = None
    trip_id: Optional[UUID] = None
    notes: Optional[str] = None


class DriverSyncRawSensorData(BaseModel):
    id: UUID
    sensor_type: int
    sensor_type_name: str
    values: List[float]
    timestamp: int
    date: Optional[datetime] = None
    accuracy: int
    location_id: Optional[UUID] = None
    trip_id: UUID
    driverProfileId: Optional[UUID] = None
    sync: Optional[bool] = False


class DriverSyncUnsafeBehaviour(BaseModel):
    id: UUID
    trip_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    driverProfileId: Optional[UUID] = None
    behaviour_type: str
    severity: float
    timestamp: int
    date: Optional[datetime] = None
    sync: Optional[bool] = False


class DriverSyncPayload(BaseModel):
    profile: DriverProfileReference
    trips: List[DriverSyncTripPayload] = []
    rawSensorData: List[DriverSyncRawSensorData] = []
    unsafeBehaviours: List[DriverSyncUnsafeBehaviour] = []
    alcoholResponses: List[DriverSyncAlcoholResponse] = []


class DriverSyncResponse(BaseModel):
    tripCount: int
    rawSensorCount: int
    unsafeBehaviourCount: int
    alcoholResponseCount: int
    driverProfileId: UUID
