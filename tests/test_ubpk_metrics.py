import sys
import types
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from uuid import uuid4
from datetime import datetime

# Stub fastapi
fastapi_stub = types.ModuleType('fastapi')
fastapi_stub.APIRouter = lambda *a, **k: types.SimpleNamespace(get=lambda *a, **k: (lambda f: f))
fastapi_stub.Depends = lambda x: x
class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str = ''):
        self.status_code = status_code
        self.detail = detail
fastapi_stub.HTTPException = HTTPException
fastapi_stub.Query = lambda *a, **k: None
sys.modules['fastapi'] = fastapi_stub

# Stub sqlalchemy
sqlalchemy_stub = types.ModuleType('sqlalchemy')
sqlalchemy_stub.func = types.SimpleNamespace(coalesce=lambda *a, **k: 0)
sqlalchemy_stub.orm = types.SimpleNamespace(Session=object)
sys.modules['sqlalchemy'] = sqlalchemy_stub
sys.modules['sqlalchemy.orm'] = sqlalchemy_stub.orm

# stub safedrive dependencies to avoid heavy imports
db_stub = types.ModuleType('safedrive.database.db')
db_stub.get_db = lambda: None
sys.modules['safedrive.database.db'] = db_stub
models_stub = types.ModuleType('safedrive.models.trip')
models_stub.Trip = type('Trip', (), {'id': None, 'driverProfileId': None, 'start_date': None, 'start_time': None})
sys.modules['safedrive.models.trip'] = models_stub
loc_stub = types.ModuleType('safedrive.models.location')
loc_stub.Location = type('Location', (), {'id': None, 'distance': None})
sys.modules['safedrive.models.location'] = loc_stub
rsd_stub = types.ModuleType('safedrive.models.raw_sensor_data')
rsd_stub.RawSensorData = type('RawSensorData', (), {'trip_id': None, 'location_id': None})
sys.modules['safedrive.models.raw_sensor_data'] = rsd_stub
beh_stub = types.ModuleType('safedrive.models.unsafe_behaviour')
beh_stub.UnsafeBehaviour = type('UnsafeBehaviour', (), {'id': None, 'trip_id': None})
sys.modules['safedrive.models.unsafe_behaviour'] = beh_stub

from app.routers import ubpk_metrics

# Override dependency
ubpk_metrics.get_db = lambda: None


def test_trip_metrics(monkeypatch):
    trip_id = uuid4()
    driver_id = uuid4()
    def fake_dist(db):
        return {trip_id: (driver_id, 2000.0, datetime(2024,1,1), 111)}
    def fake_beh(db):
        return {trip_id: 4}
    monkeypatch.setattr(ubpk_metrics, '_trip_distances', fake_dist)
    monkeypatch.setattr(ubpk_metrics, '_trip_behaviour_counts', fake_beh)
    res = ubpk_metrics.trip_metrics(trip_id, None)
    assert res['driverProfileId'] == driver_id
    assert res['ubpk'] == 2.0


def test_driver_weekly(monkeypatch):
    driver = uuid4()
    t = uuid4()
    week = '2024-01'
    def fake_dist(db):
        return {t: (driver, 1000.0, datetime.fromisocalendar(2024,1,1), 1)}
    def fake_beh(db):
        return {t: 3}
    monkeypatch.setattr(ubpk_metrics, '_trip_distances', fake_dist)
    monkeypatch.setattr(ubpk_metrics, '_trip_behaviour_counts', fake_beh)
    data = ubpk_metrics.driver_weekly_metrics(driver, week, None)
    assert data['ubpk'] == 3.0


def test_driver_improvement(monkeypatch):
    driver = uuid4()
    t1 = uuid4()
    t2 = uuid4()
    t3 = uuid4()
    t4 = uuid4()
    today = datetime.now()
    this_week = datetime.fromisocalendar(today.year, today.isocalendar().week,1)
    last_week = this_week - ubpk_metrics.timedelta(weeks=1)
    def fake_dist(db):
        return {
            t1: (driver, 1000.0, last_week, 1),
            t2: (driver, 1000.0, last_week, 1),
            t3: (driver, 1000.0, this_week, 1),
            t4: (driver, 1000.0, this_week, 1),
        }
    def fake_beh(db):
        return {t1: 4, t2: 3, t3: 2, t4: 1}
    monkeypatch.setattr(ubpk_metrics, '_trip_distances', fake_dist)
    monkeypatch.setattr(ubpk_metrics, '_trip_behaviour_counts', fake_beh)
    res = ubpk_metrics.driver_improvement(driver, None)
    assert 'p_value' in res and 'mean_difference' in res


def test_parse_iso_week_both_formats():
    start1, end1 = ubpk_metrics.parse_iso_week("2024-W06")
    start2, end2 = ubpk_metrics.parse_iso_week("2024-06")
    assert start1 == start2
    assert end1 == end2
