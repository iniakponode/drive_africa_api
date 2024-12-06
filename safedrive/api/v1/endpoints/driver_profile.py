from fastapi import APIRouter, Depends, HTTPException
from pymysql import IntegrityError
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from safedrive.database.db import get_db
from safedrive.schemas.driver_profile import (
    DriverProfileCreate,
    DriverProfileUpdate,
    DriverProfileResponse
)
from safedrive.crud.driver_profile import driver_profile_crud
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/driver_profiles/", response_model=DriverProfileResponse)
def create_driver_profile(*, db: Session = Depends(get_db), profile_in: DriverProfileCreate) -> DriverProfileResponse:
     """
    Creates a new driver profile.
    - **profile_in**: Data for creating the driver profile.
    """
     try:
            new_profile = driver_profile_crud.create(db=db, obj_in=profile_in)
            logger.info(f"DriverProfile created with ID: {new_profile.id_uuid}")
            return DriverProfileResponse(driver_profile_id=new_profile.id_uuid, **profile_in.model_dump())
        
     except IntegrityError as e:
            # Check if the IntegrityError is due to a duplicate email entry
            if 'Duplicate entry' in str(e.orig):
                logger.warning(f"Duplicate ID entry: {profile_in.email}")
                raise HTTPException(status_code=400, detail="ID already exists.")
            else:
                logger.error(f"Database integrity error: {str(e)}")
                raise HTTPException(status_code=500, detail="Database integrity error.")
        
     except Exception as e:
            logger.error(f"Unexpected error creating DriverProfile: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while creating the driver profile.")

@router.get("/driver_profiles/{profile_id}", response_model=DriverProfileResponse)
def get_driver_profile(profile_id: UUID, db: Session = Depends(get_db)) -> DriverProfileResponse:
    profile = driver_profile_crud.get(db=db, id=profile_id)
    if not profile:
        logger.warning(f"DriverProfile with ID {profile_id} not found.")
        raise HTTPException(status_code=404, detail="Driver profile not found")
    logger.info(f"Retrieved DriverProfile with ID: {profile_id}")
    return DriverProfileResponse(driver_profile_id=profile.id_uuid, email=profile.email, sync=profile.sync)

@router.get("/driver_profiles/", response_model=List[DriverProfileResponse])
def get_all_driver_profiles(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)) -> List[DriverProfileResponse]:
    profiles = driver_profile_crud.get_all(db=db, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(profiles)} DriverProfiles.")
    return [DriverProfileResponse(driver_profile_id=profile.id_uuid, email=profile.email, sync=profile.sync) for profile in profiles]

@router.put("/driver_profiles/{profile_id}", response_model=DriverProfileResponse)
def update_driver_profile(profile_id: UUID, *, db: Session = Depends(get_db), profile_in: DriverProfileUpdate) -> DriverProfileResponse:
    profile = driver_profile_crud.get(db=db, id=profile_id)
    if not profile:
        logger.warning(f"DriverProfile with ID {profile_id} not found for update.")
        raise HTTPException(status_code=404, detail="Driver profile not found")
    updated_profile = driver_profile_crud.update(db=db, db_obj=profile, obj_in=profile_in)
    logger.info(f"Updated DriverProfile with ID: {profile_id}")
    return DriverProfileResponse(driver_profile_id=updated_profile.id_uuid, email=updated_profile.email, sync=updated_profile.sync)

@router.delete("/driver_profiles/{profile_id}", response_model=DriverProfileResponse)
def delete_driver_profile(profile_id: UUID, db: Session = Depends(get_db)) -> DriverProfileResponse:
    profile = driver_profile_crud.get(db=db, id=profile_id)
    if not profile:
        logger.warning(f"DriverProfile with ID {profile_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="Driver profile not found")
    deleted_profile = driver_profile_crud.delete(db=db, id=profile_id)
    logger.info(f"Deleted DriverProfile with ID: {profile_id}")
    return DriverProfileResponse(driver_profile_id=deleted_profile.id_uuid, email=deleted_profile.email, sync=deleted_profile.sync)