from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session, joinedload

from safedrive.core.security import (
    ApiClientContext,
    Role,
    require_roles,
    get_current_client,
)
from safedrive.database.db import get_db
from safedrive.models.vehicle import Vehicle, DriverVehicleAssignment
from safedrive.models.driver_profile import DriverProfile
from safedrive.models.fleet import Fleet, VehicleGroup
from safedrive.models.trip import Trip
from safedrive.models.unsafe_behaviour import UnsafeBehaviour
from safedrive.models.location import Location
from safedrive.crud.vehicle import crud_vehicle, crud_driver_vehicle_assignment
from safedrive.schemas import vehicle as vehicle_schemas

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def _ensure_fleet_access(client: ApiClientContext, fleet_id: UUID) -> None:
    """Ensure the client has access to the specified fleet."""
    if client.role == Role.ADMIN:
        return
    if client.role == Role.FLEET_MANAGER and client.fleet_id == fleet_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Fleet access denied.",
    )


def _ensure_vehicle_access(db: Session, client: ApiClientContext, vehicle_id: UUID) -> Vehicle:
    """Ensure the client has access to the specified vehicle."""
    vehicle = crud_vehicle.get(db, vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    _ensure_fleet_access(client, vehicle.fleet_id)
    return vehicle


# --- Vehicle CRUD Endpoints ---

@router.get(
    "/vehicles",
    response_model=vehicle_schemas.VehicleListResponse,
    summary="List vehicles",
    description="Get a paginated list of vehicles with optional filtering"
)
def list_vehicles(
    fleet_id: Optional[UUID] = Query(None, description="Filter by fleet ID"),
    vehicle_group_id: Optional[UUID] = Query(None, description="Filter by vehicle group ID"),
    status: Optional[str] = Query(None, description="Filter by status (active, maintenance, retired)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=10, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER, Role.INSURANCE_PARTNER))
):
    """List vehicles with filters and pagination."""
    # Apply role-based filtering
    if client.role == Role.FLEET_MANAGER and client.fleet_id:
        fleet_id = client.fleet_id
    elif fleet_id:
        _ensure_fleet_access(client, fleet_id)

    skip = (page - 1) * page_size
    vehicles, total = crud_vehicle.get_multi(
        db,
        fleet_id=fleet_id,
        vehicle_group_id=vehicle_group_id,
        status=status,
        skip=skip,
        limit=page_size
    )

    # Convert to response format with primary driver info
    vehicle_responses = []
    for vehicle in vehicles:
        # Get primary driver
        primary_assignment = next(
            (a for a in vehicle.driver_assignments if a.is_primary and a.unassigned_at is None),
            None
        )

        vehicle_dict = {
            "id": vehicle.id_uuid,
            "fleet_id": vehicle.fleet_id,
            "vehicle_group_id": vehicle.vehicle_group_id,
            "license_plate": vehicle.license_plate,
            "vin": vehicle.vin,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "color": vehicle.color,
            "vehicle_type": vehicle.vehicle_type,
            "status": vehicle.status,
            "insurance_policy_number": vehicle.insurance_policy_number,
            "insurance_partner_id": vehicle.insurance_partner_id,
            "insurance_expiry_date": vehicle.insurance_expiry_date,
            "registration_expiry_date": vehicle.registration_expiry_date,
            "notes": vehicle.notes,
            "created_at": vehicle.created_at,
            "updated_at": vehicle.updated_at,
            "fleet": {"id": vehicle.fleet.id_uuid, "name": vehicle.fleet.name} if vehicle.fleet else None,
            "vehicle_group": {
                "id": vehicle.vehicle_group.id_uuid,
                "name": vehicle.vehicle_group.name
            } if vehicle.vehicle_group else None,
            "primary_driver": {
                "driver_profile_id": primary_assignment.driver_profile_id,
                "email": primary_assignment.driver_profile.email
            } if primary_assignment and primary_assignment.driver_profile else None
        }
        vehicle_responses.append(vehicle_schemas.VehicleResponse(**vehicle_dict))

    return vehicle_schemas.VehicleListResponse(
        vehicles=vehicle_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/vehicles/{vehicle_id}",
    response_model=vehicle_schemas.VehicleDetailResponse,
    summary="Get vehicle details",
    description="Get detailed information about a specific vehicle"
)
def get_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER, Role.DRIVER, Role.INSURANCE_PARTNER))
):
    """Get detailed vehicle information including assigned drivers, recent trips, and statistics."""
    vehicle = _ensure_vehicle_access(db, client, vehicle_id)

    # Get assigned drivers
    assignments = crud_driver_vehicle_assignment.get_vehicle_drivers(db, vehicle_id, active_only=True)
    assigned_drivers = []
    for assignment in assignments:
        if assignment.driver_profile:
            assigned_drivers.append(vehicle_schemas.VehicleDriverInfo(
                assignment_id=assignment.id_uuid,
                driver_profile_id=assignment.driver_profile_id,
                email=assignment.driver_profile.email,
                is_primary=assignment.is_primary,
                assigned_at=assignment.assigned_at
            ))

    # Get recent trips (last 10)
    recent_trips_query = (
        db.query(Trip)
        .filter(Trip.vehicle_id == vehicle_id.bytes)
        .order_by(Trip.start_time.desc())
        .limit(10)
    )
    recent_trips = []
    for trip in recent_trips_query:
        # Calculate distance from locations
        distance_km = (
            db.query(func.sum(Location.distance))
            .filter(Location.trip_id == trip.id)
            .scalar() or 0.0
        )
        # Get unsafe behaviour count
        unsafe_count = (
            db.query(func.count(UnsafeBehaviour.id))
            .filter(UnsafeBehaviour.trip_id == trip.id)
            .scalar() or 0
        )
        recent_trips.append(vehicle_schemas.TripSummary(
            id=trip.id_uuid,
            start_time=trip.start_time,
            end_time=trip.end_time,
            distance_km=distance_km,
            unsafe_count=unsafe_count
        ))

    # Calculate vehicle statistics
    stats_query = (
        db.query(
            func.count(Trip.id).label('total_trips'),
            func.sum(Location.distance).label('total_distance')
        )
        .outerjoin(Location, Location.trip_id == Trip.id)
        .filter(Trip.vehicle_id == vehicle_id.bytes)
        .first()
    )

    total_trips = stats_query.total_trips or 0
    total_distance_km = float(stats_query.total_distance or 0.0)

    # Get total unsafe behaviours
    total_unsafe = (
        db.query(func.count(UnsafeBehaviour.id))
        .join(Trip, Trip.id == UnsafeBehaviour.trip_id)
        .filter(Trip.vehicle_id == vehicle_id.bytes)
        .scalar() or 0
    )

    # Calculate UBPK
    ubpk = (total_unsafe / total_distance_km) if total_distance_km > 0 else 0.0

    stats = vehicle_schemas.VehicleStats(
        total_trips=total_trips,
        total_distance_km=total_distance_km,
        total_unsafe_behaviours=total_unsafe,
        ubpk=ubpk
    )

    # Get primary driver
    primary_assignment = next(
        (a for a in assignments if a.is_primary),
        None
    )

    # Build response
    response = vehicle_schemas.VehicleDetailResponse(
        id=vehicle.id_uuid,
        fleet_id=vehicle.fleet_id,
        vehicle_group_id=vehicle.vehicle_group_id,
        license_plate=vehicle.license_plate,
        vin=vehicle.vin,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        color=vehicle.color,
        vehicle_type=vehicle.vehicle_type,
        status=vehicle.status,
        insurance_policy_number=vehicle.insurance_policy_number,
        insurance_partner_id=vehicle.insurance_partner_id,
        insurance_expiry_date=vehicle.insurance_expiry_date,
        registration_expiry_date=vehicle.registration_expiry_date,
        notes=vehicle.notes,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
        fleet={"id": vehicle.fleet.id_uuid, "name": vehicle.fleet.name} if vehicle.fleet else None,
        vehicle_group={
            "id": vehicle.vehicle_group.id_uuid,
            "name": vehicle.vehicle_group.name
        } if vehicle.vehicle_group else None,
        primary_driver={
            "driver_profile_id": primary_assignment.driver_profile_id,
            "email": primary_assignment.driver_profile.email
        } if primary_assignment and primary_assignment.driver_profile else None,
        assigned_drivers=assigned_drivers,
        recent_trips=recent_trips,
        stats=stats
    )

    return response


@router.post(
    "/vehicles",
    response_model=vehicle_schemas.VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create vehicle",
    description="Create a new vehicle"
)
def create_vehicle(
    vehicle_in: vehicle_schemas.VehicleCreate,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER))
):
    """Create a new vehicle."""
    # Ensure client has access to the fleet
    _ensure_fleet_access(client, vehicle_in.fleet_id)

    # Verify fleet exists
    fleet = db.query(Fleet).filter(Fleet.id == vehicle_in.fleet_id.bytes).first()
    if not fleet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fleet not found"
        )

    # Verify vehicle group exists if provided
    if vehicle_in.vehicle_group_id:
        vehicle_group = db.query(VehicleGroup).filter(
            VehicleGroup.id == vehicle_in.vehicle_group_id.bytes
        ).first()
        if not vehicle_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle group not found"
            )

    vehicle = crud_vehicle.create(db, vehicle_in)

    return vehicle_schemas.VehicleResponse(
        id=vehicle.id_uuid,
        fleet_id=vehicle.fleet_id,
        vehicle_group_id=vehicle.vehicle_group_id,
        license_plate=vehicle.license_plate,
        vin=vehicle.vin,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        color=vehicle.color,
        vehicle_type=vehicle.vehicle_type,
        status=vehicle.status,
        insurance_policy_number=vehicle.insurance_policy_number,
        insurance_partner_id=vehicle.insurance_partner_id,
        insurance_expiry_date=vehicle.insurance_expiry_date,
        registration_expiry_date=vehicle.registration_expiry_date,
        notes=vehicle.notes,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
        fleet=None,
        vehicle_group=None,
        primary_driver=None
    )


@router.patch(
    "/vehicles/{vehicle_id}",
    response_model=vehicle_schemas.VehicleResponse,
    summary="Update vehicle",
    description="Update vehicle information"
)
def update_vehicle(
    vehicle_id: UUID,
    vehicle_in: vehicle_schemas.VehicleUpdate,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER))
):
    """Update a vehicle."""
    vehicle = _ensure_vehicle_access(db, client, vehicle_id)

    # Verify vehicle group if being updated
    if vehicle_in.vehicle_group_id:
        vehicle_group = db.query(VehicleGroup).filter(
            VehicleGroup.id == vehicle_in.vehicle_group_id.bytes
        ).first()
        if not vehicle_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle group not found"
            )

    vehicle = crud_vehicle.update(db, vehicle, vehicle_in)

    return vehicle_schemas.VehicleResponse(
        id=vehicle.id_uuid,
        fleet_id=vehicle.fleet_id,
        vehicle_group_id=vehicle.vehicle_group_id,
        license_plate=vehicle.license_plate,
        vin=vehicle.vin,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        color=vehicle.color,
        vehicle_type=vehicle.vehicle_type,
        status=vehicle.status,
        insurance_policy_number=vehicle.insurance_policy_number,
        insurance_partner_id=vehicle.insurance_partner_id,
        insurance_expiry_date=vehicle.insurance_expiry_date,
        registration_expiry_date=vehicle.registration_expiry_date,
        notes=vehicle.notes,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
        fleet=None,
        vehicle_group=None,
        primary_driver=None
    )


@router.delete(
    "/vehicles/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete vehicle",
    description="Soft delete a vehicle (sets status to retired)"
)
def delete_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER))
):
    """Soft delete a vehicle by setting status to 'retired'."""
    vehicle = _ensure_vehicle_access(db, client, vehicle_id)
    crud_vehicle.delete(db, vehicle_id)
    return None


@router.post(
    "/vehicles/batch",
    response_model=vehicle_schemas.VehicleBulkCreateResponse,
    summary="Batch create vehicles",
    description="Create multiple vehicles in a single request"
)
def batch_create_vehicles(
    bulk_in: vehicle_schemas.VehicleBulkCreate,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER))
):
    """Batch create vehicles."""
    # Validate fleet access for all vehicles
    for vehicle_item in bulk_in.vehicles:
        _ensure_fleet_access(client, vehicle_item.fleet_id)

    result = crud_vehicle.batch_create(db, bulk_in.vehicles)
    return vehicle_schemas.VehicleBulkCreateResponse(**result)


# --- Driver-Vehicle Assignment Endpoints ---

@router.post(
    "/vehicles/{vehicle_id}/drivers",
    response_model=vehicle_schemas.DriverVehicleAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign driver to vehicle",
    description="Assign a driver to a vehicle"
)
def assign_driver_to_vehicle(
    vehicle_id: UUID,
    assignment_in: vehicle_schemas.DriverVehicleAssignmentCreate,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER))
):
    """Assign a driver to a vehicle."""
    vehicle = _ensure_vehicle_access(db, client, vehicle_id)

    # Verify driver exists
    driver = db.query(DriverProfile).filter(
        DriverProfile.driverProfileId == assignment_in.driver_profile_id.bytes
    ).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    assignment = crud_driver_vehicle_assignment.assign_driver(
        db,
        driver_id=assignment_in.driver_profile_id,
        vehicle_id=vehicle_id,
        is_primary=assignment_in.is_primary
    )

    return vehicle_schemas.DriverVehicleAssignmentResponse(
        id=assignment.id_uuid,
        driver_profile_id=assignment.driver_profile_id,
        vehicle_id=assignment.vehicle_id,
        is_primary=assignment.is_primary,
        assigned_at=assignment.assigned_at,
        unassigned_at=assignment.unassigned_at
    )


@router.get(
    "/vehicles/{vehicle_id}/drivers",
    response_model=vehicle_schemas.VehicleDriversResponse,
    summary="List vehicle drivers",
    description="Get all drivers assigned to a vehicle"
)
def list_vehicle_drivers(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER, Role.INSURANCE_PARTNER))
):
    """List all drivers assigned to a vehicle."""
    vehicle = _ensure_vehicle_access(db, client, vehicle_id)

    assignments = crud_driver_vehicle_assignment.get_vehicle_drivers(db, vehicle_id, active_only=True)

    drivers = []
    for assignment in assignments:
        if assignment.driver_profile:
            drivers.append(vehicle_schemas.VehicleDriverInfo(
                assignment_id=assignment.id_uuid,
                driver_profile_id=assignment.driver_profile_id,
                email=assignment.driver_profile.email,
                is_primary=assignment.is_primary,
                assigned_at=assignment.assigned_at
            ))

    return vehicle_schemas.VehicleDriversResponse(drivers=drivers)


@router.delete(
    "/vehicles/{vehicle_id}/drivers/{driver_profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove driver from vehicle",
    description="Unassign a driver from a vehicle"
)
def remove_driver_from_vehicle(
    vehicle_id: UUID,
    driver_profile_id: UUID,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER))
):
    """Unassign a driver from a vehicle."""
    vehicle = _ensure_vehicle_access(db, client, vehicle_id)

    success = crud_driver_vehicle_assignment.unassign_driver(db, driver_profile_id, vehicle_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver-vehicle assignment not found"
        )

    return None


@router.get(
    "/drivers/{driver_profile_id}/vehicles",
    response_model=vehicle_schemas.DriverVehiclesResponse,
    summary="List driver vehicles",
    description="Get all vehicles assigned to a driver"
)
def list_driver_vehicles(
    driver_profile_id: UUID,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER, Role.DRIVER))
):
    """List all vehicles assigned to a driver."""
    # Verify driver exists
    driver = db.query(DriverProfile).filter(
        DriverProfile.driverProfileId == driver_profile_id.bytes
    ).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    # Check access (drivers can only see their own vehicles)
    if client.role == Role.DRIVER and client.driver_profile_id != driver_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    assignments = crud_driver_vehicle_assignment.get_driver_vehicles(db, driver_profile_id, active_only=True)

    vehicles = []
    for assignment in assignments:
        if assignment.vehicle:
            vehicles.append(vehicle_schemas.DriverVehicleInfo(
                id=assignment.vehicle.id_uuid,
                license_plate=assignment.vehicle.license_plate,
                make=assignment.vehicle.make,
                model=assignment.vehicle.model,
                is_primary=assignment.is_primary,
                assigned_at=assignment.assigned_at
            ))

    return vehicle_schemas.DriverVehiclesResponse(vehicles=vehicles)


# --- Vehicle-Trip Query Endpoints ---

@router.get(
    "/vehicles/{vehicle_id}/trips",
    response_model=vehicle_schemas.VehicleTripsResponse,
    summary="Get vehicle trips",
    description="Get trips for a specific vehicle"
)
def get_vehicle_trips(
    vehicle_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Filter trips after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter trips before this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=10, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles([Role.ADMIN, Role.FLEET_MANAGER, Role.INSURANCE_PARTNER]))
):
    """Get trips for a vehicle with optional date filtering and pagination."""
    vehicle = _ensure_vehicle_access(db, client, vehicle_id)

    # Build query
    query = db.query(Trip).filter(Trip.vehicle_id == vehicle_id.bytes)

    # Apply date filters
    if start_date:
        start_timestamp_ms = int(start_date.timestamp() * 1000)
        query = query.filter(Trip.start_time >= start_timestamp_ms)
    if end_date:
        end_timestamp_ms = int(end_date.timestamp() * 1000)
        query = query.filter(Trip.start_time <= end_timestamp_ms)

    # Get total count
    total = query.count()

    # Apply pagination
    skip = (page - 1) * page_size
    trips = query.order_by(Trip.start_time.desc()).offset(skip).limit(page_size).all()

    # Build response
    trip_summaries = []
    for trip in trips:
        # Calculate distance
        distance_km = (
            db.query(func.sum(Location.distance))
            .filter(Location.trip_id == trip.id)
            .scalar() or 0.0
        )
        # Get unsafe count
        unsafe_count = (
            db.query(func.count(UnsafeBehaviour.id))
            .filter(UnsafeBehaviour.trip_id == trip.id)
            .scalar() or 0
        )
        trip_summaries.append(vehicle_schemas.TripSummary(
            id=trip.id_uuid,
            start_time=trip.start_time,
            end_time=trip.end_time,
            distance_km=distance_km,
            unsafe_count=unsafe_count
        ))

    return vehicle_schemas.VehicleTripsResponse(
        trips=trip_summaries,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/vehicles/{vehicle_id}/stats",
    response_model=vehicle_schemas.VehicleStatsResponse,
    summary="Get vehicle statistics",
    description="Get statistical information about vehicle usage"
)
def get_vehicle_stats(
    vehicle_id: UUID,
    period: str = Query("all", regex="^(day|week|month|all)$", description="Time period for statistics"),
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER, Role.INSURANCE_PARTNER))
):
    """Get statistics for a vehicle."""
    vehicle = _ensure_vehicle_access(db, client, vehicle_id)

    # Calculate date filter based on period
    start_date = None
    if period == "day":
        start_date = datetime.utcnow() - timedelta(days=1)
    elif period == "week":
        start_date = datetime.utcnow() - timedelta(weeks=1)
    elif period == "month":
        start_date = datetime.utcnow() - timedelta(days=30)

    # Build trip query
    trip_query = db.query(Trip).filter(Trip.vehicle_id == vehicle_id.bytes)
    if start_date:
        start_timestamp_ms = int(start_date.timestamp() * 1000)
        trip_query = trip_query.filter(Trip.start_time >= start_timestamp_ms)

    # Get trip IDs for the period
    trip_ids = [trip.id for trip in trip_query.all()]

    # Calculate statistics
    total_trips = len(trip_ids)

    if total_trips > 0:
        # Total distance
        total_distance_km = float(
            db.query(func.sum(Location.distance))
            .filter(Location.trip_id.in_(trip_ids))
            .scalar() or 0.0
        )

        # Total duration in hours
        duration_query = (
            db.query(
                func.sum((Trip.end_time - Trip.start_time) / 1000 / 3600)
            )
            .filter(
                and_(
                    Trip.id.in_(trip_ids),
                    Trip.end_time.isnot(None)
                )
            )
            .scalar()
        )
        total_duration_hours = float(duration_query or 0.0)

        # Total unsafe behaviours
        total_unsafe = (
            db.query(func.count(UnsafeBehaviour.id))
            .filter(UnsafeBehaviour.trip_id.in_(trip_ids))
            .scalar() or 0
        )

        # UBPK
        ubpk = (total_unsafe / total_distance_km) if total_distance_km > 0 else 0.0

        # Unique drivers
        unique_drivers = (
            db.query(func.count(func.distinct(Trip.driverProfileId)))
            .filter(Trip.id.in_(trip_ids))
            .scalar() or 0
        )

        # Busiest driver
        busiest_query = (
            db.query(
                Trip.driverProfileId,
                func.count(Trip.id).label('trip_count')
            )
            .filter(Trip.id.in_(trip_ids))
            .group_by(Trip.driverProfileId)
            .order_by(desc('trip_count'))
            .first()
        )

        busiest_driver = None
        if busiest_query:
            driver = db.query(DriverProfile).filter(
                DriverProfile.driverProfileId == busiest_query.driverProfileId
            ).first()
            if driver:
                busiest_driver = vehicle_schemas.BusiestDriver(
                    driver_profile_id=driver.driverProfileId,
                    email=driver.email,
                    trip_count=busiest_query.trip_count
                )
    else:
        total_distance_km = 0.0
        total_duration_hours = 0.0
        total_unsafe = 0
        ubpk = 0.0
        unique_drivers = 0
        busiest_driver = None

    return vehicle_schemas.VehicleStatsResponse(
        vehicle_id=vehicle_id,
        period=period,
        total_trips=total_trips,
        total_distance_km=total_distance_km,
        total_duration_hours=total_duration_hours,
        total_unsafe_behaviours=total_unsafe,
        ubpk=ubpk,
        unique_drivers=unique_drivers,
        busiest_driver=busiest_driver
    )
