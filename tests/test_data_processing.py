import os
import sys
import types
from uuid import uuid4

from datetime import datetime

# Stub out fastapi to avoid heavy dependency during tests
fastapi_stub = types.ModuleType("fastapi")
fastapi_stub.APIRouter = lambda *a, **k: types.SimpleNamespace()
fastapi_stub.Depends = lambda x=None: x
class HTTPException(Exception):
    pass
fastapi_stub.HTTPException = HTTPException
fastapi_stub.Query = lambda *a, **k: None
sys.modules["fastapi"] = fastapi_stub

# Minimal pydantic stub for tests
pydantic_stub = types.ModuleType("pydantic")
class BaseModel:
    def __init__(self, **data):
        for k, v in data.items():
            if isinstance(v, str) and "time" in k.lower():
                if v.endswith("Z"):
                    v = datetime.fromisoformat(v.replace("Z", "+00:00"))
                else:
                    v = datetime.fromisoformat(v)
            setattr(self, k, v)
    def model_dump(self, *a, **k):
        return self.__dict__
def Field(default=None, **kwargs):
    return default
pydantic_stub.BaseModel = BaseModel
pydantic_stub.Field = Field
sys.modules["pydantic"] = pydantic_stub

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import importlib.util

module_path = os.path.join(os.path.dirname(__file__), "..", "safedrive", "core", "data_processing.py")
spec = importlib.util.spec_from_file_location("data_processing", module_path)
data_processing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_processing)
TripModel = data_processing.TripModel
SensorDataModel = data_processing.SensorDataModel
process_and_aggregate_data = data_processing.process_and_aggregate_data


def test_week_string_never_none():
    trip = TripModel(
        id=uuid4(),
        driverProfileId=uuid4(),
        start_time="2024-01-03T10:15:30Z",
    )
    result = process_and_aggregate_data([trip])[0]
    assert result["week"] == "2024-W01"
    assert result["start_time"] == "2024-01-03T10:15:30+00:00"


def test_empty_week_when_no_start():
    trip = TripModel(id=uuid4(), driverProfileId=uuid4(), start_time=None)
    result = process_and_aggregate_data([trip])[0]
    assert result["week"] == ""
    assert result["start_time"] is None


def test_week_from_sensor_timestamp_when_no_start():
    trip_id = uuid4()
    trip = TripModel(id=trip_id, driverProfileId=uuid4(), start_time=None)
    sensor = SensorDataModel(trip_id=trip_id, timestamp="2024-02-05T00:00:00Z")
    result = process_and_aggregate_data([trip], [sensor])[0]
    assert result["week"] == "2024-W06"
    assert result["start_time"] is None


def test_earliest_sensor_timestamp_used():
    trip_id = uuid4()
    trip = TripModel(id=trip_id, driverProfileId=uuid4(), start_time=None)
    s1 = SensorDataModel(trip_id=trip_id, timestamp="2024-02-06T00:00:00Z")
    s2 = SensorDataModel(trip_id=trip_id, timestamp="2024-02-04T12:00:00Z")
    result = process_and_aggregate_data([trip], [s1, s2])[0]
    assert result["week"] == "2024-W05"
