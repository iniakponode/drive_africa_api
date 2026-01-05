from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from safedrive.models.driver_profile import DriverProfile
from safedrive.models.location import Location
from safedrive.models.raw_sensor_data import RawSensorData
from safedrive.models.trip import Trip
from safedrive.models.unsafe_behaviour import UnsafeBehaviour
from tests.db_fixtures import (
    client,
    TestingSessionLocal,
    create_tables,
    drop_tables,
)


@pytest.fixture(autouse=True)
def prepare_database():
    create_tables()
    try:
        yield
    finally:
        drop_tables()


def _seed_driver_data(db):
    driver = DriverProfile(driverProfileId=uuid4(), email="fleet@example.com", sync=False)
    db.add(driver)
    db.flush()

    active_trip = Trip(
        id=uuid4(),
        driverProfileId=driver.driverProfileId,
        start_date=datetime.utcnow(),
        end_date=None,
        start_time=int(datetime.utcnow().timestamp() * 1000),
        end_time=None,
        influence="Vehicle",
        sync=True,
    )
    completed_trip = Trip(
        id=uuid4(),
        driverProfileId=driver.driverProfileId,
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow(),
        start_time=int((datetime.utcnow() - timedelta(days=1)).timestamp() * 1000),
        end_time=int(datetime.utcnow().timestamp() * 1000),
        influence="Idle",
        sync=True,
    )
    db.add_all([active_trip, completed_trip])
    db.flush()

    now_ms = int(datetime.utcnow().timestamp() * 1000)
    behaviour_recent = UnsafeBehaviour(
        id=uuid4(),
        trip_id=active_trip.id,
        driverProfileId=driver.driverProfileId,
        behaviour_type="hard_brake",
        severity=0.8,
        timestamp=now_ms,
        date=datetime.utcnow(),
        updated_at=None,
        updated=False,
        sync=False,
        alcohol_influence=False,
    )
    behaviour_old = UnsafeBehaviour(
        id=uuid4(),
        trip_id=completed_trip.id,
        driverProfileId=driver.driverProfileId,
        behaviour_type="speeding",
        severity=0.6,
        timestamp=now_ms - (48 * 60 * 60 * 1000),
        date=datetime.utcnow(),
        updated_at=None,
        updated=False,
        sync=False,
        alcohol_influence=False,
    )
    db.add_all([behaviour_recent, behaviour_old])
    db.flush()

    # Create two location records with one speeding event
    location_fast = Location(
        id=uuid4(),
        latitude=1.0,
        longitude=1.0,
        timestamp=now_ms,
        date=datetime.utcnow(),
        altitude=100.0,
        speed=25.0,
        speedLimit=20.0,
        distance=10.0,
        sync=False,
    )
    location_normal = Location(
        id=uuid4(),
        latitude=1.1,
        longitude=1.1,
        timestamp=now_ms + 1000,
        date=datetime.utcnow(),
        altitude=110.0,
        speed=15.0,
        speedLimit=20.0,
        distance=15.0,
        sync=False,
    )
    db.add_all([location_fast, location_normal])
    db.flush()

    raw_fast = RawSensorData(
        id=uuid4(),
        sensor_type=1,
        sensor_type_name="speed",
        values=[25.0],
        timestamp=now_ms,
        date=datetime.utcnow(),
        accuracy=3,
        location_id=location_fast.id,
        trip_id=active_trip.id,
        sync=False,
    )
    raw_normal = RawSensorData(
        id=uuid4(),
        sensor_type=1,
        sensor_type_name="speed",
        values=[15.0],
        timestamp=now_ms + 1000,
        date=datetime.utcnow(),
        accuracy=3,
        location_id=location_normal.id,
        trip_id=active_trip.id,
        sync=False,
    )
    db.add_all([raw_fast, raw_normal])
    db.commit()
    return driver


def test_driver_monitor_endpoint():
    with TestingSessionLocal() as db:
        driver = _seed_driver_data(db)
        driver_id = driver.driverProfileId

    response = client.get(f"/api/fleet/driver_monitor/{driver_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["driverProfileId"] == str(driver.driverProfileId)
    assert payload["activeTripStatus"] == "ACTIVE"
    assert payload["unsafeBehaviourCount"] == 2
    assert payload["unsafeBehaviourLast24h"] == 1
    assert payload["speedComplianceRatio"] == 0.5
    assert payload["speedingCount"] == 1
    assert len(payload["recentUnsafeBehaviours"]) == 2

