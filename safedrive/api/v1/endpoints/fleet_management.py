from datetime import datetime
import io
import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from safedrive.core.security import (
    ApiClientContext,
    Role,
    ensure_dataset_access,
    ensure_driver_access,
    require_roles,
)
from safedrive.database.db import get_db
from safedrive.models.alcohol_questionnaire import AlcoholQuestionnaire
from safedrive.models.driver_profile import DriverProfile
from safedrive.models.fleet import (
    Fleet,
    VehicleGroup,
    DriverFleetAssignment,
    DriverTripEvent,
)
from safedrive.models.driving_tip import DrivingTip
from safedrive.models.location import Location
from safedrive.models.nlg_report import NLGReport
from safedrive.models.raw_sensor_data import RawSensorData
from safedrive.models.trip import Trip
from safedrive.models.unsafe_behaviour import UnsafeBehaviour
from safedrive.schemas import fleet as fleet_schemas

router = APIRouter()


def _ensure_driver_exists(db: Session, driver_id: UUID) -> DriverProfile:
    driver = (
        db.query(DriverProfile)
        .filter(DriverProfile.driverProfileId == driver_id)
        .first()
    )
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver


def _ensure_fleet_access(client: ApiClientContext, fleet_id: UUID) -> None:
    if client.role == Role.ADMIN:
        return
    if client.role == Role.FLEET_MANAGER and client.fleet_id == fleet_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Fleet access denied.",
    )


def _ensure_vehicle_group_access(
    db: Session,
    client: ApiClientContext,
    group_id: UUID,
) -> VehicleGroup:
    group = db.query(VehicleGroup).filter(VehicleGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle group not found",
        )
    _ensure_fleet_access(client, group.fleet_id)
    return group


@router.post(
    "/fleet/",
    response_model=fleet_schemas.FleetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fleet(
    payload: fleet_schemas.FleetCreate,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(require_roles(Role.ADMIN)),
):
    fleet = Fleet(
        name=payload.name,
        description=payload.description,
        region=payload.region,
    )
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    return fleet


@router.get(
    "/fleet/",
    response_model=List[fleet_schemas.FleetResponse],
    status_code=status.HTTP_200_OK,
)
def list_fleets(
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    query = db.query(Fleet)
    if current_client.role == Role.FLEET_MANAGER:
        if not current_client.fleet_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fleet scope missing for this API key.",
            )
        query = query.filter(Fleet.id == current_client.fleet_id)
    fleets = query.order_by(Fleet.created_at.desc()).all()
    return fleets


@router.get(
    "/fleet/{fleet_id}",
    response_model=fleet_schemas.FleetResponse,
    status_code=status.HTTP_200_OK,
)
def get_fleet(
    fleet_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    _ensure_fleet_access(current_client, fleet_id)
    fleet = db.query(Fleet).filter(Fleet.id == fleet_id).first()
    if not fleet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet not found")
    return fleet


@router.patch(
    "/fleet/{fleet_id}",
    response_model=fleet_schemas.FleetResponse,
    status_code=status.HTTP_200_OK,
)
def update_fleet(
    fleet_id: UUID,
    payload: fleet_schemas.FleetUpdate,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(require_roles(Role.ADMIN)),
):
    fleet = db.query(Fleet).filter(Fleet.id == fleet_id).first()
    if not fleet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(fleet, key, value)
    db.commit()
    db.refresh(fleet)
    return fleet


@router.delete(
    "/fleet/{fleet_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_fleet(
    fleet_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(require_roles(Role.ADMIN)),
) -> None:
    fleet = db.query(Fleet).filter(Fleet.id == fleet_id).first()
    if not fleet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet not found")
    db.delete(fleet)
    db.commit()


@router.post(
    "/fleet/{fleet_id}/vehicle-groups",
    response_model=fleet_schemas.VehicleGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vehicle_group(
    fleet_id: UUID,
    payload: fleet_schemas.VehicleGroupCreate,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    _ensure_fleet_access(current_client, fleet_id)
    fleet = db.query(Fleet).filter(Fleet.id == fleet_id).first()
    if not fleet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet not found")
    if payload.fleet_id and payload.fleet_id != fleet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload fleet_id does not match path fleet_id.",
        )
    group = VehicleGroup(
        name=payload.name,
        description=payload.description,
        fleet_id=fleet_id,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.get(
    "/fleet/{fleet_id}/vehicle-groups",
    response_model=List[fleet_schemas.VehicleGroupResponse],
    status_code=status.HTTP_200_OK,
)
def list_vehicle_groups(
    fleet_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    _ensure_fleet_access(current_client, fleet_id)
    groups = (
        db.query(VehicleGroup)
        .filter(VehicleGroup.fleet_id == fleet_id)
        .order_by(VehicleGroup.created_at.desc())
        .all()
    )
    return groups


@router.get(
    "/fleet/vehicle-groups/{group_id}",
    response_model=fleet_schemas.VehicleGroupResponse,
    status_code=status.HTTP_200_OK,
)
def get_vehicle_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    return _ensure_vehicle_group_access(db, current_client, group_id)


@router.patch(
    "/fleet/vehicle-groups/{group_id}",
    response_model=fleet_schemas.VehicleGroupResponse,
    status_code=status.HTTP_200_OK,
)
def update_vehicle_group(
    group_id: UUID,
    payload: fleet_schemas.VehicleGroupUpdate,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    group = _ensure_vehicle_group_access(db, current_client, group_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(group, key, value)
    db.commit()
    db.refresh(group)
    return group


@router.delete(
    "/fleet/vehicle-groups/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_vehicle_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
) -> None:
    group = _ensure_vehicle_group_access(db, current_client, group_id)
    db.delete(group)
    db.commit()


@router.post(
    "/fleet/assignments/",
    response_model=fleet_schemas.DriverFleetAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_driver_assignment(
    payload: fleet_schemas.DriverFleetAssignmentCreate,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    ensure_dataset_access(db, current_client, "fleet_assignments")
    if (
        current_client.role == Role.FLEET_MANAGER
        and current_client.fleet_id
        and payload.fleet_id != current_client.fleet_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fleet access denied for this assignment.",
        )
    _ensure_driver_exists(db, payload.driverProfileId)

    fleet = db.query(Fleet).filter(Fleet.id == payload.fleet_id).first()
    if not fleet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet not found")

    vehicle_group = None
    if payload.vehicle_group_id:
        vehicle_group = (
            db.query(VehicleGroup)
            .filter(
                VehicleGroup.id == payload.vehicle_group_id,
                VehicleGroup.fleet_id == payload.fleet_id,
            )
            .first()
        )
        if not vehicle_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle group not found for the requested fleet",
            )

    assignment = DriverFleetAssignment(
        driverProfileId=payload.driverProfileId,
        fleet_id=fleet.id,
        vehicle_group_id=vehicle_group.id if vehicle_group else None,
        onboarding_completed=payload.onboarding_completed,
        compliance_note=payload.compliance_note,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


@router.get(
    "/fleet/assignments/{driver_id}",
    response_model=fleet_schemas.DriverAssignmentWithCompliance,
    status_code=status.HTTP_200_OK,
)
def get_driver_assignment(
    driver_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    ensure_dataset_access(db, current_client, "fleet_assignments")
    ensure_driver_access(current_client, driver_id)
    _ensure_driver_exists(db, driver_id)

    assignment = (
        db.query(DriverFleetAssignment)
        .filter(DriverFleetAssignment.driverProfileId == driver_id)
        .order_by(DriverFleetAssignment.assigned_at.desc())
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    questionnaire = (
        db.query(AlcoholQuestionnaire)
        .filter(AlcoholQuestionnaire.driverProfileId == driver_id)
        .order_by(AlcoholQuestionnaire.date.desc())
        .first()
    )

    return {
        "assignment": assignment,
        "questionnaire": questionnaire,
    }


@router.post(
    "/fleet/events/",
    response_model=fleet_schemas.DriverTripEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def emit_driver_event(
    payload: fleet_schemas.DriverTripEventCreate,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    ensure_dataset_access(db, current_client, "fleet_events")
    ensure_driver_access(current_client, payload.driverProfileId)
    _ensure_driver_exists(db, payload.driverProfileId)

    event = DriverTripEvent(
        driverProfileId=payload.driverProfileId,
        trip_id=payload.trip_id,
        event_type=payload.event_type,
        message=payload.message,
        gps_health=payload.gps_health,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


@router.get(
    "/fleet/events/{driver_id}",
    response_model=fleet_schemas.DriverTripEventListResponse,
    status_code=status.HTTP_200_OK,
)
def list_driver_events(
    driver_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    ensure_dataset_access(db, current_client, "fleet_events")
    ensure_driver_access(current_client, driver_id)
    _ensure_driver_exists(db, driver_id)

    events = (
        db.query(DriverTripEvent)
        .filter(DriverTripEvent.driverProfileId == driver_id)
        .order_by(DriverTripEvent.timestamp.desc())
        .limit(limit)
        .all()
    )

    return {"events": events}


@router.get(
    "/fleet/trips/{trip_id}/context",
    response_model=fleet_schemas.TripContextResponse,
    status_code=status.HTTP_200_OK,
)
def get_trip_context(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    ensure_dataset_access(db, current_client, "fleet_trip_context")
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    driver_id = trip.driverProfileId
    ensure_driver_access(current_client, driver_id)
    _ensure_driver_exists(db, driver_id)

    tips = (
        db.query(DrivingTip)
        .filter(DrivingTip.profile_id == driver_id)
        .order_by(DrivingTip.date.desc())
        .limit(10)
        .all()
    )

    severity_findings = (
        db.query(UnsafeBehaviour)
        .filter(UnsafeBehaviour.trip_id == trip_id)
        .order_by(UnsafeBehaviour.severity.desc())
        .all()
    )

    nlg_reports = (
        db.query(NLGReport)
        .filter(NLGReport.driverProfileId == driver_id)
        .order_by(NLGReport.generated_at.desc())
        .limit(5)
        .all()
    )

    return {
        "trip_id": trip.id,
        "driverProfileId": driver_id,
        "tips": [
            {
                "tip_id": tip.tip_id,
                "title": tip.title,
                "summary_tip": tip.summary_tip,
                "llm": tip.llm,
                "date": tip.date,
            }
            for tip in tips
        ],
        "severity_findings": [
            {
                "id": behaviour.id,
                "behaviour_type": behaviour.behaviour_type,
                "severity": behaviour.severity,
                "timestamp": behaviour.timestamp,
            }
            for behaviour in severity_findings
        ],
        "nlg_reports": [
            {
                "id": report.id,
                "report_text": report.report_text,
                "generated_at": report.generated_at,
            }
            for report in nlg_reports
        ],
    }


@router.get(
    "/fleet/reports/{driver_id}",
    response_model=fleet_schemas.FleetReportResponse,
    status_code=status.HTTP_200_OK,
)
def get_driver_report(
    driver_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    ensure_dataset_access(db, current_client, "fleet_reports")
    ensure_driver_access(current_client, driver_id)
    _ensure_driver_exists(db, driver_id)
    return _build_driver_report(db, driver_id)


@router.get(
    "/fleet/reports/{driver_id}/download",
    status_code=status.HTTP_200_OK,
)
def download_driver_report(
    driver_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    ensure_dataset_access(db, current_client, "fleet_reports")
    ensure_driver_access(current_client, driver_id)
    _ensure_driver_exists(db, driver_id)
    report_data = _build_driver_report(db, driver_id)
    payload = json.dumps(report_data, default=str).encode("utf-8")
    buffer = io.BytesIO(payload)
    headers = {
        "Content-Disposition": f'attachment; filename="fleet_report_{driver_id}.json"'
    }
    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers=headers,
    )


def _trip_locations(db: Session, trip_id: UUID) -> List[Location]:
    return (
        db.query(Location)
        .join(RawSensorData, RawSensorData.location_id == Location.id)
        .filter(RawSensorData.trip_id == trip_id)
        .all()
    )


def _build_trip_summary(trip: Trip, db: Session) -> dict:
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

    return {
        "trip_id": trip.id,
        "start_time": trip.start_time and datetime.fromtimestamp(trip.start_time / 1000),
        "end_time": trip.end_time and datetime.fromtimestamp(trip.end_time / 1000),
        "influence": trip.influence,
        "distance_km": distance / 1000.0,
        "unsafe_count": unsafe_count,
        "avg_severity": avg_severity,
        "speeding_events": speeding_events,
    }


def _build_driver_report(db: Session, driver_id: UUID) -> dict:
    trips = (
        db.query(Trip)
        .filter(Trip.driverProfileId == driver_id)
        .order_by(Trip.start_time.desc())
        .all()
    )

    trip_summaries = [_build_trip_summary(trip, db) for trip in trips]

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
