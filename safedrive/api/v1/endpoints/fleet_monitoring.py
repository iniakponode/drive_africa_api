from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from safedrive.core.security import ApiClientContext, Role, ensure_driver_access, require_roles
from safedrive.database.db import get_db
from safedrive.models.driver_profile import DriverProfile
from safedrive.models.location import Location
from safedrive.models.raw_sensor_data import RawSensorData
from safedrive.models.trip import Trip
from safedrive.models.unsafe_behaviour import UnsafeBehaviour

router = APIRouter()


@router.get("/fleet/driver_monitor/{driver_id}")
def driver_monitor(
    driver_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.FLEET_MANAGER)
    ),
):
    ensure_driver_access(current_client, driver_id)
    driver = (
        db.query(DriverProfile)
        .filter(DriverProfile.driverProfileId == driver_id)
        .first()
    )
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    active_trip = (
        db.query(Trip)
        .filter(
            Trip.driverProfileId == driver.driverProfileId,
            Trip.end_date.is_(None),
        )
        .order_by(Trip.start_time.desc())
        .first()
    )

    behaviours = (
        db.query(UnsafeBehaviour)
        .filter(UnsafeBehaviour.driverProfileId == driver.driverProfileId)
        .all()
    )

    now_ms = int(datetime.utcnow().timestamp() * 1000)
    last_24h_ms = now_ms - (24 * 60 * 60 * 1000)
    unsafe_behaviour_last_24h = sum(
        1 for b in behaviours if b.timestamp >= last_24h_ms
    )

    location_records = (
        db.query(Location)
        .join(RawSensorData, RawSensorData.location_id == Location.id)
        .join(Trip, RawSensorData.trip_id == Trip.id)
        .filter(Trip.driverProfileId == driver.driverProfileId)
        .all()
    )

    total_locations = len(location_records)
    speeding_count = sum(
        1 for loc in location_records if loc.speed > (loc.speedLimit or float("inf"))
    )
    compliant_count = total_locations - speeding_count
    speed_compliance_ratio = (
        compliant_count / total_locations if total_locations else 1.0
    )

    payload = {
        "driverProfileId": str(driver.driverProfileId),
        "activeTripStatus": "ACTIVE" if active_trip else "IDLE",
        "unsafeBehaviourCount": len(behaviours),
        "unsafeBehaviourLast24h": unsafe_behaviour_last_24h,
        "speedComplianceRatio": speed_compliance_ratio,
        "speedingCount": speeding_count,
        "recentUnsafeBehaviours": [
            {
                "id": str(item.id),
                "behaviour_type": item.behaviour_type,
                "severity": item.severity,
                "timestamp": item.timestamp,
            }
            for item in sorted(behaviours, key=lambda x: x.timestamp, reverse=True)
        ],
    }

    return payload
