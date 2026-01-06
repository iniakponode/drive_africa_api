from datetime import datetime
from uuid import uuid4

from safedrive.models.alcohol_questionnaire import AlcoholQuestionnaire
from safedrive.models.driver_profile import DriverProfile
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


def test_researcher_summaries_and_bundle():
    setup_database()
    try:
        with TestingSessionLocal() as db:
            driver = DriverProfile(
                driverProfileId=uuid4(),
                email="researcher.driver@example.com",
                sync=True,
            )
            db.add(driver)
            db.flush()

            trip = Trip(
                id=uuid4(),
                driverProfileId=driver.driverProfileId,
                start_date=datetime.utcnow(),
                end_date=None,
                start_time=int(datetime.utcnow().timestamp() * 1000),
                end_time=None,
                influence="Fatigue",
                sync=True,
            )
            db.add(trip)

            behaviour = UnsafeBehaviour(
                id=uuid4(),
                trip_id=trip.id,
                driverProfileId=driver.driverProfileId,
                behaviour_type="hard_brake",
                severity=0.75,
                timestamp=int(datetime.utcnow().timestamp() * 1000),
                date=datetime.utcnow(),
                updated_at=None,
                updated=False,
                sync=False,
                alcohol_influence=False,
            )
            db.add(behaviour)

            raw = RawSensorData(
                id=uuid4(),
                sensor_type=1,
                sensor_type_name="accelerometer",
                values=[0.1, 0.2, 0.3],
                timestamp=int(datetime.utcnow().timestamp() * 1000),
                date=datetime.utcnow(),
                accuracy=3,
                location_id=None,
                trip_id=trip.id,
                sync=False,
            )
            db.add(raw)

            questionnaire = AlcoholQuestionnaire(
                id=uuid4(),
                driverProfileId=driver.driverProfileId,
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
            db.add(questionnaire)

            report = NLGReport(
                id=uuid4(),
                driverProfileId=driver.driverProfileId,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow(),
                report_text="Keep a smoother braking cadence.",
                generated_at=datetime.utcnow(),
                sync=True,
            )
            db.add(report)
            db.commit()
            driver_id = driver.driverProfileId
            api_key = create_api_client(db, role="researcher")

        headers = {"X-API-Key": api_key}
        summary_resp = client.get(
            f"/api/researcher/unsafe_behaviours/summary?driverProfileId={driver_id}",
            headers=headers,
        )
        assert summary_resp.status_code == 200
        summary_data = summary_resp.json()
        assert summary_data[0]["behaviour_type"] == "hard_brake"
        assert summary_data[0]["total"] == 1

        sensor_resp = client.get(
            f"/api/researcher/raw_sensor_data/summary?driverProfileId={driver_id}",
            headers=headers,
        )
        assert sensor_resp.status_code == 200
        sensor_data = sensor_resp.json()
        assert sensor_data[0]["sensor_type_name"] == "accelerometer"
        assert sensor_data[0]["total"] == 1

        bundle_resp = client.get(
            f"/api/researcher/alcohol_trip_bundle?driverProfileId={driver_id}",
            headers=headers,
        )
        assert bundle_resp.status_code == 200
        bundle = bundle_resp.json()
        assert bundle["matchingRule"] == "Same UTC calendar day"
        assert bundle["matchingTimezone"] == "UTC"
        assert bundle["total_trips"] == 1
        assert bundle["total_questionnaires"] == 1
        assert bundle["trips"][0]["matchedQuestionnaire"]["drankAlcohol"] is False
    finally:
        teardown_database()


def test_researcher_exports_and_status():
    setup_database()
    try:
        report_week = "2025-W01"
        with TestingSessionLocal() as db:
            driver = DriverProfile(
                driverProfileId=uuid4(),
                email="export.driver@example.com",
                sync=False,
            )
            db.add(driver)
            db.flush()

            trip = Trip(
                id=uuid4(),
                driverProfileId=driver.driverProfileId,
                start_date=datetime.utcnow(),
                end_date=None,
                start_time=int(datetime.utcnow().timestamp() * 1000),
                end_time=None,
                influence=None,
                sync=True,
            )
            db.add(trip)

            raw = RawSensorData(
                id=uuid4(),
                sensor_type=2,
                sensor_type_name="gyroscope",
                values=[1.0, 2.0, 3.0],
                timestamp=int(datetime.utcnow().timestamp() * 1000),
                date=datetime.utcnow(),
                accuracy=2,
                location_id=None,
                trip_id=trip.id,
                sync=True,
            )
            db.add(raw)

            report = NLGReport(
                id=uuid4(),
                driverProfileId=driver.driverProfileId,
                start_date=datetime(2025, 1, 2),
                end_date=datetime(2025, 1, 3),
                report_text="Maintain lane consistency.",
                generated_at=datetime(2025, 1, 3),
                sync=True,
            )
            db.add(report)
            db.commit()
            driver_id = driver.driverProfileId
            api_key = create_api_client(db, role="researcher")

        headers = {"X-API-Key": api_key}
        export_nlg = client.get(
            f"/api/researcher/nlg_reports/export?driverProfileId={driver_id}&format=jsonl",
            headers=headers,
        )
        assert export_nlg.status_code == 200
        assert "Maintain lane consistency." in export_nlg.text

        export_week = client.get(
            f"/api/researcher/nlg_reports/export?driverProfileId={driver_id}&week={report_week}",
            headers=headers,
        )
        assert export_week.status_code == 200
        assert "Maintain lane consistency." in export_week.text

        export_raw = client.get(
            f"/api/researcher/raw_sensor_data/export?driverProfileId={driver_id}&format=csv",
            headers=headers,
        )
        assert export_raw.status_code == 200
        assert "sensor_type_name" in export_raw.text

        status_resp = client.get("/api/researcher/ingestion/status", headers=headers)
        assert status_resp.status_code == 200
        status_payload = status_resp.json()
        datasets = {item["dataset"] for item in status_payload["datasets"]}
        assert "raw_sensor_data" in datasets
        assert "nlg_reports" in datasets
    finally:
        teardown_database()


def test_researcher_trip_export_and_backfill():
    setup_database()
    try:
        with TestingSessionLocal() as db:
            driver = DriverProfile(
                driverProfileId=uuid4(),
                email="backfill.driver@example.com",
                sync=False,
            )
            db.add(driver)
            db.flush()

            trip = Trip(
                id=uuid4(),
                driverProfileId=driver.driverProfileId,
                start_date=datetime.utcnow(),
                end_date=None,
                start_time=int(datetime.utcnow().timestamp() * 1000),
                end_time=None,
                influence=None,
                sync=True,
                alcohol_probability=None,
                user_alcohol_response=None,
            )
            db.add(trip)

            questionnaire = AlcoholQuestionnaire(
                id=uuid4(),
                driverProfileId=driver.driverProfileId,
                drankAlcohol=True,
                selectedAlcoholTypes="beer",
                beerQuantity="1",
                wineQuantity="0",
                spiritsQuantity="0",
                firstDrinkTime="18:00",
                lastDrinkTime="19:00",
                emptyStomach=False,
                caffeinatedDrink=False,
                impairmentLevel=1,
                date=datetime.utcnow(),
                plansToDrive=True,
                sync=True,
            )
            db.add(questionnaire)
            db.commit()
            driver_id = driver.driverProfileId
            trip_id = trip.id
            api_key = create_api_client(db, role="researcher")

        headers = {"X-API-Key": api_key}
        backfill_resp = client.post(
            f"/api/researcher/trips/backfill_alcohol?driverProfileId={driver_id}",
            headers=headers,
        )
        assert backfill_resp.status_code == 200
        backfill_payload = backfill_resp.json()
        assert backfill_payload["matchedTrips"] == 1
        assert backfill_payload["updatedTrips"] == 1

        export_trips = client.get(
            f"/api/researcher/trips/export?driverProfileId={driver_id}&format=jsonl",
            headers=headers,
        )
        assert export_trips.status_code == 200
        assert "matchedQuestionnaire" in export_trips.text
        assert "matchingRule" in export_trips.text

        with TestingSessionLocal() as db:
            refreshed = db.query(Trip).filter(Trip.id == trip_id).first()
            assert refreshed.user_alcohol_response == "1"
            assert refreshed.alcohol_probability == 1.0
    finally:
        teardown_database()
