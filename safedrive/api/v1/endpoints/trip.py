from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from safedrive.database.db import get_db
from safedrive.models.trip import Trip
from safedrive.schemas.trip import TripCreatePayload, TripResponsePayload, _format_local_time

router = APIRouter(tags=["trips"])


def _trip_to_payload(trip: Trip) -> TripResponsePayload:
    def normalize_epoch_ms(value: object) -> int | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return int(value.timestamp() * 1000)
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    return TripResponsePayload(
        id=UUID(trip.id),
        driverProfileId=UUID(trip.driverProfileId),
        startDate=trip.start_date,
        endDate=trip.end_date,
        startTime=normalize_epoch_ms(trip.start_time),
        endTime=normalize_epoch_ms(trip.end_time),
        startTimeLocal=_format_local_time(
            normalize_epoch_ms(trip.start_time),
            trip.timeZoneId,
            trip.timeZoneOffsetMinutes,
        ),
        endTimeLocal=_format_local_time(
            normalize_epoch_ms(trip.end_time),
            trip.timeZoneId,
            trip.timeZoneOffsetMinutes,
        ),
        timeZoneId=trip.timeZoneId,
        timeZoneOffsetMinutes=trip.timeZoneOffsetMinutes,
        sync=trip.sync,
        influence=trip.influence,
        userAlcoholResponse=trip.userAlcoholResponse,
        alcoholProbability=trip.alcoholProbability,
        notes=trip.notes,
    )


def _populate_trip_from_payload(trip: Trip, payload: TripCreatePayload) -> Trip:
    if payload.driverProfileId:
        trip.driverProfileId = str(payload.driverProfileId)
    if payload.startDate is not None:
        trip.start_date = payload.startDate
    if payload.endDate is not None:
        trip.end_date = payload.endDate
    if payload.startTime is not None:
        trip.start_time = payload.startTime
    if payload.endTime is not None:
        trip.end_time = payload.endTime
    if payload.influence is not None:
        trip.influence = payload.influence
    if payload.userAlcoholResponse is not None:
        trip.userAlcoholResponse = payload.userAlcoholResponse
    if payload.alcoholProbability is not None:
        trip.alcoholProbability = payload.alcoholProbability
    if payload.notes is not None:
        trip.notes = payload.notes
    if payload.timeZoneId is not None:
        trip.timeZoneId = payload.timeZoneId
    if payload.timeZoneOffsetMinutes is not None:
        trip.timeZoneOffsetMinutes = payload.timeZoneOffsetMinutes
    trip.sync = payload.sync
    return trip


@router.post("/trips/", response_model=TripResponsePayload)
def create_trip(payload: TripCreatePayload, db: Session = Depends(get_db)) -> TripResponsePayload:
    if not payload.driverProfileId:
        raise HTTPException(status_code=400, detail="driverProfileId is required for trips.")
    trip = Trip(
        id=str(payload.id),
        driverProfileId=str(payload.driverProfileId),
        start_date=payload.startDate,
        end_date=payload.endDate,
        start_time=payload.startTime or 0,
        end_time=payload.endTime,
        influence=payload.influence,
        userAlcoholResponse=payload.userAlcoholResponse,
        alcoholProbability=payload.alcoholProbability,
        notes=payload.notes,
        timeZoneId=payload.timeZoneId,
        timeZoneOffsetMinutes=payload.timeZoneOffsetMinutes,
        sync=payload.sync,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return _trip_to_payload(trip)


@router.put("/trips/{trip_id}", response_model=TripResponsePayload)
def update_trip(trip_id: UUID, payload: TripCreatePayload, db: Session = Depends(get_db)) -> TripResponsePayload:
    trip = db.query(Trip).filter(Trip.id == str(trip_id)).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found.")
    trip = _populate_trip_from_payload(trip, payload)
    db.commit()
    db.refresh(trip)
    return _trip_to_payload(trip)


@router.get("/trips/{trip_id}", response_model=TripResponsePayload)
def get_trip(trip_id: UUID, db: Session = Depends(get_db)) -> TripResponsePayload:
    trip = db.query(Trip).filter(Trip.id == str(trip_id)).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found.")
    return _trip_to_payload(trip)


@router.get("/trips/", response_model=list[TripResponsePayload])
def list_trips(
    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1), db: Session = Depends(get_db)
) -> list[TripResponsePayload]:
    trips = (
        db.query(Trip)
        .order_by(Trip.start_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_trip_to_payload(trip) for trip in trips]


@router.delete("/trips/{trip_id}", status_code=204)
def delete_trip(trip_id: UUID, db: Session = Depends(get_db)):
    deleted = db.query(Trip).filter(Trip.id == str(trip_id)).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="Trip not found.")
    db.commit()


@router.post("/trips/batch_create")
def batch_create_trips(trips: list[TripCreatePayload], db: Session = Depends(get_db)):
    created = 0
    for payload in trips:
        if not payload.driverProfileId:
            continue
        existing = db.query(Trip).filter(Trip.id == str(payload.id)).first()
        if existing:
            continue
        trip = Trip(
            id=str(payload.id),
            driverProfileId=str(payload.driverProfileId),
            start_date=payload.startDate,
            end_date=payload.endDate,
            start_time=payload.startTime or 0,
            end_time=payload.endTime,
            influence=payload.influence,
            userAlcoholResponse=payload.userAlcoholResponse,
            alcoholProbability=payload.alcoholProbability,
            notes=payload.notes,
            sync=payload.sync,
        )
        db.add(trip)
        created += 1
    db.commit()
    return {"created": created}


@router.delete("/trips/batch_delete")
def batch_delete_trips(ids: list[UUID], db: Session = Depends(get_db)):
    deleted = db.query(Trip).filter(Trip.id.in_([str(i) for i in ids])).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}
