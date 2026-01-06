from datetime import datetime
from uuid import uuid4

from safedrive.models.alcohol_questionnaire import AlcoholQuestionnaire
from safedrive.models.driver_profile import DriverProfile
from safedrive.models.driving_tip import DrivingTip
from safedrive.models.fleet import Fleet, VehicleGroup
from safedrive.models.location import Location
from safedrive.models.nlg_report import NLGReport
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


def test_driver_assignment_and_compliance():
    setup_database()
    try:
        with TestingSessionLocal() as db:
            driver = DriverProfile(
                driverProfileId=uuid4(),
                email="fleet.manager@example.com",
                sync=False,
            )
            db.add(driver)
            db.flush()

            fleet = Fleet(name="North Fleet", description="Test fleet", region="Lagos")
            db.add(fleet)
            db.flush()

            vehicle_group = VehicleGroup(
                name="Route A",
                description="Daily pickups",
                fleet_id=fleet.id,
            )
            db.add(vehicle_group)
            db.flush()

            questionnaire = AlcoholQuestionnaire(
                id=uuid4(),
                driverProfileId=driver.driverProfileId,
                drankAlcohol=True,
                selectedAlcoholTypes="beer",
                beerQuantity="2",
                wineQuantity="0",
                spiritsQuantity="0",
                firstDrinkTime="18:00",
                lastDrinkTime="20:00",
                emptyStomach=False,
                caffeinatedDrink=True,
                impairmentLevel=2,
                date=datetime.utcnow(),
                plansToDrive=True,
                sync=True,
            )
            db.add(questionnaire)
            db.commit()
            driver_id = driver.driverProfileId
            fleet_id = fleet.id
            vehicle_group_id = vehicle_group.id
            api_key = create_api_client(db, role="admin")

        headers = {"X-API-Key": api_key}
        response = client.post(
            "/api/fleet/assignments/",
            json={
                "driverProfileId": str(driver_id),
                "fleet_id": str(fleet_id),
                "vehicle_group_id": str(vehicle_group_id),
                "onboarding_completed": True,
                "compliance_note": "Checked onboarding forms",
            },
            headers=headers,
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["driverProfileId"] == str(driver.driverProfileId)
        assert payload["fleet"]["name"] == "North Fleet"
        assert payload["vehicle_group"]["name"] == "Route A"

        assignment_response = client.get(
            f"/api/fleet/assignments/{driver_id}",
            headers=headers,
        )
        assert assignment_response.status_code == 200
        data = assignment_response.json()
        assert data["assignment"]["onboarding_completed"] is True
        assert data["questionnaire"]["drankAlcohol"] is True
        assert data["questionnaire"]["impairmentLevel"] == 2
    finally:
        teardown_database()


def test_driver_event_lifecycle():
    setup_database()
    try:
        with TestingSessionLocal() as db:
            driver = DriverProfile(
                driverProfileId=uuid4(),
                email="event.driver@example.com",
                sync=False,
            )
            db.add(driver)
            db.commit()
            driver_id = driver.driverProfileId
            api_key = create_api_client(db, role="admin")

        headers = {"X-API-Key": api_key}
        event_resp = client.post(
            "/api/fleet/events/",
            json={
                "driverProfileId": str(driver_id),
                "event_type": "TRIP_STARTED",
                "gps_health": "GPS_OK",
                "message": "Trip recording started",
            },
            headers=headers,
        )
        assert event_resp.status_code == 201
        event_payload = event_resp.json()
        assert event_payload["event_type"] == "TRIP_STARTED"
        assert event_payload["gps_health"] == "GPS_OK"

        list_resp = client.get(
            f"/api/fleet/events/{driver.driverProfileId}?limit=5",
            headers=headers,
        )
        assert list_resp.status_code == 200
        events = list_resp.json()["events"]
        assert len(events) == 1
        assert events[0]["event_type"] == "TRIP_STARTED"
    finally:
        teardown_database()


def test_trip_context_and_report_endpoints():
    setup_database()
    try:
        with TestingSessionLocal() as db:
            driver = DriverProfile(
                driverProfileId=uuid4(),
                email="context.driver@example.com",
                sync=False,
            )
            db.add(driver)
            db.commit()
            driver_id = driver.driverProfileId

            trip = Trip(
                id=uuid4(),
                driverProfileId=driver_id,
                start_date=datetime.utcnow(),
                end_date=None,
                start_time=int(datetime.utcnow().timestamp() * 1000),
                end_time=None,
                influence="Vehicle",
                sync=True,
            )
            db.add(trip)

            tip = DrivingTip(
                tip_id=uuid4(),
                title="Stay Smooth",
                meaning="Avoid hard braking to keep passengers safe",
                penalty="None",
                fine="0",
                law="N/A",
                hostility="Low",
                summary_tip="Maintain cushion distance",
                sync=True,
                date=datetime.utcnow(),
                profile_id=driver_id,
            )
            db.add(tip)

            behaviour = UnsafeBehaviour(
                id=uuid4(),
                trip_id=trip.id,
                driverProfileId=driver_id,
                behaviour_type="hard_brake",
                severity=0.85,
                timestamp=int(datetime.utcnow().timestamp() * 1000),
                date=datetime.utcnow(),
                updated_at=None,
                updated=False,
                sync=False,
                alcohol_influence=False,
            )
            db.add(behaviour)

            report = NLGReport(
                id=uuid4(),
                driverProfileId=driver_id,
                report_text="Smooth driving observed after initial hard brake.",
                generated_at=datetime.utcnow(),
                sync=True,
            )
            db.add(report)

            location = Location(
                id=uuid4(),
                latitude=0.1,
                longitude=0.1,
                timestamp=int(datetime.utcnow().timestamp() * 1000),
                date=datetime.utcnow(),
                altitude=1.0,
                speed=30.0,
                speedLimit=20.0,
                distance=500.0,
                sync=False,
            )
            db.add(location)
            db.flush()

            raw = RawSensorData(
                id=uuid4(),
                sensor_type=1,
                sensor_type_name="speed",
                values=[30.0],
                timestamp=int(datetime.utcnow().timestamp() * 1000),
                date=datetime.utcnow(),
                accuracy=3,
                location_id=location.id,
                trip_id=trip.id,
                sync=False,
            )
            db.add(raw)

            alcohol_response = AlcoholQuestionnaire(
                id=uuid4(),
                driverProfileId=driver_id,
                drankAlcohol=False,
                selectedAlcoholTypes="none",
                beerQuantity="0",
                wineQuantity="0",
                spiritsQuantity="0",
                firstDrinkTime="00:00",
                lastDrinkTime="00:00",
                emptyStomach=False,
                caffeinatedDrink=False,
                impairmentLevel=0,
                date=datetime.utcnow(),
                plansToDrive=True,
                sync=True,
            )
            db.add(alcohol_response)

            db.commit()
            trip_id = trip.id
            api_key = create_api_client(db, role="admin")

        headers = {"X-API-Key": api_key}
        context_response = client.get(
            f"/api/fleet/trips/{trip_id}/context",
            headers=headers,
        )
        assert context_response.status_code == 200
        context_payload = context_response.json()
        assert context_payload["driverProfileId"] == str(driver_id)
        assert len(context_payload["tips"]) == 1
        assert len(context_payload["severity_findings"]) == 1
        assert len(context_payload["nlg_reports"]) == 1

        fleet_report = client.get(
            f"/api/fleet/reports/{driver_id}",
            headers=headers,
        )
        assert fleet_report.status_code == 200
        report_payload = fleet_report.json()
        assert report_payload["speed_compliance"]["speeding_events"] >= 0
        assert len(report_payload["trips"]) >= 1
        assert len(report_payload["unsafe_behaviour_logs"]) >= 1

        download_response = client.get(
            f"/api/fleet/reports/{driver_id}/download",
            headers=headers,
        )
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/json"
    finally:
        teardown_database()
