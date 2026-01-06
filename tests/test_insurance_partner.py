from datetime import datetime
from uuid import uuid4

from safedrive.models.driver_profile import DriverProfile
from safedrive.models.insurance_partner import InsurancePartner, InsurancePartnerDriver
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


def test_insurance_endpoints():
    setup_database()
    try:
        with TestingSessionLocal() as db:
            partner = InsurancePartner(
                name="Test Insurer",
                label="test-insurer",
                active=True,
            )
            db.add(partner)
            db.flush()

            driver = DriverProfile(
                driverProfileId=uuid4(),
                email="insurance.driver@example.com",
                sync=True,
            )
            db.add(driver)
            db.flush()

            db.add(
                InsurancePartnerDriver(
                    partner_id=partner.id,
                    driverProfileId=driver.driverProfileId,
                )
            )

            trip = Trip(
                id=uuid4(),
                driverProfileId=driver.driverProfileId,
                start_date=datetime.utcnow(),
                end_date=None,
                start_time=int(datetime.utcnow().timestamp() * 1000),
                end_time=None,
                influence="Vehicle",
                sync=True,
            )
            db.add(trip)

            location = Location(
                id=uuid4(),
                latitude=1.0,
                longitude=1.0,
                timestamp=int(datetime.utcnow().timestamp() * 1000),
                date=datetime.utcnow(),
                altitude=10.0,
                speed=40.0,
                speedLimit=30.0,
                distance=500.0,
                sync=True,
            )
            db.add(location)
            db.flush()

            raw = RawSensorData(
                id=uuid4(),
                sensor_type=1,
                sensor_type_name="speed",
                values=[40.0],
                timestamp=int(datetime.utcnow().timestamp() * 1000),
                date=datetime.utcnow(),
                accuracy=3,
                location_id=location.id,
                trip_id=trip.id,
                sync=True,
            )
            db.add(raw)

            behaviour = UnsafeBehaviour(
                id=uuid4(),
                trip_id=trip.id,
                driverProfileId=driver.driverProfileId,
                behaviour_type="hard_brake",
                severity=0.9,
                timestamp=int(datetime.utcnow().timestamp() * 1000),
                date=datetime.utcnow(),
                updated_at=None,
                updated=False,
                sync=False,
                alcohol_influence=False,
            )
            db.add(behaviour)
            db.commit()

            api_key = create_api_client(
                db,
                role="insurance_partner",
                insurance_partner_id=partner.id,
            )
            driver_id = driver.driverProfileId

        headers = {"X-API-Key": api_key}
        telematics = client.get("/api/insurance/telematics/trips", headers=headers)
        assert telematics.status_code == 200
        payload = telematics.json()
        assert payload["total"] == 1

        report = client.get(f"/api/insurance/reports/{driver_id}", headers=headers)
        assert report.status_code == 200
        assert report.json()["driverProfileId"] == str(driver_id)

        aggregate = client.get("/api/insurance/reports/aggregate", headers=headers)
        assert aggregate.status_code == 200
        aggregate_payload = aggregate.json()
        assert aggregate_payload["total_trips"] == 1
        assert aggregate_payload["total_drivers"] == 1
        assert aggregate_payload["total_unsafe_events"] == 1

        alerts = client.get("/api/insurance/alerts?minSeverity=0.5", headers=headers)
        assert alerts.status_code == 200
        assert len(alerts.json()) >= 1

        export = client.get(
            "/api/insurance/raw_sensor_data/export?format=jsonl",
            headers=headers,
        )
        assert export.status_code == 200
        assert "sensor_type_name" in export.text
    finally:
        teardown_database()
