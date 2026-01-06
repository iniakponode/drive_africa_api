from datetime import datetime
from uuid import uuid4

from safedrive.models.driver_profile import DriverProfile
from safedrive.models.fleet import Fleet, VehicleGroup, DriverFleetAssignment
from safedrive.models.location import Location
from safedrive.models.raw_sensor_data import RawSensorData
from safedrive.models.trip import Trip
from safedrive.models.unsafe_behaviour import UnsafeBehaviour
from tests.db_fixtures import (
    TestingSessionLocal,
    client,
    create_api_client,
    create_tables,
    drop_tables,
)


def setup_database():
    drop_tables()
    create_tables()


def teardown_database():
    drop_tables()


def test_auth_me():
    setup_database()
    try:
        with TestingSessionLocal() as db:
            api_key = create_api_client(db, role="admin")

        headers = {"X-API-Key": api_key}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        payload = response.json()
        assert payload["role"] == "admin"
        assert payload["name"] == "admin-test-client"
    finally:
        teardown_database()


def test_analytics_endpoints():
    setup_database()
    try:
        with TestingSessionLocal() as db:
            fleet = Fleet(name="Ops Fleet", description="Test fleet", region="Lagos")
            db.add(fleet)
            db.flush()

            group_a = VehicleGroup(
                name="Route A", description="Daily", fleet_id=fleet.id
            )
            group_b = VehicleGroup(
                name="Route B", description="Long", fleet_id=fleet.id
            )
            db.add_all([group_a, group_b])
            db.flush()

            driver_a = DriverProfile(
                driverProfileId=uuid4(),
                email="driver.a@example.com",
                sync=False,
            )
            driver_b = DriverProfile(
                driverProfileId=uuid4(),
                email="driver.b@example.com",
                sync=False,
            )
            db.add_all([driver_a, driver_b])
            db.flush()

            db.add_all(
                [
                    DriverFleetAssignment(
                        driverProfileId=driver_a.driverProfileId,
                        fleet_id=fleet.id,
                        vehicle_group_id=group_a.id,
                        onboarding_completed=True,
                    ),
                    DriverFleetAssignment(
                        driverProfileId=driver_b.driverProfileId,
                        fleet_id=fleet.id,
                        vehicle_group_id=group_b.id,
                        onboarding_completed=True,
                    ),
                ]
            )

            now = datetime.utcnow()
            trip_a = Trip(
                id=uuid4(),
                driverProfileId=driver_a.driverProfileId,
                start_date=now,
                end_date=None,
                start_time=int(now.timestamp() * 1000),
                end_time=None,
                influence="Vehicle",
                sync=True,
            )
            trip_b = Trip(
                id=uuid4(),
                driverProfileId=driver_b.driverProfileId,
                start_date=now,
                end_date=None,
                start_time=int(now.timestamp() * 1000),
                end_time=None,
                influence="Vehicle",
                sync=True,
            )
            db.add_all([trip_a, trip_b])
            db.flush()

            location_a = Location(
                id=uuid4(),
                latitude=1.0,
                longitude=1.0,
                timestamp=int(now.timestamp() * 1000),
                date=now,
                altitude=0.0,
                speed=30.0,
                speedLimit=20.0,
                distance=1000.0,
                sync=True,
            )
            location_b = Location(
                id=uuid4(),
                latitude=1.0,
                longitude=1.0,
                timestamp=int(now.timestamp() * 1000),
                date=now,
                altitude=0.0,
                speed=30.0,
                speedLimit=20.0,
                distance=1000.0,
                sync=True,
            )
            db.add_all([location_a, location_b])
            db.flush()

            raw_a = RawSensorData(
                id=uuid4(),
                sensor_type=1,
                sensor_type_name="speed",
                values=[30.0],
                timestamp=int(now.timestamp() * 1000),
                date=now,
                accuracy=3,
                location_id=location_a.id,
                trip_id=trip_a.id,
                sync=True,
            )
            raw_b = RawSensorData(
                id=uuid4(),
                sensor_type=1,
                sensor_type_name="speed",
                values=[30.0],
                timestamp=int(now.timestamp() * 1000),
                date=now,
                accuracy=3,
                location_id=location_b.id,
                trip_id=trip_b.id,
                sync=True,
            )
            db.add_all([raw_a, raw_b])

            db.add(
                UnsafeBehaviour(
                    id=uuid4(),
                    trip_id=trip_a.id,
                    driverProfileId=driver_a.driverProfileId,
                    behaviour_type="hard_brake",
                    severity=0.9,
                    timestamp=int(now.timestamp() * 1000),
                    date=now,
                    updated_at=None,
                    updated=False,
                    sync=False,
                    alcohol_influence=False,
                )
            )
            db.add_all(
                [
                    UnsafeBehaviour(
                        id=uuid4(),
                        trip_id=trip_b.id,
                        driverProfileId=driver_b.driverProfileId,
                        behaviour_type="hard_brake",
                        severity=0.9,
                        timestamp=int(now.timestamp() * 1000),
                        date=now,
                        updated_at=None,
                        updated=False,
                        sync=False,
                        alcohol_influence=False,
                    ),
                    UnsafeBehaviour(
                        id=uuid4(),
                        trip_id=trip_b.id,
                        driverProfileId=driver_b.driverProfileId,
                        behaviour_type="hard_turn",
                        severity=0.8,
                        timestamp=int(now.timestamp() * 1000),
                        date=now,
                        updated_at=None,
                        updated=False,
                        sync=False,
                        alcohol_influence=False,
                    ),
                ]
            )

            db.commit()
            driver_a_id = driver_a.driverProfileId
            driver_b_id = driver_b.driverProfileId

            api_key = create_api_client(db, role="fleet_manager", fleet_id=fleet.id)

        headers = {"X-API-Key": api_key}
        leaderboard = client.get("/api/analytics/leaderboard", headers=headers)
        assert leaderboard.status_code == 200
        leaderboard_payload = leaderboard.json()
        assert leaderboard_payload["total_drivers"] == 2
        assert leaderboard_payload["best"][0]["driverProfileId"] == str(driver_a_id)
        assert leaderboard_payload["worst"][0]["driverProfileId"] == str(driver_b_id)

        series = client.get(
            f"/api/analytics/driver-ubpk?driverProfileId={driver_a_id}",
            headers=headers,
        )
        assert series.status_code == 200
        assert series.json()["driverProfileId"] == str(driver_a_id)

        bad_days = client.get("/api/analytics/bad-days", headers=headers)
        assert bad_days.status_code == 200
        assert len(bad_days.json()["drivers"]) == 2

        kpis = client.get("/api/analytics/driver-kpis", headers=headers)
        assert kpis.status_code == 200
        assert len(kpis.json()["drivers"]) == 2
    finally:
        teardown_database()
