from __future__ import annotations

from datetime import datetime
from typing import List, Optional
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


def process_and_aggregate_data(trips: List[TripModel]) -> List[dict]:
    """Process trips and compute week strings for the dashboard."""

    results: List[dict] = []
    for trip in trips:
        if trip.start_time:
            iy, iw, _ = trip.start_time.isocalendar()
            week_str = f"{iy}-W{iw:02d}"
            start_str = trip.start_time.isoformat()
        else:
            week_str = ""
            start_str = None
        results.append({
            "id": str(trip.id),
            "driverProfileId": str(trip.driver_id),
            "start_time": start_str,
            "week": week_str,
        })
    return results
