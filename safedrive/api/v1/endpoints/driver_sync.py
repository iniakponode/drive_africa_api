from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from safedrive.core.security import (
    ApiClientContext,
    Role,
    ensure_driver_access,
    require_roles_or_jwt,
)
from safedrive.crud.driver_profile import driver_profile_crud
from safedrive.crud.raw_sensor_data import raw_sensor_data_crud
from safedrive.crud.trip import trip_crud
from safedrive.crud.unsafe_behaviour import unsafe_behaviour_crud
from safedrive.database.db import get_db
from safedrive.schemas.driver_sync import (
    DriverSyncPayload,
    DriverSyncResponse,
)
from safedrive.schemas.raw_sensor_data import RawSensorDataCreate
from safedrive.schemas.trip import TripCreate
from safedrive.schemas.unsafe_behaviour import UnsafeBehaviourCreate

router = APIRouter()
logger = logging.getLogger(__name__)


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        cleaned = value.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def _epoch_ms_to_datetime(value: int) -> datetime:
    return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)


@router.post("/driver/sync", response_model=DriverSyncResponse)
def sync_driver_data(
    payload: DriverSyncPayload,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(Role.ADMIN, Role.DRIVER)
    ),
) -> DriverSyncResponse:
    driver_profile_id = payload.profile.driverProfileId
    if not driver_profile_id:
        profile = driver_profile_crud.get_by_email(db, payload.profile.email)
        if profile:
            driver_profile_id = profile.id_uuid
        else:
            raise HTTPException(
                status_code=400,
                detail="Driver profile ID is required for sync.",
            )

    ensure_driver_access(current_client, driver_profile_id)

    trip_creates: List[TripCreate] = []
    for trip in payload.trips:
        try:
            start_time = _epoch_ms_to_datetime(trip.start_time)
            trip_data = {
                "id": trip.id,
                "driverProfileId": driver_profile_id,
                "startTime": start_time.isoformat(),
                "end_time": trip.end_time,
                "start_date": _parse_iso_datetime(trip.start_date),
                "end_date": _parse_iso_datetime(trip.end_date),
                "influence": trip.influence,
                "tripNotes": trip.notes,
                "sync": trip.sync if trip.sync is not None else True,
            }
            trip_creates.append(TripCreate.model_validate(trip_data))
        except Exception as exc:
            logger.warning("Skipping trip %s during driver sync: %s", trip.id, exc)

    trip_count = 0
    if trip_creates:
        created_trips = trip_crud.batch_create(db=db, objs_in=trip_creates)
        trip_count = len(created_trips)

    raw_creates: List[RawSensorDataCreate] = []
    for raw in payload.rawSensorData:
        try:
            raw_data = {
                "id": raw.id,
                "sensor_type": raw.sensor_type,
                "sensor_type_name": raw.sensor_type_name,
                "values": raw.values,
                "timestamp": raw.timestamp,
                "date": raw.date,
                "accuracy": raw.accuracy,
                "location_id": raw.location_id,
                "trip_id": raw.trip_id,
                "sync": raw.sync if raw.sync is not None else True,
            }
            raw_creates.append(RawSensorDataCreate.model_validate(raw_data))
        except Exception as exc:
            logger.warning("Skipping raw sensor data %s during driver sync: %s", raw.id, exc)

    raw_sensor_count = 0
    if raw_creates:
        created_raw = raw_sensor_data_crud.batch_create(db=db, data_in=raw_creates)
        raw_sensor_count = len(created_raw)

    unsafe_creates: List[UnsafeBehaviourCreate] = []
    for behaviour in payload.unsafeBehaviours:
        if behaviour.trip_id is None:
            logger.warning("Skipping unsafe behaviour %s without trip_id.", behaviour.id)
            continue
        try:
            behaviour_data = {
                "id": behaviour.id,
                "trip_id": behaviour.trip_id,
                "location_id": behaviour.location_id,
                "driverProfileId": driver_profile_id,
                "behaviour_type": behaviour.behaviour_type,
                "severity": behaviour.severity,
                "timestamp": behaviour.timestamp,
                "date": behaviour.date,
                "sync": behaviour.sync if behaviour.sync is not None else True,
            }
            unsafe_creates.append(UnsafeBehaviourCreate.model_validate(behaviour_data))
        except Exception as exc:
            logger.warning("Skipping unsafe behaviour %s during driver sync: %s", behaviour.id, exc)

    unsafe_behaviour_count = 0
    if unsafe_creates:
        created_unsafe = unsafe_behaviour_crud.batch_create(db=db, data_in=unsafe_creates)
        unsafe_behaviour_count = len(created_unsafe)

    return DriverSyncResponse(
        tripCount=trip_count,
        rawSensorCount=raw_sensor_count,
        unsafeBehaviourCount=unsafe_behaviour_count,
        alcoholResponseCount=0,
        driverProfileId=driver_profile_id,
    )
