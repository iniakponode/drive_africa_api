from datetime import datetime, timedelta, date
from typing import Dict, Tuple, List, Optional
from uuid import UUID
from statistics import NormalDist
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from safedrive.database.db import get_db
from safedrive.models.trip import Trip
from safedrive.models.location import Location
from safedrive.models.unsafe_behaviour import UnsafeBehaviour
try:
    from safedrive.crud.unsafe_behaviour import unsafe_behaviour_crud
except Exception:  # pragma: no cover - optional dependency during tests
    class _DummyCRUD:
        def get_by_trip(self, *args, **kwargs):
            return []

        def get_by_driver_and_time(self, *args, **kwargs):
            return []

        def get_by_time(self, *args, **kwargs):
            return []

    unsafe_behaviour_crud = _DummyCRUD()
try:
    from safedrive.schemas.ubpk_metrics import (
        TripUBPKResponse,
        DriverWeekUBPKResponse,
        DriverImprovementResponse,
    )
except Exception:  # pragma: no cover - fallback for test stubs
    TripUBPKResponse = DriverWeekUBPKResponse = DriverImprovementResponse = dict

router = APIRouter()


def parse_iso_week(week: str) -> tuple[date, date]:
    year, week_no = week.split("-W")
    year, week_no = int(year), int(week_no)
    start = date.fromisocalendar(year, week_no, 1)
    return start, start + timedelta(days=7)


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


@router.get("/v2/trip/{trip_id}")
def trip_metrics_v2(trip_id: UUID, db: Session = Depends(get_db)):
    distances = _trip_distances(db)
    behaviours = _trip_behaviour_counts(db)
    if trip_id not in distances:
        raise HTTPException(status_code=404, detail="Trip not found")
    driver_id, dist, start_date, start_time = distances[trip_id]
    count = behaviours.get(trip_id, 0)
    dt = start_date or (datetime.fromtimestamp(start_time / 1000) if start_time else None)
    if dt:
        iy, iw, _ = dt.isocalendar()
        week = f"{iy}-W{iw:02d}"
        week_start, week_end = parse_iso_week(week)
    else:
        week = ""
        week_start, week_end = parse_iso_week(f"{date.today().isocalendar()[0]}-W{date.today().isocalendar()[1]:02d}")
    dist_km = dist / 1000
    ubpk = (count / dist_km) if dist_km > 0 else 0.0
    return {
        "tripId": str(trip_id),
        "driverProfileId": str(driver_id),
        "week": week,
        "weekStart": week_start,
        "weekEnd": week_end,
        "totalUnsafeCount": count,
        "distanceKm": dist_km,
        "ubpk": ubpk,
    }


@router.get("/v2/driver/{driver_id}")
def driver_weekly_metrics_v2(
    driver_id: UUID,
    week: str | None = Query(None, description="ISO week YYYY-WW"),
    db: Session = Depends(get_db),
):
    if week is None:
        today = date.today()
        week = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
    start, end = parse_iso_week(week)
    distances = _trip_distances(db)
    behaviours = _trip_behaviour_counts(db)
    values: List[float] = []
    for trip_id, (d_id, dist, dt, st) in distances.items():
        if d_id != driver_id:
            continue
        trip_date = dt or (datetime.fromtimestamp(st / 1000) if st else None)
        if trip_date and start <= trip_date < end:
            ubpk = behaviours.get(trip_id, 0) / (dist / 1000) if dist > 0 else 0.0
            values.append(ubpk)
    mean_val = sum(values) / len(values) if values else 0.0
    return {
        "driverProfileId": str(driver_id),
        "week": week,
        "weekStart": start,
        "weekEnd": end,
        "numTrips": len(values),
        "ubpkValues": values,
        "meanUBPK": mean_val,
    }


@router.get("/v2/driver/{driver_id}/improvement")
def driver_improvement_v2(
    driver_id: UUID,
    week: str | None = Query(None, description="ISO week YYYY-WW"),
    db: Session = Depends(get_db),
):
    if week is None:
        today = date.today()
        week = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
    start2, end2 = parse_iso_week(week)
    prev_start = start2 - timedelta(days=7)
    prev_end = start2
    prev_week = f"{prev_start.isocalendar()[0]}-W{prev_start.isocalendar()[1]:02d}"
    distances = _trip_distances(db)
    behaviours = _trip_behaviour_counts(db)
    last_vals: List[float] = []
    this_vals: List[float] = []
    for trip_id, (d_id, dist, dt, st) in distances.items():
        if d_id != driver_id:
            continue
        trip_date = dt or (datetime.fromtimestamp(st / 1000) if st else None)
        if not trip_date:
            continue
        ubpk = behaviours.get(trip_id, 0) / (dist / 1000) if dist > 0 else 0.0
        if prev_start <= trip_date < prev_end:
            last_vals.append(ubpk)
        elif start2 <= trip_date < end2:
            this_vals.append(ubpk)
    if len(last_vals) < 1 or len(this_vals) < 1:
        raise HTTPException(status_code=400, detail="Not enough trips for t-test")
    mean_diff, p = _paired_ttest(this_vals, last_vals)
    return {
        "driverProfileId": str(driver_id),
        "week": week,
        "previousWeek": prev_week,
        "previousWeekStart": prev_start,
        "previousWeekEnd": prev_end,
        "pValue": p,
        "meanDifference": mean_diff,
    }


@router.get("/trip/{trip_id}/ubpk", response_model=TripUBPKResponse)
def trip_ubpk(trip_id: UUID, db: Session = Depends(get_db)) -> TripUBPKResponse:
    events = unsafe_behaviour_crud.get_by_trip(db, trip_id)
    if not events:
        raise HTTPException(404, "No unsafe events for trip")
    distances = _trip_distances(db)
    if trip_id not in distances:
        raise HTTPException(404, "Trip not found or missing distance")
    driver_id, dist, _, _ = distances[trip_id]
    week_dt = datetime.fromtimestamp(events[0].timestamp / 1000)
    week = week_dt.isocalendar()[:2]
    week_str = f"{week[0]}-W{week[1]:02d}"
    start, end = parse_iso_week(week_str)
    dist_km = dist / 1000
    ubpk = len(events) / dist_km if dist_km > 0 else 0.0
    return TripUBPKResponse(
        tripId=str(trip_id),
        driverProfileId=str(driver_id),
        week=week_str,
        weekStart=start,
        weekEnd=end,
        totalUnsafeCount=len(events),
        distanceKm=dist_km,
        ubpk=ubpk,
    )


@router.get("/driver/{driver_id}", response_model=DriverWeekUBPKResponse)
def driver_week_metrics(
    driver_id: UUID,
    week: Optional[str] = Query(None, regex=r"^\\d{4}-W\\d{2}$"),
    db: Session = Depends(get_db),
) -> DriverWeekUBPKResponse:
    if week is None:
        today = date.today()
        year, wk, _ = today.isocalendar()
        week = f"{year}-W{wk:02d}"
    start, end = parse_iso_week(week)
    events = unsafe_behaviour_crud.get_by_driver_and_time(
        db,
        driver_id,
        datetime.combine(start, datetime.min.time()),
        datetime.combine(end, datetime.min.time()),
    )
    if not events:
        raise HTTPException(404, "No unsafe events for driver/week")
    trips: Dict[UUID, List[UnsafeBehaviour]] = {}
    for ev in events:
        trips.setdefault(ev.trip_id, []).append(ev)
    distances = _trip_distances(db)
    ubpk_vals: List[float] = []
    for t_id, evs in trips.items():
        info = distances.get(t_id)
        if info:
            dist_km = info[1] / 1000
            if dist_km > 0:
                ubpk_vals.append(len(evs) / dist_km)
    return DriverWeekUBPKResponse(
        driverProfileId=str(driver_id),
        week=week,
        weekStart=start,
        weekEnd=end,
        numTrips=len(ubpk_vals),
        ubpkValues=ubpk_vals,
        meanUBPK=sum(ubpk_vals) / len(ubpk_vals) if ubpk_vals else 0.0,
    )


@router.get("/driver/{driver_id}/improvement", response_model=DriverImprovementResponse)
def driver_improvement_endpoint(
    driver_id: UUID,
    week: Optional[str] = Query(None, regex=r"^\\d{4}-W\\d{2}$"),
    db: Session = Depends(get_db),
) -> DriverImprovementResponse:
    if week is None:
        today = date.today()
        year, wk, _ = today.isocalendar()
        week = f"{year}-W{wk:02d}"
    curr_start, curr_end = parse_iso_week(week)
    prev_start = curr_start - timedelta(days=7)
    prev_week = f"{prev_start.isocalendar()[0]}-W{prev_start.isocalendar()[1]:02d}"
    curr = driver_week_metrics(driver_id, week, db)
    prev = driver_week_metrics(driver_id, prev_week, db)
    from scipy.stats import ttest_rel

    _, p_value = ttest_rel(curr.ubpkValues, prev.ubpkValues)
    mean_diff = curr.meanUBPK - prev.meanUBPK
    return DriverImprovementResponse(
        driverProfileId=str(driver_id),
        week=week,
        previousWeek=prev_week,
        previousWeekStart=prev_start,
        previousWeekEnd=curr_start,
        pValue=p_value,
        meanDifference=mean_diff,
    )


@router.get("/trips", response_model=List[TripUBPKResponse])
def trips_weekly(
    week: Optional[str] = Query(None, regex=r"^\\d{4}-W\\d{2}$"),
    db: Session = Depends(get_db),
) -> List[TripUBPKResponse]:
    if week is None:
        today = date.today()
        year, wk, _ = today.isocalendar()
        week = f"{year}-W{wk:02d}"
    start, end = parse_iso_week(week)
    events = unsafe_behaviour_crud.get_by_time(
        db,
        datetime.combine(start, datetime.min.time()),
        datetime.combine(end, datetime.min.time()),
    )
    if not events:
        raise HTTPException(404, "No unsafe events that week")
    trip_counts: Dict[UUID, int] = {}
    for ev in events:
        trip_counts.setdefault(ev.trip_id, 0)
        trip_counts[ev.trip_id] += 1
    distances = _trip_distances(db)
    responses: List[TripUBPKResponse] = []
    for t_id, count in trip_counts.items():
        info = distances.get(t_id)
        if not info:
            continue
        driver_id, dist, _, _ = info
        dist_km = dist / 1000
        ubpk = count / dist_km if dist_km > 0 else 0.0
        responses.append(
            TripUBPKResponse(
                tripId=str(t_id),
                driverProfileId=str(driver_id),
                week=week,
                weekStart=start,
                weekEnd=end,
                totalUnsafeCount=count,
                distanceKm=dist_km,
                ubpk=ubpk,
            )
        )
    return responses
