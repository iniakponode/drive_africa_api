from datetime import datetime, timedelta
import calendar
from typing import Dict, Iterable, List, Optional, Set, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from safedrive.core.security import (
    ApiClientContext,
    Role,
    ensure_driver_access,
    require_roles,
    require_roles_or_jwt,
)
from safedrive.database.db import get_db
from safedrive.models.fleet import DriverFleetAssignment
from safedrive.models.insurance_partner import InsurancePartnerDriver
from safedrive.models.location import Location
from safedrive.models.raw_sensor_data import RawSensorData
from safedrive.models.trip import Trip
from safedrive.models.unsafe_behaviour import UnsafeBehaviour
from safedrive.schemas.analytics import (
    BadDaysResponse,
    BadDaysSummary,
    BadDaysThresholds,
    DriverKpiResponse,
    DriverKpiSummary,
    DriverPeriodUBPK,
    DriverUBPKSeriesResponse,
    LeaderboardEntry,
    LeaderboardResponse,
)

router = APIRouter()

LEADERBOARD_WINDOWS = {"day": 1, "week": 7, "month": 30}
TREND_WINDOWS = {"day": 60, "week": 180, "month": 365}
BAD_DAY_WINDOWS = {"day": 60, "week": 180, "month": 365}
SUPPORTED_PERIODS = {"day", "week", "month"}


def _cohort_from_fleet(db: Session, fleet_id: UUID) -> Set[UUID]:
    rows = (
        db.query(DriverFleetAssignment.driverProfileId)
        .filter(DriverFleetAssignment.fleet_id == fleet_id)
        .all()
    )
    return {row[0] for row in rows}


def _cohort_from_partner(db: Session, partner_id: UUID) -> Set[UUID]:
    rows = (
        db.query(InsurancePartnerDriver.driverProfileId)
        .filter(InsurancePartnerDriver.partner_id == partner_id)
        .all()
    )
    return {row[0] for row in rows}


def _resolve_cohort(
    db: Session,
    current_client: ApiClientContext,
    fleet_id: Optional[UUID],
    partner_id: Optional[UUID],
    require_scope: bool,
) -> Tuple[Optional[Set[UUID]], str]:
    if current_client.role == Role.FLEET_MANAGER:
        if fleet_id and fleet_id != current_client.fleet_id:
            raise HTTPException(status_code=403, detail="Fleet scope mismatch.")
        if not current_client.fleet_id:
            raise HTTPException(status_code=403, detail="Fleet scope missing.")
        return _cohort_from_fleet(db, current_client.fleet_id), "fleet"
    if current_client.role == Role.INSURANCE_PARTNER:
        if partner_id and partner_id != current_client.insurance_partner_id:
            raise HTTPException(status_code=403, detail="Partner scope mismatch.")
        if not current_client.insurance_partner_id:
            raise HTTPException(status_code=403, detail="Partner scope missing.")
        return (
            _cohort_from_partner(db, current_client.insurance_partner_id),
            "insurance_partner",
        )
    if current_client.role == Role.DRIVER:
        if not current_client.driver_profile_id:
            raise HTTPException(status_code=403, detail="Driver scope missing.")
        assignment = (
            db.query(DriverFleetAssignment)
            .filter(DriverFleetAssignment.driverProfileId == current_client.driver_profile_id)
            .order_by(DriverFleetAssignment.assigned_at.desc())
            .first()
        )
        if assignment:
            return _cohort_from_fleet(db, assignment.fleet_id), "fleet"
        mapping = (
            db.query(InsurancePartnerDriver)
            .filter(InsurancePartnerDriver.driverProfileId == current_client.driver_profile_id)
            .first()
        )
        if mapping:
            return _cohort_from_partner(db, mapping.partner_id), "insurance_partner"
        return {current_client.driver_profile_id}, "self"

    if fleet_id:
        return _cohort_from_fleet(db, fleet_id), "fleet"
    if partner_id:
        return _cohort_from_partner(db, partner_id), "insurance_partner"
    if require_scope:
        raise HTTPException(
            status_code=400,
            detail="fleetId or insurancePartnerId is required for this endpoint.",
        )
    return None, "all"


def _trip_start_dt(trip: Trip) -> Optional[datetime]:
    if trip.start_date:
        return trip.start_date
    if trip.start_time:
        return datetime.utcfromtimestamp(trip.start_time / 1000.0)
    return None


def _resolve_window(
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    default_days: int,
) -> Tuple[datetime, datetime]:
    end = end_date or datetime.utcnow()
    start = start_date or (end - timedelta(days=default_days))
    return start, end


def _period_start(value: datetime, period: str) -> datetime:
    if period == "day":
        return datetime(value.year, value.month, value.day)
    if period == "week":
        day = value.date()
        week_start = day - timedelta(days=day.weekday())
        return datetime.combine(week_start, datetime.min.time())
    if period == "month":
        return datetime(value.year, value.month, 1)
    raise ValueError("Unsupported period")


def _period_end(value: datetime, period: str) -> datetime:
    if period == "day":
        return value + timedelta(days=1)
    if period == "week":
        return value + timedelta(days=7)
    if period == "month":
        last_day = calendar.monthrange(value.year, value.month)[1]
        return datetime(value.year, value.month, last_day) + timedelta(days=1)
    raise ValueError("Unsupported period")


def _trip_stats(db: Session, trip_ids: Iterable[UUID]) -> Tuple[Dict[UUID, float], Dict[UUID, int]]:
    trip_ids = list(trip_ids)
    if not trip_ids:
        return {}, {}
    distances = dict(
        db.query(
            Trip.id,
            func.coalesce(func.sum(Location.distance), 0.0),
        )
        .outerjoin(RawSensorData, RawSensorData.trip_id == Trip.id)
        .outerjoin(Location, Location.id == RawSensorData.location_id)
        .filter(Trip.id.in_(trip_ids))
        .group_by(Trip.id)
        .all()
    )
    unsafe_counts = dict(
        db.query(UnsafeBehaviour.trip_id, func.count(UnsafeBehaviour.id))
        .filter(UnsafeBehaviour.trip_id.in_(trip_ids))
        .group_by(UnsafeBehaviour.trip_id)
        .all()
    )
    return distances, unsafe_counts


def _filter_trips_by_window(
    trips: Iterable[Trip],
    start_date: datetime,
    end_date: datetime,
) -> List[Trip]:
    selected: List[Trip] = []
    for trip in trips:
        start_dt = _trip_start_dt(trip)
        if not start_dt:
            continue
        if start_dt < start_date or start_dt > end_date:
            continue
        selected.append(trip)
    return selected


def _aggregate_driver_window(
    trips: List[Trip],
    distances: Dict[UUID, float],
    unsafe_counts: Dict[UUID, int],
) -> Dict[UUID, Dict[str, float]]:
    summary: Dict[UUID, Dict[str, float]] = {}
    for trip in trips:
        driver_id = trip.driverProfileId
        summary.setdefault(driver_id, {"distance_m": 0.0, "unsafe_count": 0})
        summary[driver_id]["distance_m"] += float(distances.get(trip.id, 0.0) or 0.0)
        summary[driver_id]["unsafe_count"] += int(unsafe_counts.get(trip.id, 0))
    return summary


def _period_series_by_driver(
    trips: List[Trip],
    distances: Dict[UUID, float],
    unsafe_counts: Dict[UUID, int],
    period: str,
) -> Dict[UUID, Dict[datetime, Dict[str, float]]]:
    series: Dict[UUID, Dict[datetime, Dict[str, float]]] = {}
    for trip in trips:
        start_dt = _trip_start_dt(trip)
        if not start_dt:
            continue
        bucket_start = _period_start(start_dt, period)
        driver_id = trip.driverProfileId
        series.setdefault(driver_id, {})
        series[driver_id].setdefault(
            bucket_start, {"distance_m": 0.0, "unsafe_count": 0}
        )
        payload = series[driver_id][bucket_start]
        payload["distance_m"] += float(distances.get(trip.id, 0.0) or 0.0)
        payload["unsafe_count"] += int(unsafe_counts.get(trip.id, 0))
    return series


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = int((len(values) - 1) * pct)
    return float(values[idx])


def _build_leaderboard_entries(
    driver_stats: Dict[UUID, Dict[str, float]],
) -> List[LeaderboardEntry]:
    entries: List[LeaderboardEntry] = []
    for driver_id, payload in driver_stats.items():
        distance_km = payload["distance_m"] / 1000.0
        unsafe_count = int(payload["unsafe_count"])
        ubpk = (unsafe_count / distance_km) if distance_km > 0 else 0.0
        entries.append(
            LeaderboardEntry(
                driverProfileId=driver_id,
                ubpk=ubpk,
                unsafe_count=unsafe_count,
                distance_km=distance_km,
            )
        )
    entries.sort(key=lambda item: item.ubpk)
    return entries


def _bad_days_summary(
    trips: List[Trip],
    distances: Dict[UUID, float],
    unsafe_counts: Dict[UUID, int],
    period: str,
    window_days: int,
) -> Tuple[Dict[UUID, Tuple[int, Optional[float]]], float]:
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=window_days)
    filtered = _filter_trips_by_window(trips, start_date, end_date)
    series_by_driver = _period_series_by_driver(
        filtered, distances, unsafe_counts, period
    )
    deltas: List[float] = []
    per_driver: Dict[UUID, Tuple[int, Optional[float]]] = {}

    for driver_id, buckets in series_by_driver.items():
        items = sorted(buckets.items(), key=lambda item: item[0])
        ubpks = []
        for bucket_start, payload in items:
            distance_km = payload["distance_m"] / 1000.0
            unsafe_count = int(payload["unsafe_count"])
            ubpk = (unsafe_count / distance_km) if distance_km > 0 else 0.0
            ubpks.append((bucket_start, ubpk))
        driver_deltas: List[float] = []
        for idx in range(1, len(ubpks)):
            delta = ubpks[idx][1] - ubpks[idx - 1][1]
            driver_deltas.append(delta)
            deltas.append(delta)
        last_delta = driver_deltas[-1] if driver_deltas else None
        per_driver[driver_id] = (0, last_delta)

    threshold = _percentile(deltas, 0.75)
    threshold = max(threshold, 0.0)

    for driver_id, buckets in series_by_driver.items():
        items = sorted(buckets.items(), key=lambda item: item[0])
        ubpks = []
        for bucket_start, payload in items:
            distance_km = payload["distance_m"] / 1000.0
            unsafe_count = int(payload["unsafe_count"])
            ubpk = (unsafe_count / distance_km) if distance_km > 0 else 0.0
            ubpks.append(ubpk)
        bad_count = 0
        for idx in range(1, len(ubpks)):
            delta = ubpks[idx] - ubpks[idx - 1]
            if delta > threshold:
                bad_count += 1
        last_delta = per_driver.get(driver_id, (0, None))[1]
        per_driver[driver_id] = (bad_count, last_delta)

    return per_driver, threshold


@router.get("/analytics/leaderboard", response_model=LeaderboardResponse)
def leaderboard(
    period: str = Query("week"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    limit: int = Query(5, ge=1, le=50),
    fleet_id: Optional[UUID] = Query(None, alias="fleetId"),
    insurance_partner_id: Optional[UUID] = Query(None, alias="insurancePartnerId"),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(
            Role.ADMIN,
            Role.RESEARCHER,
            Role.FLEET_MANAGER,
            Role.INSURANCE_PARTNER,
            Role.DRIVER,
        )
    ),
) -> LeaderboardResponse:
    period = period.lower()
    if period not in SUPPORTED_PERIODS:
        raise HTTPException(status_code=400, detail="Invalid period value.")

    cohort_ids, _ = _resolve_cohort(
        db, current_client, fleet_id, insurance_partner_id, require_scope=False
    )
    cohort_ids = cohort_ids or set()

    window_days = LEADERBOARD_WINDOWS[period]
    start_dt, end_dt = _resolve_window(start_date, end_date, window_days)

    # Optimize: Only fetch trips within the required window (+ buffer for date ranges)
    cutoff_date = (start_dt or datetime.utcnow()) - timedelta(days=window_days + 30)
    
    trips_query = db.query(Trip).filter(Trip.start_time >= cutoff_date)
    if cohort_ids:
        trips_query = trips_query.filter(Trip.driverProfileId.in_(cohort_ids))
    trips = _filter_trips_by_window(trips_query.all(), start_dt, end_dt)
    trip_ids = [trip.id for trip in trips]
    distances, unsafe_counts = _trip_stats(db, trip_ids)
    driver_stats = _aggregate_driver_window(trips, distances, unsafe_counts)
    entries = _build_leaderboard_entries(driver_stats)

    return LeaderboardResponse(
        period=period,
        start_date=start_dt,
        end_date=end_dt,
        total_drivers=len(entries),
        best=entries[:limit],
        worst=list(reversed(entries[-limit:])) if entries else [],
    )


@router.get("/analytics/driver-ubpk", response_model=DriverUBPKSeriesResponse)
def driver_ubpk_series(
    period: str = Query("week"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    driver_profile_id: Optional[UUID] = Query(None, alias="driverProfileId"),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(
            Role.ADMIN,
            Role.RESEARCHER,
            Role.FLEET_MANAGER,
            Role.INSURANCE_PARTNER,
            Role.DRIVER,
        )
    ),
) -> DriverUBPKSeriesResponse:
    period = period.lower()
    if period not in SUPPORTED_PERIODS:
        raise HTTPException(status_code=400, detail="Invalid period value.")

    if current_client.role == Role.DRIVER:
        driver_id = current_client.driver_profile_id
    else:
        if not driver_profile_id:
            raise HTTPException(
                status_code=400, detail="driverProfileId is required."
            )
        ensure_driver_access(current_client, driver_profile_id)
        driver_id = driver_profile_id

    if not driver_id:
        raise HTTPException(status_code=403, detail="Driver scope missing.")

    window_days = TREND_WINDOWS[period]
    start_dt, end_dt = _resolve_window(start_date, end_date, window_days)

    trips = (
        db.query(Trip)
        .filter(Trip.driverProfileId == driver_id)
        .all()
    )
    trips = _filter_trips_by_window(trips, start_dt, end_dt)
    distances, unsafe_counts = _trip_stats(db, [trip.id for trip in trips])
    series_by_driver = _period_series_by_driver(trips, distances, unsafe_counts, period)
    buckets = series_by_driver.get(driver_id, {})
    series: List[DriverPeriodUBPK] = []
    for bucket_start, payload in sorted(buckets.items(), key=lambda item: item[0]):
        distance_km = payload["distance_m"] / 1000.0
        unsafe_count = int(payload["unsafe_count"])
        ubpk = (unsafe_count / distance_km) if distance_km > 0 else 0.0
        series.append(
            DriverPeriodUBPK(
                period_start=bucket_start,
                period_end=_period_end(bucket_start, period),
                ubpk=ubpk,
                unsafe_count=unsafe_count,
                distance_km=distance_km,
            )
        )

    return DriverUBPKSeriesResponse(
        driverProfileId=driver_id,
        period=period,
        start_date=start_dt,
        end_date=end_dt,
        series=series,
    )


@router.get("/analytics/bad-days", response_model=BadDaysResponse)
def bad_days(
    fleet_id: Optional[UUID] = Query(None, alias="fleetId"),
    insurance_partner_id: Optional[UUID] = Query(None, alias="insurancePartnerId"),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(
            Role.ADMIN,
            Role.RESEARCHER,
            Role.FLEET_MANAGER,
            Role.INSURANCE_PARTNER,
            Role.DRIVER,
        )
    ),
) -> BadDaysResponse:
    cohort_ids, _ = _resolve_cohort(
        db, current_client, fleet_id, insurance_partner_id, require_scope=False
    )
    cohort_ids = cohort_ids or set()

    # Only fetch trips from the last year (max window needed for monthly analysis)
    cutoff_date = datetime.utcnow() - timedelta(days=BAD_DAY_WINDOWS["month"])
    
    trips_query = db.query(Trip).filter(Trip.start_time >= cutoff_date)
    if cohort_ids:
        trips_query = trips_query.filter(Trip.driverProfileId.in_(cohort_ids))
    trips = trips_query.all()
    distances, unsafe_counts = _trip_stats(db, [trip.id for trip in trips])

    day_summary, day_threshold = _bad_days_summary(
        trips, distances, unsafe_counts, "day", BAD_DAY_WINDOWS["day"]
    )
    week_summary, week_threshold = _bad_days_summary(
        trips, distances, unsafe_counts, "week", BAD_DAY_WINDOWS["week"]
    )
    month_summary, month_threshold = _bad_days_summary(
        trips, distances, unsafe_counts, "month", BAD_DAY_WINDOWS["month"]
    )

    driver_ids = set(day_summary.keys()) | set(week_summary.keys()) | set(month_summary.keys())
    drivers: List[BadDaysSummary] = []
    for driver_id in sorted(driver_ids, key=lambda item: str(item)):
        day_payload = day_summary.get(driver_id, (0, None))
        week_payload = week_summary.get(driver_id, (0, None))
        month_payload = month_summary.get(driver_id, (0, None))
        drivers.append(
            BadDaysSummary(
                driverProfileId=driver_id,
                bad_days=day_payload[0],
                bad_weeks=week_payload[0],
                bad_months=month_payload[0],
                last_day_delta=day_payload[1],
                last_week_delta=week_payload[1],
                last_month_delta=month_payload[1],
            )
        )

    return BadDaysResponse(
        thresholds=BadDaysThresholds(
            day=day_threshold,
            week=week_threshold,
            month=month_threshold,
        ),
        drivers=drivers,
    )


@router.get("/analytics/driver-kpis", response_model=DriverKpiResponse)
def driver_kpis(
    period: str = Query("week"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    fleet_id: Optional[UUID] = Query(None, alias="fleetId"),
    insurance_partner_id: Optional[UUID] = Query(None, alias="insurancePartnerId"),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(
            Role.ADMIN,
            Role.RESEARCHER,
            Role.FLEET_MANAGER,
            Role.INSURANCE_PARTNER,
            Role.DRIVER,
        )
    ),
) -> DriverKpiResponse:
    period = period.lower()
    if period not in SUPPORTED_PERIODS:
        raise HTTPException(status_code=400, detail="Invalid period value.")

    cohort_ids, _ = _resolve_cohort(
        db, current_client, fleet_id, insurance_partner_id, require_scope=False
    )
    cohort_ids = cohort_ids or set()

    window_days = LEADERBOARD_WINDOWS[period]
    start_dt, end_dt = _resolve_window(start_date, end_date, window_days)

    # Optimize: Only fetch trips within a reasonable range (max bad-days window + leaderboard window)
    cutoff_date = datetime.utcnow() - timedelta(days=max(BAD_DAY_WINDOWS["month"], window_days) + 30)
    
    trips_query = db.query(Trip).filter(Trip.start_time >= cutoff_date)
    if cohort_ids:
        trips_query = trips_query.filter(Trip.driverProfileId.in_(cohort_ids))
    trips = _filter_trips_by_window(trips_query.all(), start_dt, end_dt)
    distances, unsafe_counts = _trip_stats(db, [trip.id for trip in trips])
    driver_stats = _aggregate_driver_window(trips, distances, unsafe_counts)

    day_summary, _ = _bad_days_summary(
        trips, distances, unsafe_counts, "day", BAD_DAY_WINDOWS["day"]
    )
    week_summary, _ = _bad_days_summary(
        trips, distances, unsafe_counts, "week", BAD_DAY_WINDOWS["week"]
    )
    month_summary, _ = _bad_days_summary(
        trips, distances, unsafe_counts, "month", BAD_DAY_WINDOWS["month"]
    )

    drivers: List[DriverKpiSummary] = []
    for driver_id, payload in driver_stats.items():
        distance_km = payload["distance_m"] / 1000.0
        unsafe_count = int(payload["unsafe_count"])
        ubpk = (unsafe_count / distance_km) if distance_km > 0 else 0.0
        drivers.append(
            DriverKpiSummary(
                driverProfileId=driver_id,
                ubpk=ubpk,
                unsafe_count=unsafe_count,
                distance_km=distance_km,
                bad_days=day_summary.get(driver_id, (0, None))[0],
                bad_weeks=week_summary.get(driver_id, (0, None))[0],
                bad_months=month_summary.get(driver_id, (0, None))[0],
            )
        )

    drivers.sort(key=lambda item: item.ubpk)

    return DriverKpiResponse(
        period=period,
        start_date=start_dt,
        end_date=end_dt,
        drivers=drivers,
    )
