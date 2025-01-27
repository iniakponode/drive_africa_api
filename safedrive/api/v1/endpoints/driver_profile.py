from fastapi import APIRouter, Depends, HTTPException
from pymysql import IntegrityError
from sqlalchemy.orm import Session, subqueryload
from typing import List
from uuid import UUID
from safedrive.database.db import get_db
from safedrive.models.driver_profile import DriverProfile
from safedrive.models.raw_sensor_data import RawSensorData
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

@router.post("/driver_profiles/", response_model=DriverProfileResponse)
def create_driver_profile(*, db: Session = Depends(get_db), profile_in: DriverProfileCreate) -> DriverProfileResponse:
    try:
        # Create the driver profile using the schema's driver_profile_id, email, and sync
        new_profile = driver_profile_crud.create(db=db, obj_in=profile_in)
        logger.info(f"DriverProfile created with ID: {new_profile.driverProfileId}")
        return DriverProfileResponse(
            driverProfileId=profile_in.driverProfileId,
            email=profile_in.email,
            sync=profile_in.sync
        )

    except IntegrityError as e:
        if 'Duplicate entry' in str(e.orig):
            logger.warning(f"Duplicate ID entry: {profile_in.email}")
            raise HTTPException(status_code=400, detail="ID already exists.")
        else:
            logger.error(f"Database integrity error: {str(e)}")
            raise HTTPException(status_code=500, detail="Database integrity error.")

    except Exception as e:
        logger.error(f"Unexpected error creating DriverProfile: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while creating the driver profile.")

@router.post("/driver_profiles/batch_create", response_model=List[DriverProfileResponse])
def batch_create_driver_profiles(
    *,
    db: Session = Depends(get_db),
    profiles_in: List[DriverProfileCreate]
) -> List[DriverProfileResponse]:
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

@router.get("/driver_profiles/{profile_id}", response_model=DriverProfileResponse)
def get_driver_profile(profile_id: UUID, db: Session = Depends(get_db)) -> DriverProfileResponse:
    profile = driver_profile_crud.get(db=db, id=profile_id)
    if not profile:
        logger.warning(f"DriverProfile with ID {profile_id} not found.")
        raise HTTPException(status_code=404, detail="Driver profile not found")
    logger.info(f"Retrieved DriverProfile with ID: {profile_id}")
    return DriverProfileResponse(driverProfileId=profile.id_uuid, email=profile.email, sync=profile.sync)

@router.get("/driver-profiles/by-profile_id/{email}", response_model=DriverProfileOut)
def get_driver_profile_by_email(
    email: str,
    db: Session = Depends(get_db),
    limit_sensor_data: int = 10
):
    driver_profile = (
        db.query(DriverProfile)
        .filter(DriverProfile.email == email)
        .options(subqueryload(DriverProfile.trips))  # load trips eagerly
        .one_or_none()
    )
    if not driver_profile:
        raise HTTPException(status_code=404, detail="DriverProfile not found.")

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
    limit_sensor_data: int = 10
):
    # 1) Get the driver profile + eager load trips
    driver_profile = (
        db.query(DriverProfile)
        .filter(DriverProfile.email == email)
        .options(subqueryload(DriverProfile.trips))  # optional eager load
        .one_or_none()
    )
    if not driver_profile:
        raise HTTPException(status_code=404, detail="DriverProfile not found.")

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

@router.get("/driver_profiles/", response_model=List[DriverProfileResponse])
def get_all_driver_profiles(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)) -> List[DriverProfileResponse]:
    profiles = driver_profile_crud.get_all(db=db, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(profiles)} DriverProfiles.")
    return [DriverProfileResponse(driverProfileId=profile.id_uuid, email=profile.email, sync=profile.sync) for profile in profiles]

@router.put("/driver_profiles/{profile_id}", response_model=DriverProfileResponse)
def update_driver_profile(profile_id: UUID, *, db: Session = Depends(get_db), profile_in: DriverProfileUpdate) -> DriverProfileResponse:
    profile = driver_profile_crud.get(db=db, id=profile_id)
    if not profile:
        logger.warning(f"DriverProfile with ID {profile_id} not found for update.")
        raise HTTPException(status_code=404, detail="Driver profile not found")
    updated_profile = driver_profile_crud.update(db=db, db_obj=profile, obj_in=profile_in)
    logger.info(f"Updated DriverProfile with ID: {profile_id}")
    return DriverProfileResponse(driverProfileId=updated_profile.id_uuid, email=updated_profile.email, sync=updated_profile.sync)

@router.delete("/driver_profiles/{profile_id}", response_model=DriverProfileResponse)
def delete_driver_profile(profile_id: UUID, db: Session = Depends(get_db)) -> DriverProfileResponse:
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
) -> DriverProfileResponse:
    """
    Deletes a driver profile (by email) and all related child records.
    Returns the deleted driver profile data.
    """
    deleted_profile = driver_profile_crud.delete_by_email_cascade(db, email)
    if not deleted_profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    # Convert the (already deleted) SQLAlchemy object to a response schema.
    return DriverProfileResponse.model_validate(deleted_profile)
