from datetime import datetime, timedelta
import io
import json
from typing import Iterable, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from safedrive.core.security import (
    ApiClientContext,
    Role,
    ensure_driver_access,
    filter_query_by_driver_ids,
    require_roles,
)
from safedrive.database.db import get_db
from safedrive.models.alcohol_questionnaire import AlcoholQuestionnaire
from safedrive.models.location import Location
from safedrive.models.raw_sensor_data import RawSensorData
from safedrive.models.trip import Trip
from safedrive.models.unsafe_behaviour import UnsafeBehaviour
from safedrive.schemas.fleet import FleetReportResponse
from safedrive.schemas.insurance_partner import (
    InsuranceAlert,
    InsuranceTelematicsResponse,
    InsuranceTelematicsTrip,
)

router = APIRouter()


def _trip_locations(db: Session, trip_id: UUID) -> List[Location]:
    return (
        db.query(Location)
        .join(RawSensorData, RawSensorData.location_id == Location.id)
        .filter(RawSensorData.trip_id == trip_id)
        .all()
    )


def _build_trip_metrics(trip: Trip, db: Session) -> InsuranceTelematicsTrip:
    locations = _trip_locations(db, trip.id)
    distance = sum((loc.distance or 0) for loc in locations)
    speeding_events = sum(
        1 for loc in locations if loc.speedLimit and loc.speed and loc.speed > loc.speedLimit
    )
    behaviours = (
        db.query(UnsafeBehaviour)
        .filter(UnsafeBehaviour.trip_id == trip.id)
        .all()
    )
    unsafe_count = len(behaviours)
    avg_severity = float(
        sum((beh.severity for beh in behaviours)) / unsafe_count
        if unsafe_count
        else 0.0
    )
    total_locations = len(locations)
    speed_compliance_ratio = (
        (total_locations - speeding_events) / total_locations if total_locations else 1.0
    )
    return InsuranceTelematicsTrip(
        trip_id=trip.id,
        driverProfileId=trip.driverProfileId,
        start_time=trip.start_time and datetime.fromtimestamp(trip.start_time / 1000),
        end_time=trip.end_time and datetime.fromtimestamp(trip.end_time / 1000),
        influence=trip.influence,
        distance_km=distance / 1000.0,
        unsafe_count=unsafe_count,
        avg_severity=avg_severity,
        speeding_events=speeding_events,
        speed_compliance_ratio=speed_compliance_ratio,
    )


def _build_driver_report(db: Session, driver_id: UUID) -> dict:
    trips = (
        db.query(Trip)
        .filter(Trip.driverProfileId == driver_id)
        .order_by(Trip.start_time.desc())
        .all()
    )

    trip_summaries = []
    for trip in trips:
        metrics = _build_trip_metrics(trip, db)
        trip_summaries.append(
            {
                "trip_id": metrics.trip_id,
                "start_time": metrics.start_time,
                "end_time": metrics.end_time,
                "influence": metrics.influence,
                "distance_km": metrics.distance_km,
                "unsafe_count": metrics.unsafe_count,
                "avg_severity": metrics.avg_severity,
                "speeding_events": metrics.speeding_events,
            }
        )

    unsafe_logs = (
        db.query(UnsafeBehaviour)
        .filter(UnsafeBehaviour.driverProfileId == driver_id)
        .order_by(UnsafeBehaviour.timestamp.desc())
        .limit(100)
        .all()
    )

    locations = (
        db.query(Location)
        .join(RawSensorData, RawSensorData.location_id == Location.id)
        .join(Trip, RawSensorData.trip_id == Trip.id)
        .filter(Trip.driverProfileId == driver_id)
        .all()
    )

    total_locations = len(locations)
    speeding_events = sum(
        1 for loc in locations if loc.speedLimit and loc.speed and loc.speed > loc.speedLimit
    )

    questionnaires = (
        db.query(AlcoholQuestionnaire)
        .filter(AlcoholQuestionnaire.driverProfileId == driver_id)
        .order_by(AlcoholQuestionnaire.date.desc())
        .all()
    )

    return {
        "driverProfileId": driver_id,
        "report_generated_at": datetime.utcnow(),
        "trips": trip_summaries,
        "unsafe_behaviour_logs": [
            {
                "id": log.id,
                "trip_id": log.trip_id,
                "behaviour_type": log.behaviour_type,
                "severity": log.severity,
                "timestamp": log.timestamp,
            }
            for log in unsafe_logs
        ],
        "alcohol_responses": [
            {
                "id": response.id,
                "drankAlcohol": response.drankAlcohol,
                "plansToDrive": response.plansToDrive,
                "impairmentLevel": response.impairmentLevel,
                "date": response.date,
            }
            for response in questionnaires
        ],
        "speed_compliance": {
            "total_records": total_locations,
            "speeding_events": speeding_events,
            "compliance_ratio": (
                (total_locations - speeding_events) / total_locations
                if total_locations
                else 1.0
            ),
        },
    }


@router.get("/insurance/telematics/trips", response_model=InsuranceTelematicsResponse)
def list_insurance_trips(
    driver_profile_id: Optional[UUID] = Query(None, alias="driverProfileId"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.INSURANCE_PARTNER)
    ),
) -> InsuranceTelematicsResponse:
    query = db.query(Trip)
    query = filter_query_by_driver_ids(query, Trip.driverProfileId, current_client)
    if driver_profile_id:
        ensure_driver_access(current_client, driver_profile_id)
        query = query.filter(Trip.driverProfileId == driver_profile_id)
    if start_date:
        query = query.filter(Trip.start_date >= start_date)
    if end_date:
        query = query.filter(Trip.start_date <= end_date)
    trips = (
        query.order_by(Trip.start_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    metrics = [_build_trip_metrics(trip, db) for trip in trips]
    return InsuranceTelematicsResponse(total=len(metrics), trips=metrics)


@router.get("/insurance/reports/{driver_id}", response_model=FleetReportResponse)
def get_insurance_driver_report(
    driver_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.INSURANCE_PARTNER)
    ),
) -> FleetReportResponse:
    ensure_driver_access(current_client, driver_id)
    payload = _build_driver_report(db, driver_id)
    return FleetReportResponse.model_validate(payload)


@router.get("/insurance/reports/{driver_id}/download")
def download_insurance_driver_report(
    driver_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.INSURANCE_PARTNER)
    ),
):
    ensure_driver_access(current_client, driver_id)
    report_data = _build_driver_report(db, driver_id)
    payload = json.dumps(report_data, default=str).encode("utf-8")
    buffer = io.BytesIO(payload)
    headers = {
        "Content-Disposition": f'attachment; filename="insurance_report_{driver_id}.json"'
    }
    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers=headers,
    )


@router.get("/insurance/raw_sensor_data/export")
def export_insurance_raw_sensor_data(
    driver_profile_id: Optional[UUID] = Query(None, alias="driverProfileId"),
    trip_id: Optional[UUID] = Query(None, alias="tripId"),
    start_timestamp: Optional[int] = Query(None, alias="startTimestamp"),
    end_timestamp: Optional[int] = Query(None, alias="endTimestamp"),
    export_format: str = Query("jsonl", alias="format"),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.INSURANCE_PARTNER)
    ),
):
    export_format = (export_format or "").lower()
    if export_format not in {"jsonl", "csv"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Supported values are 'jsonl' and 'csv'.",
        )

    query = db.query(RawSensorData, Trip.driverProfileId).outerjoin(
        Trip, RawSensorData.trip_id == Trip.id
    )
    query = filter_query_by_driver_ids(query, Trip.driverProfileId, current_client)
    if driver_profile_id:
        ensure_driver_access(current_client, driver_profile_id)
        query = query.filter(Trip.driverProfileId == driver_profile_id)
    if trip_id:
        query = query.filter(RawSensorData.trip_id == trip_id)
    if start_timestamp is not None:
        query = query.filter(RawSensorData.timestamp >= start_timestamp)
    if end_timestamp is not None:
        query = query.filter(RawSensorData.timestamp <= end_timestamp)
    query = query.order_by(RawSensorData.timestamp.asc())

    def _record_payload(row) -> dict:
        raw, driver_id = row
        return {
            "id": str(raw.id),
            "driverProfileId": str(driver_id) if driver_id else None,
            "sensor_type": raw.sensor_type,
            "sensor_type_name": raw.sensor_type_name,
            "values": raw.values,
            "timestamp": raw.timestamp,
            "date": raw.date,
            "accuracy": raw.accuracy,
            "location_id": str(raw.location_id) if raw.location_id else None,
            "trip_id": str(raw.trip_id) if raw.trip_id else None,
            "sync": raw.sync,
        }

    if export_format == "csv":
        header = [
            "id",
            "driverProfileId",
            "sensor_type",
            "sensor_type_name",
            "values",
            "timestamp",
            "date",
            "accuracy",
            "location_id",
            "trip_id",
            "sync",
        ]

        def rows() -> Iterable[str]:
            yield ",".join(header) + "\n"
            for raw, driver_id in query.yield_per(500):
                payload = _record_payload((raw, driver_id))
                values = [
                    payload["id"],
                    payload["driverProfileId"] or "",
                    str(payload["sensor_type"]),
                    payload["sensor_type_name"],
                    json.dumps(payload["values"], default=str),
                    str(payload["timestamp"]),
                    str(payload["date"]) if payload["date"] else "",
                    str(payload["accuracy"]),
                    payload["location_id"] or "",
                    payload["trip_id"] or "",
                    str(payload["sync"]),
                ]
                yield ",".join(values) + "\n"

        headers = {
            "Content-Disposition": "attachment; filename=\"insurance_raw_sensor_data.csv\""
        }
        return StreamingResponse(
            rows(),
            media_type="text/csv",
            headers=headers,
        )

    def jsonl_rows() -> Iterable[bytes]:
        for raw, driver_id in query.yield_per(500):
            payload = _record_payload((raw, driver_id))
            yield (json.dumps(payload, default=str) + "\n").encode("utf-8")

    headers = {
        "Content-Disposition": "attachment; filename=\"insurance_raw_sensor_data.jsonl\""
    }
    return StreamingResponse(
        jsonl_rows(),
        media_type="application/x-ndjson",
        headers=headers,
    )


@router.get("/insurance/alerts", response_model=List[InsuranceAlert])
def list_insurance_alerts(
    min_severity: float = Query(0.8, alias="minSeverity"),
    since_hours: int = Query(24, alias="sinceHours", ge=1, le=168),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.INSURANCE_PARTNER)
    ),
) -> List[InsuranceAlert]:
    since_ms = int((datetime.utcnow() - timedelta(hours=since_hours)).timestamp() * 1000)
    unsafe_query = db.query(UnsafeBehaviour)
    unsafe_query = filter_query_by_driver_ids(
        unsafe_query, UnsafeBehaviour.driverProfileId, current_client
    )
    unsafe_query = unsafe_query.filter(
        UnsafeBehaviour.timestamp >= since_ms,
        UnsafeBehaviour.severity >= min_severity,
    )
    unsafe_events = unsafe_query.order_by(UnsafeBehaviour.timestamp.desc()).limit(limit).all()

    alerts: List[InsuranceAlert] = [
        InsuranceAlert(
            driverProfileId=event.driverProfileId,
            trip_id=event.trip_id,
            alert_type="unsafe_behaviour",
            severity=event.severity,
            timestamp=event.timestamp,
            message=f"Unsafe behaviour {event.behaviour_type} severity {event.severity}",
        )
        for event in unsafe_events
    ]

    speed_query = (
        db.query(Location, Trip.id, Trip.driverProfileId)
        .join(RawSensorData, RawSensorData.location_id == Location.id)
        .join(Trip, RawSensorData.trip_id == Trip.id)
        .filter(Location.speedLimit.isnot(None))
        .filter(Location.speed.isnot(None))
        .filter(Location.speed > Location.speedLimit)
    )
    speed_query = filter_query_by_driver_ids(
        speed_query, Trip.driverProfileId, current_client
    )
    speed_events = speed_query.limit(limit).all()
    for loc, trip_id, driver_id in speed_events:
        alerts.append(
            InsuranceAlert(
                driverProfileId=driver_id,
                trip_id=trip_id,
                alert_type="speed_violation",
                severity=None,
                timestamp=loc.timestamp,
                message="Speed exceeded posted limit",
            )
        )

    return alerts[:limit]
