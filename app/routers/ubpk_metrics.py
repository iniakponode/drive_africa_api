from datetime import datetime, timedelta, date
from typing import Dict, Tuple, List
from uuid import UUID
from statistics import NormalDist
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from safedrive.database.db import get_db
from safedrive.models.trip import Trip
from safedrive.models.location import Location
from safedrive.models.unsafe_behaviour import UnsafeBehaviour

router = APIRouter()


def _trip_distances(db: Session) -> Dict[UUID, Tuple[UUID, float, datetime, int]]:
    results = (
        db.query(
            Trip.id,
            Trip.driverProfileId,
            func.coalesce(func.sum(Location.distance), 0.0),
            Trip.start_date,
            Trip.start_time,
        )
        .outerjoin(Location, Location.trip_id == Trip.id)
        .group_by(Trip.id)
        .all()
    )
    return {r[0]: (r[1], float(r[2] or 0), r[3], r[4]) for r in results}


def _trip_behaviour_counts(db: Session) -> Dict[UUID, int]:
    results = (
        db.query(UnsafeBehaviour.trip_id, func.count(UnsafeBehaviour.id))
        .group_by(UnsafeBehaviour.trip_id)
        .all()
    )
    return {r[0]: int(r[1]) for r in results}


def _parse_week(value: str) -> Tuple[datetime, datetime]:
    try:
        year, week = value.split("-")
        start = datetime.fromisocalendar(int(year), int(week), 1)
        end = start + timedelta(days=7)
        return start, end
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid week format") from exc


def _placeholder_history(weeks: int = 8) -> List[Dict[str, str]]:
    today = date.today()
    hist = []
    for i in range(weeks):
        day = today - timedelta(weeks=i)
        iso = day.isocalendar()
        hist.append({"week": f"{iso[0]}-{iso[1]:02d}", "ubpk": 0.0})
    hist.reverse()
    return hist


def _paired_ttest(a: List[float], b: List[float]) -> Tuple[float, float]:
    n = min(len(a), len(b))
    if n < 2:
        raise ValueError("Not enough observations")
    diffs = [x - y for x, y in zip(a[:n], b[:n])]
    mean_diff = sum(diffs) / n
    var = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1)
    if var == 0:
        return mean_diff, 1.0
    t = mean_diff / (var ** 0.5 * (n ** -0.5))
    p = 2 * (1 - NormalDist().cdf(abs(t)))
    return mean_diff, p


@router.get("/trip/{trip_id}")
def trip_metrics(trip_id: UUID, db: Session = Depends(get_db)):
    distances = _trip_distances(db)
    behaviours = _trip_behaviour_counts(db)
    if trip_id not in distances:
        raise HTTPException(status_code=404, detail="Trip not found")
    driver_id, dist, _, start_time = distances[trip_id]
    count = behaviours.get(trip_id, 0)
    ubpk = (count / (dist / 1000)) if dist > 0 else 0.0
    return {
        "trip_id": trip_id,
        "driverProfileId": driver_id,
        "start_time": start_time,
        "behaviour_count": count,
        "distance_km": dist / 1000,
        "ubpk": ubpk,
    }


@router.get("/driver/{driver_id}")
def driver_weekly_metrics(
    driver_id: UUID,
    week: str | None = Query(None, description="ISO week YYYY-WW"),
    db: Session = Depends(get_db),
):
    if week is None:
        today = date.today()
        week = f"{today.isocalendar()[0]}-{today.isocalendar()[1]:02d}"
    start, end = _parse_week(week)
    distances = _trip_distances(db)
    behaviours = _trip_behaviour_counts(db)
    total_beh = 0
    total_dist = 0.0
    for trip_id, (d_id, dist, dt, _) in distances.items():
        if d_id == driver_id and dt and start <= dt < end:
            total_beh += behaviours.get(trip_id, 0)
            total_dist += dist
    if total_dist == 0:
        return {"driverProfileId": driver_id, "week": week, "ubpk": 0.0, "history": _placeholder_history()}
    ubpk = total_beh / (total_dist / 1000)
    return {"driverProfileId": driver_id, "week": week, "ubpk": ubpk}


@router.get("/driver/{driver_id}/improvement")
def driver_improvement(driver_id: UUID, db: Session = Depends(get_db)):
    today = date.today()
    this_week = f"{today.isocalendar()[0]}-{today.isocalendar()[1]:02d}"
    last_week_dt = today - timedelta(weeks=1)
    last_week = f"{last_week_dt.isocalendar()[0]}-{last_week_dt.isocalendar()[1]:02d}"
    start1, end1 = _parse_week(last_week)
    start2, end2 = _parse_week(this_week)
    distances = _trip_distances(db)
    behaviours = _trip_behaviour_counts(db)
    last_vals: List[float] = []
    this_vals: List[float] = []
    for trip_id, (d_id, dist, dt, _) in distances.items():
        if d_id != driver_id or not dt:
            continue
        ubpk = (behaviours.get(trip_id, 0) / (dist / 1000)) if dist > 0 else 0.0
        if start1 <= dt < end1:
            last_vals.append(ubpk)
        elif start2 <= dt < end2:
            this_vals.append(ubpk)
    if len(last_vals) < 1 or len(this_vals) < 1:
        raise HTTPException(status_code=400, detail="Not enough trips for t-test")
    mean_diff, p = _paired_ttest(this_vals, last_vals)
    return {"driverProfileId": driver_id, "p_value": p, "mean_difference": mean_diff}
