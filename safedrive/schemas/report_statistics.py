from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class ReportStatisticsBase(BaseModel):
    id: UUID
    driverProfileId: UUID
    tripId: Optional[UUID] = None
    startDate: Optional[Any] = None
    endDate: Optional[Any] = None
    createdDate: Optional[Any] = None
    totalIncidences: int = 0
    mostFrequentUnsafeBehaviour: Optional[str] = None
    mostFrequentBehaviourCount: int = 0
    mostFrequentBehaviourOccurrences: Optional[Any] = None
    tripWithMostIncidences: Optional[Any] = None
    tripsPerAggregationUnit: Optional[Any] = None
    aggregationUnitWithMostIncidences: Optional[Any] = None
    incidencesPerAggregationUnit: Optional[Any] = None
    incidencesPerTrip: Optional[Any] = None
    aggregationLevel: Optional[str] = None
    aggregationUnitsWithAlcoholInfluence: int = 0
    tripsWithAlcoholInfluencePerAggregationUnit: Optional[Any] = None
    sync: bool = False
    processed: bool = False
    numberOfTrips: int = 0
    numberOfTripsWithIncidences: int = 0
    numberOfTripsWithAlcoholInfluence: int = 0
    lastTripDuration: Optional[Any] = None
    lastTripDistance: Optional[float] = None
    lastTripAverageSpeed: Optional[float] = None
    lastTripStartLocation: Optional[str] = None
    lastTripEndLocation: Optional[str] = None
    lastTripStartTime: Optional[Any] = None
    lastTripEndTime: Optional[Any] = None
    lastTripInfluence: Optional[str] = None

    class Config:
        from_attributes = True


class ReportStatisticsCreate(ReportStatisticsBase):
    pass


class ReportStatisticsUpdate(BaseModel):
    driverProfileId: Optional[UUID] = None
    tripId: Optional[UUID] = None
    startDate: Optional[Any] = None
    endDate: Optional[Any] = None
    createdDate: Optional[Any] = None
    totalIncidences: Optional[int] = None
    mostFrequentUnsafeBehaviour: Optional[str] = None
    mostFrequentBehaviourCount: Optional[int] = None
    mostFrequentBehaviourOccurrences: Optional[Any] = None
    tripWithMostIncidences: Optional[Any] = None
    tripsPerAggregationUnit: Optional[Any] = None
    aggregationUnitWithMostIncidences: Optional[Any] = None
    incidencesPerAggregationUnit: Optional[Any] = None
    incidencesPerTrip: Optional[Any] = None
    aggregationLevel: Optional[str] = None
    aggregationUnitsWithAlcoholInfluence: Optional[int] = None
    tripsWithAlcoholInfluencePerAggregationUnit: Optional[Any] = None
    sync: Optional[bool] = None
    processed: Optional[bool] = None
    numberOfTrips: Optional[int] = None
    numberOfTripsWithIncidences: Optional[int] = None
    numberOfTripsWithAlcoholInfluence: Optional[int] = None
    lastTripDuration: Optional[Any] = None
    lastTripDistance: Optional[float] = None
    lastTripAverageSpeed: Optional[float] = None
    lastTripStartLocation: Optional[str] = None
    lastTripEndLocation: Optional[str] = None
    lastTripStartTime: Optional[Any] = None
    lastTripEndTime: Optional[Any] = None
    lastTripInfluence: Optional[str] = None


class ReportStatisticsResponse(ReportStatisticsBase):
    pass
