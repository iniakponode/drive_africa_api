from datetime import datetime, timedelta
import csv
import io
import json
from typing import Iterable, List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from safedrive.core.security import (
    ApiClientContext,
    Role,
    ensure_dataset_access,
    require_roles,
)
from safedrive.database.db import get_db
from safedrive.models.alcohol_questionnaire import AlcoholQuestionnaire
from safedrive.models.driver_profile import DriverProfile
from safedrive.models.driving_tip import DrivingTip
from safedrive.models.location import Location
from safedrive.models.nlg_report import NLGReport
from safedrive.models.raw_sensor_data import RawSensorData
from safedrive.models.trip import Trip
from safedrive.models.unsafe_behaviour import UnsafeBehaviour
from safedrive.schemas.alcohol_questionnaire import AlcoholQuestionnaireResponseSchema
from safedrive.schemas.behaviour_metrics import DriverUBPK, TripUBPK
from safedrive.schemas.researcher import (
    AggregatedSnapshotResponse,
    IngestionStatusItem,
    IngestionStatusResponse,
    RawSensorSummary,
    ResearcherTripAlcoholBundle,
    ResearcherTripMetadata,
    UnsafeBehaviourSummary,
)

router = APIRouter()

MATCHING_RULE = "Same UTC calendar day"
MATCHING_TIMEZONE = "UTC"


def _parse_week(week: str) -> tuple[datetime, datetime]:
    try:
        year_part, week_part = week.split("-W")
        year = int(year_part)
        week_num = int(week_part)
        week_start = datetime.fromisocalendar(year, week_num, 1)
        week_end = week_start + timedelta(days=7)
        return week_start, week_end
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid week format. Use YYYY-Www.",
        ) from exc


def _apply_date_filters(query, column, start_date, end_date, week):
    if week:
        week_start, week_end = _parse_week(week)
        query = query.filter(column >= week_start, column < week_end)
    if start_date:
        query = query.filter(column >= start_date)
    if end_date:
        query = query.filter(column <= end_date)
    return query


def _apply_report_period_filters(
    query,
    start_column,
    end_column,
    start_date,
    end_date,
    week,
):
    if week:
        week_start, week_end = _parse_week(week)
        query = query.filter(start_column <= week_end, end_column >= week_start)
    if start_date:
        query = query.filter(start_column >= start_date)
    if end_date:
        query = query.filter(end_column <= end_date)
    return query


def _trip_day_utc(trip: Trip):
    if trip.start_date:
        return trip.start_date.date()
    if trip.start_time:
        return datetime.utcfromtimestamp(trip.start_time / 1000.0).date()
    return None


def _build_questionnaire_lookup(
    questionnaires: List[AlcoholQuestionnaire],
) -> dict:
    lookup: dict = {}
    for questionnaire in questionnaires:
        if not questionnaire.date:
            continue
        day = questionnaire.date.date()
        driver_id = questionnaire.driverProfileId
        lookup.setdefault(driver_id, {})
        existing = lookup[driver_id].get(day)
        if not existing or (
            existing.date is None or questionnaire.date > existing.date
        ):
            lookup[driver_id][day] = questionnaire
    return lookup


def _match_questionnaire(
    lookup: dict,
    driver_id: UUID,
    trip_day,
) -> Optional[AlcoholQuestionnaire]:
    if trip_day is None:
        return None
    return lookup.get(driver_id, {}).get(trip_day)


def _parse_export_format(export_format: str) -> str:
    value = (export_format or "").lower()
    if value not in {"jsonl", "csv"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Supported values are 'jsonl' and 'csv'.",
        )
    return value


def _unsafe_behaviour_summary(
    db: Session,
    driver_profile_id: Optional[UUID] = None,
    trip_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    week: Optional[str] = None,
    min_severity: Optional[float] = None,
    max_severity: Optional[float] = None,
) -> List[UnsafeBehaviourSummary]:
    query = db.query(
        UnsafeBehaviour.behaviour_type.label("behaviour_type"),
        func.count(UnsafeBehaviour.id).label("total"),
        func.avg(UnsafeBehaviour.severity).label("avg_severity"),
        func.min(UnsafeBehaviour.severity).label("min_severity"),
        func.max(UnsafeBehaviour.severity).label("max_severity"),
    )
    if driver_profile_id:
        query = query.filter(UnsafeBehaviour.driverProfileId == driver_profile_id)
    if trip_id:
        query = query.filter(UnsafeBehaviour.trip_id == trip_id)
    if min_severity is not None:
        query = query.filter(UnsafeBehaviour.severity >= min_severity)
    if max_severity is not None:
        query = query.filter(UnsafeBehaviour.severity <= max_severity)
    query = _apply_date_filters(
        query, UnsafeBehaviour.date, start_date, end_date, week
    )
    query = query.group_by(UnsafeBehaviour.behaviour_type)

    results = []
    for row in query.all():
        results.append(
            UnsafeBehaviourSummary(
                behaviour_type=row.behaviour_type,
                total=int(row.total or 0),
                avg_severity=float(row.avg_severity or 0.0),
                min_severity=float(row.min_severity or 0.0),
                max_severity=float(row.max_severity or 0.0),
            )
        )
    return results


def _raw_sensor_summary(
    db: Session,
    driver_profile_id: Optional[UUID] = None,
    trip_id: Optional[UUID] = None,
    sensor_type: Optional[int] = None,
    sensor_type_name: Optional[str] = None,
    start_timestamp: Optional[int] = None,
    end_timestamp: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    week: Optional[str] = None,
) -> List[RawSensorSummary]:
    query = db.query(
        RawSensorData.sensor_type.label("sensor_type"),
        RawSensorData.sensor_type_name.label("sensor_type_name"),
        func.count(RawSensorData.id).label("total"),
        func.min(RawSensorData.timestamp).label("min_timestamp"),
        func.max(RawSensorData.timestamp).label("max_timestamp"),
        func.avg(RawSensorData.accuracy).label("avg_accuracy"),
    )
    if driver_profile_id:
        query = query.join(Trip, RawSensorData.trip_id == Trip.id).filter(
            Trip.driverProfileId == driver_profile_id
        )
    if trip_id:
        query = query.filter(RawSensorData.trip_id == trip_id)
    if sensor_type is not None:
        query = query.filter(RawSensorData.sensor_type == sensor_type)
    if sensor_type_name:
        query = query.filter(RawSensorData.sensor_type_name == sensor_type_name)
    if start_timestamp is not None:
        query = query.filter(RawSensorData.timestamp >= start_timestamp)
    if end_timestamp is not None:
        query = query.filter(RawSensorData.timestamp <= end_timestamp)
    query = _apply_date_filters(
        query, RawSensorData.date, start_date, end_date, week
    )

    query = query.group_by(RawSensorData.sensor_type, RawSensorData.sensor_type_name)

    results = []
    for row in query.all():
        results.append(
            RawSensorSummary(
                sensor_type=int(row.sensor_type),
                sensor_type_name=row.sensor_type_name,
                total=int(row.total or 0),
                min_timestamp=row.min_timestamp,
                max_timestamp=row.max_timestamp,
                avg_accuracy=float(row.avg_accuracy or 0.0),
            )
        )
    return results


def _trip_distances(
    db: Session,
    driver_profile_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    week: Optional[str] = None,
) -> dict:
    query = (
        db.query(
            Trip.id,
            Trip.driverProfileId,
            func.coalesce(func.sum(Location.distance), 0.0),
            Trip.start_date,
        )
        .outerjoin(RawSensorData, RawSensorData.trip_id == Trip.id)
        .outerjoin(Location, Location.id == RawSensorData.location_id)
        .group_by(Trip.id)
    )
    if driver_profile_id:
        query = query.filter(Trip.driverProfileId == driver_profile_id)
    query = _apply_date_filters(query, Trip.start_date, start_date, end_date, week)

    results = query.all()
    return {r[0]: (r[1], float(r[2] or 0.0), r[3]) for r in results}


def _trip_behaviour_counts(
    db: Session,
    trip_ids: Optional[Iterable[UUID]] = None,
    driver_profile_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    week: Optional[str] = None,
) -> dict:
    query = db.query(UnsafeBehaviour.trip_id, func.count(UnsafeBehaviour.id))
    if trip_ids:
        query = query.filter(UnsafeBehaviour.trip_id.in_(list(trip_ids)))
    if driver_profile_id:
        query = query.filter(UnsafeBehaviour.driverProfileId == driver_profile_id)
    query = _apply_date_filters(
        query, UnsafeBehaviour.date, start_date, end_date, week
    )
    query = query.group_by(UnsafeBehaviour.trip_id)
    return {r[0]: int(r[1]) for r in query.all()}


def _ubpk_snapshot(
    db: Session,
    driver_profile_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    week: Optional[str] = None,
) -> Tuple[List[DriverUBPK], List[TripUBPK]]:
    distances = _trip_distances(
        db,
        driver_profile_id=driver_profile_id,
        start_date=start_date,
        end_date=end_date,
        week=week,
    )
    behaviours = _trip_behaviour_counts(
        db,
        trip_ids=distances.keys(),
        driver_profile_id=driver_profile_id,
        start_date=start_date,
        end_date=end_date,
        week=week,
    )

    per_driver = {}
    per_trip: List[TripUBPK] = []

    for trip_id, (driver_id, distance_m, _) in distances.items():
        count = behaviours.get(trip_id, 0)
        ubpk = (count / (distance_m / 1000)) if distance_m > 0 else 0.0
        per_trip.append(
            TripUBPK(trip_id=trip_id, driverProfileId=driver_id, ubpk=ubpk)
        )
        per_driver.setdefault(driver_id, [0, 0.0])
        per_driver[driver_id][0] += count
        per_driver[driver_id][1] += distance_m

    per_driver_results: List[DriverUBPK] = []
    for driver_id, (count, distance_m) in per_driver.items():
        ubpk = (count / (distance_m / 1000)) if distance_m > 0 else 0.0
        per_driver_results.append(DriverUBPK(driverProfileId=driver_id, ubpk=ubpk))

    return per_driver_results, per_trip


def _latest_from_ms(value: Optional[int]) -> Optional[datetime]:
    if value is None:
        return None
    return datetime.utcfromtimestamp(value / 1000.0)


def _sync_counts(
    db: Session,
    count_field,
    sync_field,
) -> Tuple[int, int, int]:
    total = int(db.query(func.count(count_field)).scalar() or 0)
    synced = int(
        db.query(func.sum(case((sync_field.is_(True), 1), else_=0))).scalar() or 0
    )
    return total, synced, total - synced


def _stream_csv(header: List[str], rows: Iterable[List[str]]) -> Iterable[str]:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    yield output.getvalue()
    output.seek(0)
    output.truncate(0)
    for row in rows:
        writer.writerow(row)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)


@router.get(
    "/researcher/unsafe_behaviours/summary",
    response_model=List[UnsafeBehaviourSummary],
)
def get_unsafe_behaviour_summary(
    driver_profile_id: Optional[UUID] = Query(None, alias="driverProfileId"),
    trip_id: Optional[UUID] = Query(None, alias="tripId"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    week: Optional[str] = Query(None),
    min_severity: Optional[float] = Query(None, alias="minSeverity"),
    max_severity: Optional[float] = Query(None, alias="maxSeverity"),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.RESEARCHER)
    ),
) -> List[UnsafeBehaviourSummary]:
    ensure_dataset_access(db, current_client, "researcher_unsafe_behaviours")
    return _unsafe_behaviour_summary(
        db,
        driver_profile_id=driver_profile_id,
        trip_id=trip_id,
        start_date=start_date,
        end_date=end_date,
        week=week,
        min_severity=min_severity,
        max_severity=max_severity,
    )


@router.get(
    "/researcher/raw_sensor_data/summary",
    response_model=List[RawSensorSummary],
)
def get_raw_sensor_summary(
    driver_profile_id: Optional[UUID] = Query(None, alias="driverProfileId"),
    trip_id: Optional[UUID] = Query(None, alias="tripId"),
    sensor_type: Optional[int] = Query(None, alias="sensorType"),
    sensor_type_name: Optional[str] = Query(None, alias="sensorTypeName"),
    start_timestamp: Optional[int] = Query(None, alias="startTimestamp"),
    end_timestamp: Optional[int] = Query(None, alias="endTimestamp"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    week: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.RESEARCHER)
    ),
) -> List[RawSensorSummary]:
    ensure_dataset_access(db, current_client, "researcher_raw_sensor_data")
    return _raw_sensor_summary(
        db,
        driver_profile_id=driver_profile_id,
        trip_id=trip_id,
        sensor_type=sensor_type,
        sensor_type_name=sensor_type_name,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        start_date=start_date,
        end_date=end_date,
        week=week,
    )


@router.get(
    "/researcher/alcohol_trip_bundle",
    response_model=ResearcherTripAlcoholBundle,
)
def get_alcohol_trip_bundle(
    driver_profile_id: Optional[UUID] = Query(None, alias="driverProfileId"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    week: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 5000,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.RESEARCHER)
    ),
) -> ResearcherTripAlcoholBundle:
    ensure_dataset_access(db, current_client, "researcher_alcohol_trip_bundle")
    trips_query = db.query(Trip)
    if driver_profile_id:
        trips_query = trips_query.filter(Trip.driverProfileId == driver_profile_id)
    trips_query = _apply_date_filters(
        trips_query, Trip.start_date, start_date, end_date, week
    )

    trips = (
        trips_query.order_by(Trip.start_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    questionnaire_query = db.query(AlcoholQuestionnaire)
    if driver_profile_id:
        questionnaire_query = questionnaire_query.filter(
            AlcoholQuestionnaire.driverProfileId == driver_profile_id
        )
    questionnaire_query = _apply_date_filters(
        questionnaire_query, AlcoholQuestionnaire.date, start_date, end_date, week
    )

    questionnaires = (
        questionnaire_query.order_by(AlcoholQuestionnaire.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    lookup = _build_questionnaire_lookup(questionnaires)
    trip_payloads: List[ResearcherTripMetadata] = []
    for trip in trips:
        trip_payload = ResearcherTripMetadata.model_validate(trip)
        match = _match_questionnaire(
            lookup, trip.driverProfileId, _trip_day_utc(trip)
        )
        if match:
            trip_payload.matched_questionnaire = (
                AlcoholQuestionnaireResponseSchema.model_validate(match)
            )
        trip_payloads.append(trip_payload)

    return ResearcherTripAlcoholBundle(
        driverProfileId=driver_profile_id,
        start_date=start_date,
        end_date=end_date,
        matching_rule=MATCHING_RULE,
        matching_timezone=MATCHING_TIMEZONE,
        total_trips=len(trips),
        total_questionnaires=len(questionnaires),
        trips=trip_payloads,
        questionnaires=[
            AlcoholQuestionnaireResponseSchema.model_validate(item)
            for item in questionnaires
        ],
    )


@router.get("/researcher/nlg_reports/export")
def export_nlg_reports(
    driver_profile_id: Optional[UUID] = Query(None, alias="driverProfileId"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    week: Optional[str] = Query(None),
    sync: Optional[bool] = Query(None),
    export_format: str = Query("jsonl", alias="format"),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.RESEARCHER)
    ),
):
    ensure_dataset_access(db, current_client, "researcher_nlg_reports")
    export_format = _parse_export_format(export_format)

    query = db.query(NLGReport)
    if driver_profile_id:
        query = query.filter(NLGReport.driverProfileId == driver_profile_id)
    query = _apply_report_period_filters(
        query,
        NLGReport.start_date,
        NLGReport.end_date,
        start_date,
        end_date,
        week,
    )
    if sync is not None:
        query = query.filter(NLGReport.sync == sync)

    query = query.order_by(NLGReport.generated_at.desc())

    def _record_payload(report: NLGReport) -> dict:
        return {
            "id": str(report.id),
            "driverProfileId": str(report.driverProfileId),
            "startDate": report.start_date,
            "endDate": report.end_date,
            "report_text": report.report_text,
            "generated_at": report.generated_at,
            "sync": report.sync,
        }

    filename = "nlg_reports"
    if driver_profile_id:
        filename = f"{filename}_{driver_profile_id}"

    if export_format == "csv":
        header = [
            "id",
            "driverProfileId",
            "startDate",
            "endDate",
            "report_text",
            "generated_at",
            "sync",
        ]

        def rows() -> Iterable[List[str]]:
            for report in query.yield_per(500):
                payload = _record_payload(report)
                yield [
                    payload["id"],
                    payload["driverProfileId"],
                    str(payload["startDate"]) if payload["startDate"] else "",
                    str(payload["endDate"]) if payload["endDate"] else "",
                    payload["report_text"],
                    str(payload["generated_at"]) if payload["generated_at"] else "",
                    str(payload["sync"]),
                ]

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}.csv"'
        }
        return StreamingResponse(
            _stream_csv(header, rows()),
            media_type="text/csv",
            headers=headers,
        )

    def jsonl_rows() -> Iterable[bytes]:
        for report in query.yield_per(500):
            payload = _record_payload(report)
            yield (json.dumps(payload, default=str) + "\n").encode("utf-8")

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}.jsonl"'
    }
    return StreamingResponse(
        jsonl_rows(),
        media_type="application/x-ndjson",
        headers=headers,
    )


@router.get("/researcher/raw_sensor_data/export")
def export_raw_sensor_data(
    driver_profile_id: Optional[UUID] = Query(None, alias="driverProfileId"),
    trip_id: Optional[UUID] = Query(None, alias="tripId"),
    sensor_type: Optional[int] = Query(None, alias="sensorType"),
    sensor_type_name: Optional[str] = Query(None, alias="sensorTypeName"),
    start_timestamp: Optional[int] = Query(None, alias="startTimestamp"),
    end_timestamp: Optional[int] = Query(None, alias="endTimestamp"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    week: Optional[str] = Query(None),
    export_format: str = Query("jsonl", alias="format"),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.RESEARCHER)
    ),
):
    ensure_dataset_access(db, current_client, "researcher_raw_sensor_export")
    export_format = _parse_export_format(export_format)

    query = db.query(RawSensorData, Trip.driverProfileId).outerjoin(
        Trip, RawSensorData.trip_id == Trip.id
    )
    if driver_profile_id:
        query = query.filter(Trip.driverProfileId == driver_profile_id)
    if trip_id:
        query = query.filter(RawSensorData.trip_id == trip_id)
    if sensor_type is not None:
        query = query.filter(RawSensorData.sensor_type == sensor_type)
    if sensor_type_name:
        query = query.filter(RawSensorData.sensor_type_name == sensor_type_name)
    if start_timestamp is not None:
        query = query.filter(RawSensorData.timestamp >= start_timestamp)
    if end_timestamp is not None:
        query = query.filter(RawSensorData.timestamp <= end_timestamp)
    query = _apply_date_filters(
        query, RawSensorData.date, start_date, end_date, week
    )

    query = query.order_by(RawSensorData.timestamp.asc())

    def _record_payload(row: Tuple[RawSensorData, Optional[UUID]]) -> dict:
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

    filename = "raw_sensor_data"
    if driver_profile_id:
        filename = f"{filename}_{driver_profile_id}"

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

        def rows() -> Iterable[List[str]]:
            for raw, driver_id in query.yield_per(500):
                payload = _record_payload((raw, driver_id))
                yield [
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

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}.csv"'
        }
        return StreamingResponse(
            _stream_csv(header, rows()),
            media_type="text/csv",
            headers=headers,
        )

    def jsonl_rows() -> Iterable[bytes]:
        for raw, driver_id in query.yield_per(500):
            payload = _record_payload((raw, driver_id))
            yield (json.dumps(payload, default=str) + "\n").encode("utf-8")

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}.jsonl"'
    }
    return StreamingResponse(
        jsonl_rows(),
        media_type="application/x-ndjson",
        headers=headers,
    )


@router.get("/researcher/trips/export")
def export_trips(
    driver_profile_id: Optional[UUID] = Query(None, alias="driverProfileId"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    week: Optional[str] = Query(None),
    export_format: str = Query("jsonl", alias="format"),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.RESEARCHER)
    ),
):
    ensure_dataset_access(db, current_client, "researcher_trips_export")
    export_format = _parse_export_format(export_format)

    trips_query = db.query(Trip)
    if driver_profile_id:
        trips_query = trips_query.filter(Trip.driverProfileId == driver_profile_id)
    trips_query = _apply_date_filters(
        trips_query, Trip.start_date, start_date, end_date, week
    )
    trips_query = trips_query.order_by(Trip.start_date.desc())

    questionnaires_query = db.query(AlcoholQuestionnaire)
    if driver_profile_id:
        questionnaires_query = questionnaires_query.filter(
            AlcoholQuestionnaire.driverProfileId == driver_profile_id
        )
    questionnaires_query = _apply_date_filters(
        questionnaires_query, AlcoholQuestionnaire.date, start_date, end_date, week
    )

    lookup = _build_questionnaire_lookup(questionnaires_query.all())

    def _trip_payload(trip: Trip) -> dict:
        match = _match_questionnaire(
            lookup, trip.driverProfileId, _trip_day_utc(trip)
        )
        questionnaire_payload = (
            AlcoholQuestionnaireResponseSchema.model_validate(match).model_dump()
            if match
            else None
        )
        return {
            "id": str(trip.id),
            "driverProfileId": str(trip.driverProfileId),
            "startDate": trip.start_date,
            "endDate": trip.end_date,
            "startTime": trip.start_time,
            "endTime": trip.end_time,
            "influence": trip.influence,
            "tripNotes": trip.trip_notes,
            "alcoholProbability": trip.alcohol_probability,
            "userAlcoholResponse": trip.user_alcohol_response,
            "sync": trip.sync,
            "matchedQuestionnaire": questionnaire_payload,
            "matchingRule": MATCHING_RULE,
            "matchingTimezone": MATCHING_TIMEZONE,
        }

    filename = "trips"
    if driver_profile_id:
        filename = f"{filename}_{driver_profile_id}"

    if export_format == "csv":
        header = [
            "id",
            "driverProfileId",
            "startDate",
            "endDate",
            "startTime",
            "endTime",
            "influence",
            "tripNotes",
            "alcoholProbability",
            "userAlcoholResponse",
            "sync",
            "matchedQuestionnaire",
            "matchingRule",
            "matchingTimezone",
        ]

        def rows() -> Iterable[List[str]]:
            for trip in trips_query.yield_per(200):
                payload = _trip_payload(trip)
                yield [
                    payload["id"],
                    payload["driverProfileId"],
                    str(payload["startDate"]) if payload["startDate"] else "",
                    str(payload["endDate"]) if payload["endDate"] else "",
                    str(payload["startTime"]) if payload["startTime"] else "",
                    str(payload["endTime"]) if payload["endTime"] else "",
                    payload["influence"] or "",
                    payload["tripNotes"] or "",
                    str(payload["alcoholProbability"])
                    if payload["alcoholProbability"] is not None
                    else "",
                    payload["userAlcoholResponse"] or "",
                    str(payload["sync"]),
                    json.dumps(payload["matchedQuestionnaire"], default=str)
                    if payload["matchedQuestionnaire"]
                    else "",
                    payload["matchingRule"],
                    payload["matchingTimezone"],
                ]

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}.csv"'
        }
        return StreamingResponse(
            _stream_csv(header, rows()),
            media_type="text/csv",
            headers=headers,
        )

    def jsonl_rows() -> Iterable[bytes]:
        for trip in trips_query.yield_per(200):
            payload = _trip_payload(trip)
            yield (json.dumps(payload, default=str) + "\n").encode("utf-8")

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}.jsonl"'
    }
    return StreamingResponse(
        jsonl_rows(),
        media_type="application/x-ndjson",
        headers=headers,
    )


@router.get(
    "/researcher/snapshots/aggregate",
    response_model=AggregatedSnapshotResponse,
)
def get_aggregate_snapshot(
    driver_profile_id: Optional[UUID] = Query(None, alias="driverProfileId"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    week: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.RESEARCHER)
    ),
) -> AggregatedSnapshotResponse:
    ensure_dataset_access(db, current_client, "researcher_aggregate_snapshot")
    ubpk_per_driver, ubpk_per_trip = _ubpk_snapshot(
        db,
        driver_profile_id=driver_profile_id,
        start_date=start_date,
        end_date=end_date,
        week=week,
    )
    return AggregatedSnapshotResponse(
        generated_at=datetime.utcnow(),
        ubpk_per_driver=ubpk_per_driver,
        ubpk_per_trip=ubpk_per_trip,
        unsafe_behaviour_summary=_unsafe_behaviour_summary(
            db,
            driver_profile_id=driver_profile_id,
            start_date=start_date,
            end_date=end_date,
            week=week,
        ),
        raw_sensor_summary=_raw_sensor_summary(
            db,
            driver_profile_id=driver_profile_id,
            start_date=start_date,
            end_date=end_date,
            week=week,
        ),
    )


@router.get("/researcher/snapshots/aggregate/download")
def download_aggregate_snapshot(
    driver_profile_id: Optional[UUID] = Query(None, alias="driverProfileId"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    week: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.RESEARCHER)
    ),
):
    ensure_dataset_access(db, current_client, "researcher_aggregate_snapshot")
    payload = get_aggregate_snapshot(
        driver_profile_id=driver_profile_id,
        start_date=start_date,
        end_date=end_date,
        week=week,
        db=db,
        current_client=current_client,
    )
    buffer = io.BytesIO(json.dumps(payload.model_dump(), default=str).encode("utf-8"))
    headers = {
        "Content-Disposition": 'attachment; filename="researcher_aggregate_snapshot.json"'
    }
    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers=headers,
    )


@router.post("/researcher/trips/backfill_alcohol")
def backfill_trip_alcohol(
    driver_profile_id: Optional[UUID] = Query(None, alias="driverProfileId"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    week: Optional[str] = Query(None),
    overwrite: bool = Query(False),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.RESEARCHER)
    ),
):
    ensure_dataset_access(db, current_client, "researcher_trips_export")
    trips_query = db.query(Trip)
    if driver_profile_id:
        trips_query = trips_query.filter(Trip.driverProfileId == driver_profile_id)
    trips_query = _apply_date_filters(
        trips_query, Trip.start_date, start_date, end_date, week
    )
    trips = trips_query.all()

    questionnaires_query = db.query(AlcoholQuestionnaire)
    if driver_profile_id:
        questionnaires_query = questionnaires_query.filter(
            AlcoholQuestionnaire.driverProfileId == driver_profile_id
        )
    questionnaires_query = _apply_date_filters(
        questionnaires_query, AlcoholQuestionnaire.date, start_date, end_date, week
    )

    lookup = _build_questionnaire_lookup(questionnaires_query.all())

    matched = 0
    updated = 0
    skipped_no_date = 0

    for trip in trips:
        trip_day = _trip_day_utc(trip)
        if trip_day is None:
            skipped_no_date += 1
            continue
        match = _match_questionnaire(lookup, trip.driverProfileId, trip_day)
        if not match:
            continue
        matched += 1
        response_code = "1" if match.drankAlcohol else "0"
        probability = 1.0 if match.drankAlcohol else 0.0

        changed = False
        if overwrite or trip.user_alcohol_response in (None, ""):
            trip.user_alcohol_response = response_code
            changed = True
        if overwrite or trip.alcohol_probability is None:
            trip.alcohol_probability = probability
            changed = True
        if changed:
            updated += 1

    if updated:
        db.commit()

    return {
        "driverProfileId": str(driver_profile_id) if driver_profile_id else None,
        "matchingRule": MATCHING_RULE,
        "matchingTimezone": MATCHING_TIMEZONE,
        "totalTrips": len(trips),
        "matchedTrips": matched,
        "updatedTrips": updated,
        "skippedTripsNoDate": skipped_no_date,
        "overwrite": overwrite,
    }


@router.get(
    "/researcher/ingestion/status",
    response_model=IngestionStatusResponse,
)
def get_ingestion_status(
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.RESEARCHER)
    ),
) -> IngestionStatusResponse:
    ensure_dataset_access(db, current_client, "researcher_ingestion_status")
    datasets: List[IngestionStatusItem] = []

    total, synced, unsynced = _sync_counts(
        db, DriverProfile.driverProfileId, DriverProfile.sync
    )
    datasets.append(
        IngestionStatusItem(
            dataset="driver_profiles",
            total=total,
            synced=synced,
            unsynced=unsynced,
        )
    )

    total, synced, unsynced = _sync_counts(db, Trip.id, Trip.sync)
    latest_trip_date = db.query(func.max(Trip.start_date)).scalar()
    latest_trip_time = db.query(func.max(Trip.start_time)).scalar()
    datasets.append(
        IngestionStatusItem(
            dataset="trips",
            total=total,
            synced=synced,
            unsynced=unsynced,
            latest_record_at=latest_trip_date or _latest_from_ms(latest_trip_time),
        )
    )

    total, synced, unsynced = _sync_counts(db, RawSensorData.id, RawSensorData.sync)
    latest_raw_ts = db.query(func.max(RawSensorData.timestamp)).scalar()
    datasets.append(
        IngestionStatusItem(
            dataset="raw_sensor_data",
            total=total,
            synced=synced,
            unsynced=unsynced,
            latest_record_at=_latest_from_ms(latest_raw_ts),
        )
    )

    total, synced, unsynced = _sync_counts(
        db, UnsafeBehaviour.id, UnsafeBehaviour.sync
    )
    latest_unsafe_ts = db.query(func.max(UnsafeBehaviour.timestamp)).scalar()
    datasets.append(
        IngestionStatusItem(
            dataset="unsafe_behaviours",
            total=total,
            synced=synced,
            unsynced=unsynced,
            latest_record_at=_latest_from_ms(latest_unsafe_ts),
        )
    )

    total, synced, unsynced = _sync_counts(
        db, AlcoholQuestionnaire.id, AlcoholQuestionnaire.sync
    )
    latest_questionnaire = db.query(func.max(AlcoholQuestionnaire.date)).scalar()
    datasets.append(
        IngestionStatusItem(
            dataset="alcohol_questionnaires",
            total=total,
            synced=synced,
            unsynced=unsynced,
            latest_record_at=latest_questionnaire,
        )
    )

    total, synced, unsynced = _sync_counts(db, NLGReport.id, NLGReport.sync)
    latest_nlg = db.query(func.max(NLGReport.generated_at)).scalar()
    datasets.append(
        IngestionStatusItem(
            dataset="nlg_reports",
            total=total,
            synced=synced,
            unsynced=unsynced,
            latest_record_at=latest_nlg,
        )
    )

    total, synced, unsynced = _sync_counts(db, DrivingTip.tip_id, DrivingTip.sync)
    latest_tip = db.query(func.max(DrivingTip.date)).scalar()
    datasets.append(
        IngestionStatusItem(
            dataset="driving_tips",
            total=total,
            synced=synced,
            unsynced=unsynced,
            latest_record_at=latest_tip,
        )
    )

    return IngestionStatusResponse(generated_at=datetime.utcnow(), datasets=datasets)
