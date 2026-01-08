from sqlalchemy import Boolean, Column, Float, Integer, JSON, String
from sqlalchemy_utils import UUIDType
from safedrive.database.base import Base
from uuid import uuid4, UUID


class ReportStatistics(Base):
    __tablename__ = "report_statistics"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    driverProfileId = Column(UUIDType(binary=True), nullable=False)
    tripId = Column(UUIDType(binary=True), nullable=True)
    startDate = Column(JSON, nullable=True)
    endDate = Column(JSON, nullable=True)
    createdDate = Column(JSON, nullable=True)
    totalIncidences = Column(Integer, nullable=False, default=0)
    mostFrequentUnsafeBehaviour = Column(String(255), nullable=True)
    mostFrequentBehaviourCount = Column(Integer, nullable=False, default=0)
    mostFrequentBehaviourOccurrences = Column(JSON, nullable=True)
    tripWithMostIncidences = Column(JSON, nullable=True)
    tripsPerAggregationUnit = Column(JSON, nullable=True)
    aggregationUnitWithMostIncidences = Column(JSON, nullable=True)
    incidencesPerAggregationUnit = Column(JSON, nullable=True)
    incidencesPerTrip = Column(JSON, nullable=True)
    aggregationLevel = Column(String(50), nullable=True)
    aggregationUnitsWithAlcoholInfluence = Column(Integer, nullable=False, default=0)
    tripsWithAlcoholInfluencePerAggregationUnit = Column(JSON, nullable=True)
    sync = Column(Boolean, nullable=False, default=False)
    processed = Column(Boolean, nullable=False, default=False)
    numberOfTrips = Column(Integer, nullable=False, default=0)
    numberOfTripsWithIncidences = Column(Integer, nullable=False, default=0)
    numberOfTripsWithAlcoholInfluence = Column(Integer, nullable=False, default=0)
    lastTripDuration = Column(JSON, nullable=True)
    lastTripDistance = Column(Float, nullable=True)
    lastTripAverageSpeed = Column(Float, nullable=True)
    lastTripStartLocation = Column(String(255), nullable=True)
    lastTripEndLocation = Column(String(255), nullable=True)
    lastTripStartTime = Column(JSON, nullable=True)
    lastTripEndTime = Column(JSON, nullable=True)
    lastTripInfluence = Column(String(255), nullable=True)

    @property
    def id_uuid(self) -> UUID:
        return self.id
