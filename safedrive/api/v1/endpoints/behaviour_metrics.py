from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from uuid import UUID
from typing import List, Dict, Tuple
from scipy.stats import ttest_ind

from safedrive.database.db import get_db
from safedrive.models.trip import Trip
from safedrive.models.location import Location
from safedrive.models.unsafe_behaviour import UnsafeBehaviour
from safedrive.schemas.behaviour_metrics import (
    DriverUBPK,
    TripUBPK,
    WeeklyDriverUBPK,
    ImprovementSummary,
)

router = APIRouter()


def _trip_distances(db: Session) -> Dict[UUID, Tuple[UUID, float, datetime]]:
    """Return mapping of trip_id -> (driver_id, distance_m, start_date)."""
    results = (
        db.query(
            Trip.id,
            Trip.driverProfileId,
            func.coalesce(func.sum(Location.distance), 0.0),
            Trip.start_date,
        )
        .outerjoin(Location, Location.trip_id == Trip.id)
        .group_by(Trip.id)
        .all()
    )
    return {r[0]: (r[1], float(r[2] or 0), r[3]) for r in results}


def _trip_behaviour_counts(db: Session) -> Dict[UUID, int]:
    results = (
        db.query(UnsafeBehaviour.trip_id, func.count(UnsafeBehaviour.id))
        .group_by(UnsafeBehaviour.trip_id)
        .all()
    )
    return {r[0]: int(r[1]) for r in results}


@router.get("/behaviour_metrics/ubpk", response_model=List[DriverUBPK])
def ubpk_per_driver(db: Session = Depends(get_db)) -> List[DriverUBPK]:
    """Return UBPK aggregated per driver."""
    try:
        distances = _trip_distances(db)
        behaviours = _trip_behaviour_counts(db)
        agg: Dict[UUID, Tuple[int, float]] = {}
        for trip_id, (driver_id, dist, _) in distances.items():
            agg.setdefault(driver_id, [0, 0.0])
            agg[driver_id][0] += behaviours.get(trip_id, 0)
            agg[driver_id][1] += dist
        result = []
        for driver_id, (count, dist) in agg.items():
            ubpk = (count / (dist / 1000)) if dist > 0 else 0.0
            result.append(DriverUBPK(driverProfileId=driver_id, ubpk=ubpk))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/behaviour_metrics/trip", response_model=List[TripUBPK])
def ubpk_per_trip(db: Session = Depends(get_db)) -> List[TripUBPK]:
    """Return UBPK for each trip."""
    try:
        distances = _trip_distances(db)
        behaviours = _trip_behaviour_counts(db)
        result = []
        for trip_id, (driver_id, dist, _) in distances.items():
            count = behaviours.get(trip_id, 0)
            ubpk = (count / (dist / 1000)) if dist > 0 else 0.0
            result.append(TripUBPK(trip_id=trip_id, driverProfileId=driver_id, ubpk=ubpk))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/behaviour_metrics/weekly", response_model=List[WeeklyDriverUBPK])
def ubpk_per_week(db: Session = Depends(get_db)) -> List[WeeklyDriverUBPK]:
    """Return weekly UBPK metrics per driver."""
    try:
        distances = _trip_distances(db)
        behaviours = _trip_behaviour_counts(db)
        weekly: Dict[Tuple[UUID, datetime], Tuple[int, float]] = {}
        for trip_id, (driver_id, dist, start) in distances.items():
            if start is None:
                continue
            week_start = start.date() - timedelta(days=start.weekday())
            key = (driver_id, week_start)
            weekly.setdefault(key, [0, 0.0])
            weekly[key][0] += behaviours.get(trip_id, 0)
            weekly[key][1] += dist
        result = []
        for (driver_id, week_start), (count, dist) in weekly.items():
            ubpk = (count / (dist / 1000)) if dist > 0 else 0.0
            result.append(
                WeeklyDriverUBPK(
                    driverProfileId=driver_id, week_start=week_start, ubpk=ubpk
                )
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/behaviour_metrics/improvement", response_model=List[ImprovementSummary])
def drivers_improvement(db: Session = Depends(get_db)) -> List[ImprovementSummary]:
    """Analyse drivers that improved their UBPK over time using a t-test."""
    try:
        weekly_metrics = ubpk_per_week(db)
    except HTTPException as exc:
        raise exc
    driver_map: Dict[UUID, List[Tuple[datetime, float]]] = {}
    for m in weekly_metrics:
        driver_map.setdefault(m.driverProfileId, []).append((m.week_start, m.ubpk))

    results: List[ImprovementSummary] = []
    for driver_id, data in driver_map.items():
        data.sort(key=lambda x: x[0])
        ubpks = [d[1] for d in data]
        n = len(ubpks)
        if n < 2:
            continue
        first_half = ubpks[: n // 2]
        second_half = ubpks[n // 2 :]
        if not second_half or not first_half:
            continue
        stat, p_value = ttest_ind(first_half, second_half, equal_var=False)
        improved = (p_value < 0.05) and (sum(second_half) / len(second_half) < sum(first_half) / len(first_half))
        results.append(
            ImprovementSummary(
                driverProfileId=driver_id,
                improved=improved,
                p_value=float(p_value),
            )
        )
    return results
    
