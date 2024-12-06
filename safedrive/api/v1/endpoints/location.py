from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging

from safedrive.database.db import get_db
from safedrive.schemas.location import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
)
from safedrive.crud.location import location_crud

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

@router.post("/locations/", response_model=LocationResponse)
def create_location(
    *,
    db: Session = Depends(get_db),
    location_in: LocationCreate,
) -> LocationResponse:
    """
    Create a new location.

    - **latitude**: Latitude of the location.
    - **longitude**: Longitude of the location.
    - **timestamp**: Timestamp when the location was recorded.
    - Other optional fields.
    """
    try:
        # Validation: Ensure necessary fields are not empty or invalid
        if location_in.latitude is None or location_in.longitude is None:
            logger.error("Latitude and longitude are required to create a location.")
            raise HTTPException(status_code=400, detail="Latitude and longitude are required")
        new_location = location_crud.create(db=db, obj_in=location_in)
        logger.info(f"Location created with ID: {new_location.id.hex()}")
        return LocationResponse.model_validate(new_location)
    except Exception as e:
        logger.exception("Error creating location")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/locations/{location_id}", response_model=LocationResponse)
def get_location(
    location_id: UUID,
    db: Session = Depends(get_db),
) -> LocationResponse:
    """
    Retrieve a location by ID.

    - **location_id**: The UUID of the location to retrieve.
    """
    try:
        location = location_crud.get(db=db, id=location_id)
        if not location:
            logger.warning(f"Location with ID {location_id} not found.")
            raise HTTPException(status_code=404, detail="Location not found")
        logger.info(f"Retrieved location with ID: {location_id}")
        return LocationResponse.model_validate(location)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error retrieving location")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/locations/", response_model=List[LocationResponse])
def get_all_locations(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> List[LocationResponse]:
    """
    Retrieve all locations with optional pagination.

    - **skip**: Number of records to skip.
    - **limit**: Maximum number of records to retrieve (max 100).
    """
    try:
        if limit > 100:
            logger.error("Limit cannot exceed 100 items.")
            raise HTTPException(status_code=400, detail="Limit cannot exceed 100 items")
        locations = location_crud.get_all(db=db, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(locations)} locations.")
        return [LocationResponse.model_validate(loc) for loc in locations]
    except Exception as e:
        logger.exception("Error retrieving locations")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/locations/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: UUID,
    *,
    db: Session = Depends(get_db),
    location_in: LocationUpdate,
) -> LocationResponse:
    """
    Update an existing location.

    - **location_id**: The UUID of the location to update.
    - **location_in**: The updated data.
    """
    try:
        location = location_crud.get(db=db, id=location_id)
        if not location:
            logger.warning(f"Location with ID {location_id} not found.")
            raise HTTPException(status_code=404, detail="Location not found")
        updated_location = location_crud.update(db=db, db_obj=location, obj_in=location_in)
        logger.info(f"Updated location with ID: {location_id}")
        return LocationResponse.model_validate(updated_location)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error updating location")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/locations/{location_id}", response_model=LocationResponse)
def delete_location(
    location_id: UUID,
    db: Session = Depends(get_db),
) -> LocationResponse:
    """
    Delete a location by ID.

    - **location_id**: The UUID of the location to delete.
    """
    try:
        location = location_crud.get(db=db, id=location_id)
        if not location:
            logger.warning(f"Location with ID {location_id} not found.")
            raise HTTPException(status_code=404, detail="Location not found")
        deleted_location = location_crud.delete(db=db, id=location_id)
        logger.info(f"Deleted location with ID: {location_id}")
        return LocationResponse.model_validate(deleted_location)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error deleting location")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/locations/batch_create", status_code=201)
def batch_create_locations(data: List[LocationCreate], db: Session = Depends(get_db)):
    try:
        created_locations = location_crud.batch_create(db=db, data_in=data)
        return {"message": f"{len(created_locations)} Location records created."}
    except Exception as e:
        logger.error(f"Error in batch create Location: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch creation failed.")

@router.delete("/locations/batch_delete", status_code=204)
def batch_delete_locations(ids: List[UUID], db: Session = Depends(get_db)):
    try:
        location_crud.batch_delete(db=db, ids=ids)
        return {"message": f"{len(ids)} Location records deleted."}
    except Exception as e:
        logger.error(f"Error in batch delete Location: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch deletion failed.")