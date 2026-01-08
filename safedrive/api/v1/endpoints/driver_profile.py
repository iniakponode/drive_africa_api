from fastapi import APIRouter, Depends, HTTPException
from pymysql import IntegrityError
from sqlalchemy.orm import Session, subqueryload
from typing import List
from uuid import UUID
from safedrive.database.db import get_db
from safedrive.models.driver_profile import DriverProfile
from safedrive.models.raw_sensor_data import RawSensorData
from safedrive.core.security import ApiClientContext, Role, ensure_driver_access, require_roles
from safedrive.schemas.driver_profile import (
    DriverProfileCreate,
    DriverProfileOut,
    DriverProfileUpdate,
    DriverProfileResponse
)
from safedrive.crud.driver_profile import driver_profile_crud
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

@router.post("/driver_profiles/", response_model=DriverProfileResponse)
def create_driver_profile(
    *,
    db: Session = Depends(get_db),
    profile_in: DriverProfileCreate,
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> DriverProfileResponse:
    """
    Creates a new driver profile, or returns the existing one if there's a duplicate email.
    """
    ensure_driver_access(current_client, profile_in.driverProfileId)
    # No `try/except IntegrityError` block here, because CRUD function handles it.
    new_profile = driver_profile_crud.create(db=db, obj_in=profile_in)
    logger.info(f"DriverProfile created or retrieved with ID: {new_profile.driverProfileId}")

    return DriverProfileResponse(
        driverProfileId=new_profile.driverProfileId,
        email=new_profile.email,
        sync=new_profile.sync
    )


@router.post("/driver_profiles/batch_create", response_model=List[DriverProfileResponse])
def batch_create_driver_profiles(
    *,
    db: Session = Depends(get_db),
    profiles_in: List[DriverProfileCreate],
    current_client: ApiClientContext = Depends(require_roles(Role.ADMIN)),
) -> List[DriverProfileResponse]:
    """Create multiple driver profiles at once."""
    try:
        # Use bulk creation for all profiles at once
        new_profiles = driver_profile_crud.batch_create(db=db, objs_in=profiles_in)

        if not new_profiles:
            raise HTTPException(
                status_code=400,
                detail="No profiles were created due to errors or duplicates."
            )

        # Map the created profiles to the response model
        created_profiles = [
            DriverProfileResponse(
                driverProfileId=profile.driverProfileId,
                email=profile.email,
                sync=profile.sync
            )
            for profile in new_profiles
        ]

        return created_profiles

    except IntegrityError as e:
        # Handle database integrity issues if they arise during the bulk operation
        logger.error(f"Database integrity error during batch creation: {str(e)}")
        raise HTTPException(status_code=500, detail="Database integrity error.")
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error during batch creation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating driver profiles."
        )

@router.delete("/driver_profiles/batch_delete", status_code=204)
def batch_delete_driver_profiles(
    *,
    db: Session = Depends(get_db),
    ids: List[UUID],
    current_client: ApiClientContext = Depends(require_roles(Role.ADMIN)),
):
    """Delete multiple driver profiles at once."""
    deleted = driver_profile_crud.batch_delete(db=db, ids=ids)
    logger.info("Batch deleted %s DriverProfile records.", deleted)

@router.get("/driver_profiles/{profile_id}", response_model=DriverProfileResponse)
def get_driver_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> DriverProfileResponse:
    """Retrieve a driver profile by ID."""
    ensure_driver_access(current_client, profile_id)
    profile = driver_profile_crud.get(db=db, id=profile_id)
    if not profile:
        logger.warning(f"DriverProfile with ID {profile_id} not found.")
        raise HTTPException(status_code=404, detail="Driver profile not found")
    logger.info(f"Retrieved DriverProfile with ID: {profile_id}")
    return DriverProfileResponse(driverProfileId=profile.id_uuid, email=profile.email, sync=profile.sync)

@router.get("/driver-profiles/by-profile-id/{email}", response_model=DriverProfileOut)
def get_driver_profile_by_email(
    email: str,
    db: Session = Depends(get_db),
    limit_sensor_data: int = 5000,
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    """Get a driver profile and related trips by email."""
    driver_profile = (
        db.query(DriverProfile)
        .filter(DriverProfile.email == email)
        .options(subqueryload(DriverProfile.trips))  # load trips eagerly
        .one_or_none()
    )
    if not driver_profile:
        raise HTTPException(status_code=404, detail="DriverProfile not found.")
    ensure_driver_access(current_client, driver_profile.driverProfileId)

    # Now for each trip in driver_profile.trips, we can do:
    for trip in driver_profile.trips:
        # Use the custom property we defined
        data = (db.query(RawSensorData)
                  .filter(RawSensorData.trip_id == trip.id)
                  .limit(limit_sensor_data)
                  .all())
        trip.raw_sensor_data = data

    return driver_profile

@router.get("/driver-profiles/by-email/{email}", response_model=DriverProfileOut)
def get_driver_profile_by_email(
    email: str,
    db: Session = Depends(get_db),
    limit_sensor_data: int = 5000,
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    """Retrieve driver profile with limited sensor data by email."""
    # 1) Get the driver profile + eager load trips
    driver_profile = (
        db.query(DriverProfile)
        .filter(DriverProfile.email == email)
        .options(subqueryload(DriverProfile.trips))  # optional eager load
        .one_or_none()
    )
    if not driver_profile:
        raise HTTPException(status_code=404, detail="DriverProfile not found.")
    ensure_driver_access(current_client, driver_profile.driverProfileId)

    # 2) For each trip, limit raw sensor data
    for trip in driver_profile.trips:
        data = (
            db.query(RawSensorData)
            .filter(RawSensorData.trip_id == trip.id)
            .limit(limit_sensor_data)
            .all()
        )
        trip.raw_sensor_data = data

    # 3) Convert the SQLAlchemy object to your Pydantic model with nested trips
    #    Because `DriverProfileOut` -> `List[TripOut]` -> `List[RawSensorDataOut]`,
    #    you must ensure each of those Pydantic classes has `from_attributes = True`.
    return DriverProfileOut.model_validate(driver_profile)

@router.get("/driver-profile-by-email/{email}", response_model=DriverProfileResponse)
def get_driver_profile_by_email(
    email: str,
    db: Session = Depends(get_db),
    limit: int = 1,
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    """Return a minimal driver profile using an email lookup."""
    # 1) Get the driver profile + eager load trips
    driver_profile = (
        db.query(DriverProfile)
        .filter(DriverProfile.email == email)
        .first()
    )
    if not driver_profile:
        raise HTTPException(status_code=404, detail="DriverProfile not found.")
    ensure_driver_access(current_client, driver_profile.driverProfileId)

    return DriverProfileResponse.model_validate(driver_profile)

@router.get("/driver_profiles/", response_model=List[DriverProfileResponse])
def get_all_driver_profiles(
    skip: int = 0,
    limit: int = 5000,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> List[DriverProfileResponse]:
    """List all driver profiles."""
    if current_client.role == Role.ADMIN:
        profiles = driver_profile_crud.get_all(db=db, skip=skip, limit=limit)
    else:
        profiles = (
            db.query(DriverProfile)
            .filter(DriverProfile.driverProfileId == current_client.driver_profile_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    logger.info(f"Retrieved {len(profiles)} DriverProfiles.")
    return [DriverProfileResponse(driverProfileId=profile.id_uuid, email=profile.email, sync=profile.sync) for profile in profiles]

@router.put("/driver_profiles/{profile_id}", response_model=DriverProfileResponse)
def update_driver_profile(
    profile_id: UUID,
    *,
    db: Session = Depends(get_db),
    profile_in: DriverProfileUpdate,
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> DriverProfileResponse:
    """Update a driver profile."""
    ensure_driver_access(current_client, profile_id)
    profile = driver_profile_crud.get(db=db, id=profile_id)
    if not profile:
        logger.warning(f"DriverProfile with ID {profile_id} not found for update.")
        raise HTTPException(status_code=404, detail="Driver profile not found")
    updated_profile = driver_profile_crud.update(db=db, db_obj=profile, obj_in=profile_in)
    logger.info(f"Updated DriverProfile with ID: {profile_id}")
    return DriverProfileResponse(driverProfileId=updated_profile.id_uuid, email=updated_profile.email, sync=updated_profile.sync)

@router.delete("/driver_profiles/{profile_id}", response_model=DriverProfileResponse)
def delete_driver_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> DriverProfileResponse:
    """Delete a driver profile by ID."""
    ensure_driver_access(current_client, profile_id)
    profile = driver_profile_crud.get(db=db, id=profile_id)
    if not profile:
        logger.warning(f"DriverProfile with ID {profile_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="Driver profile not found")
    deleted_profile = driver_profile_crud.delete(db=db, id=profile_id)
    logger.info(f"Deleted DriverProfile with ID: {profile_id}")
    return DriverProfileResponse(driverProfileId=deleted_profile.id_uuid, email=deleted_profile.email, sync=deleted_profile.sync)

@router.delete("/driver_profiles/by-profile-id/{email}", response_model=DriverProfileResponse)
def delete_driver_profile_by_email(
    email: str,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> DriverProfileResponse:
    """
    Deletes a driver profile (by email) and all related child records.
    Returns the deleted driver profile data.
    """
    profile = driver_profile_crud.get_by_email(db, email)
    if not profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    ensure_driver_access(current_client, profile.driverProfileId)

    deleted_profile = driver_profile_crud.delete_by_email_cascade(db, email)
    if not deleted_profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    # Convert the (already deleted) SQLAlchemy object to a response schema.
    return DriverProfileResponse.model_validate(deleted_profile)
