from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field


class TripModel(BaseModel):
    """Simplified trip model used for dashboard aggregation."""

    id: UUID
    driver_id: UUID = Field(..., alias="driverProfileId")
    start_time: Optional[datetime] = Field(None, alias="startTime")

    class Config:
        from_attributes = True
        populate_by_name = True


class SensorDataModel(BaseModel):
    """Simplified sensor data used for aggregation."""

    trip_id: UUID = Field(..., alias="tripId")
    timestamp: Optional[datetime] = Field(None, alias="timestamp")

    class Config:
        from_attributes = True
        populate_by_name = True


def process_and_aggregate_data(
    trips: List[TripModel], sensor_data: Optional[List[SensorDataModel]] = None
) -> List[dict]:
    """Process trips and compute week strings for the dashboard."""

    sensor_data = sensor_data or []
    valid_sensor_data = [s for s in sensor_data if s.trip_id and s.timestamp]
    earliest_sensor_ts: Dict[str, datetime] = {}
    for sensor in valid_sensor_data:
        tid = str(sensor.trip_id)
        ts = sensor.timestamp
        if ts is None:
            continue
        if tid not in earliest_sensor_ts or ts < earliest_sensor_ts[tid]:
            earliest_sensor_ts[tid] = ts

    results: List[dict] = []
    for trip in trips:
        ts: Optional[datetime] = None
        if trip.start_time:
            ts = trip.start_time
        elif earliest_sensor_ts.get(str(trip.id)):
            ts = earliest_sensor_ts[str(trip.id)]

        if ts:
            iy, iw, _ = ts.isocalendar()
            week_str = f"{iy}-W{iw:02d}"
        else:
            week_str = ""
        start_str = trip.start_time.isoformat() if trip.start_time else None

        results.append({
            "id": str(trip.id),
            "driverProfileId": str(trip.driver_id),
            "start_time": start_str,
            "week": week_str,
        })

    return results
