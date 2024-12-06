from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging
from safedrive.crud.trip import trip_crud
from safedrive.crud.driver_profile import driver_profile_crud
from safedrive.database.db import get_db
from safedrive.schemas.trip import (
    TripCreate,
    TripUpdate,
    TripResponse,
)

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

@router.post("/trips/", response_model=TripResponse)
def create_trip(*, db: Session = Depends(get_db), trip_in: TripCreate) -> TripResponse:
    try:
        # Check for required fields
        if not trip_in.driver_profile_id or not trip_in.start_time:
            logger.warning("Driver Profile ID and start time are required to create a trip.")
            raise HTTPException(status_code=400, detail="Driver Profile ID and start time are required to create a trip.")
        
        # Validate if the driver profile exists
        profile_exists = driver_profile_crud.get(db=db, id=trip_in.driver_profile_id)
        if not profile_exists:
            logger.warning(f"DriverProfile with ID {trip_in.driver_profile_id} not found.")
            raise HTTPException(status_code=404, detail="Driver Profile ID does not exist in the database.")
        
        # Create the new trip
        new_trip = trip_crud.create(db=db, obj_in=trip_in)
        logger.info(f"Created Trip with ID: {new_trip.id_uuid}")
        return TripResponse(
            id=new_trip.id_uuid,
            driver_profile_id=new_trip.driver_profile_id_uuid,
            start_date=new_trip.start_date,
            end_date=new_trip.end_date,
            start_time=new_trip.start_time,
            end_time=new_trip.end_time,
            synced=new_trip.synced
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error creating trip: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error creating trip.")

@router.get("/trips/{trip_id}", response_model=TripResponse)
def get_trip(
    trip_id: UUID,
    db: Session = Depends(get_db),
) -> TripResponse:
    """
    Retrieve a trip by ID.

    - **trip_id**: The UUID of the trip to retrieve.
    """
    try:
        trip = trip_crud.get(db=db, id=trip_id)
        if not trip:
            logger.warning(f"Trip with ID {trip_id} not found.")
            raise HTTPException(status_code=404, detail="Trip not found")
        logger.info(f"Retrieved trip with ID: {trip_id}")
        return TripResponse.model_validate(trip)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error retrieving trip")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/trips/", response_model=List[TripResponse])
def get_all_trips(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> List[TripResponse]:
    """
    Retrieve all trips with optional pagination.

    - **skip**: Number of records to skip.
    - **limit**: Maximum number of records to retrieve (max 100).
    """
    try:
        if limit > 100:
            logger.error("Limit cannot exceed 100 items.")
            raise HTTPException(status_code=400, detail="Limit cannot exceed 100 items")
        trips = trip_crud.get_all(db=db, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(trips)} trips.")
        return [TripResponse.model_validate(trip) for trip in trips]
    except Exception as e:
        logger.exception("Error retrieving trips")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/trips/{trip_id}", response_model=TripResponse)
def update_trip(
    trip_id: UUID,
    *,
    db: Session = Depends(get_db),
    trip_in: TripUpdate,
) -> TripResponse:
    """
    Update an existing trip.

    - **trip_id**: The UUID of the trip to update.
    - **trip_in**: The updated data.
    """
    try:
        trip = trip_crud.get(db=db, id=trip_id)
        if not trip:
            logger.warning(f"Trip with ID {trip_id} not found.")
            raise HTTPException(status_code=404, detail="Trip not found")
        updated_trip = trip_crud.update(db=db, db_obj=trip, obj_in=trip_in)
        logger.info(f"Updated trip with ID: {trip_id}")
        return TripResponse.model_validate(updated_trip)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error updating trip")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/trips/{trip_id}", response_model=TripResponse)
def delete_trip(
    trip_id: UUID,
    db: Session = Depends(get_db),
) -> TripResponse:
    """
    Delete a trip by ID.

    - **trip_id**: The UUID of the trip to delete.
    """
    try:
        trip = trip_crud.get(db=db, id=trip_id)
        if not trip:
            logger.warning(f"Trip with ID {trip_id} not found.")
            raise HTTPException(status_code=404, detail="Trip not found")
        deleted_trip = trip_crud.delete(db=db, id=trip_id)
        logger.info(f"Deleted trip with ID: {trip_id}")
        return TripResponse.model_validate(deleted_trip)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error deleting trip")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.post("/trips/batch_create", status_code=201)
def batch_create_trips(data: List[TripCreate], db: Session = Depends(get_db)):
    try:
        created_trips = trip_crud.batch_create(db=db, data_in=data)
        return {"message": f"{len(created_trips)} Trip records created."}
    except Exception as e:
        logger.error(f"Error in batch create Trip: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch creation failed.")

@router.delete("/trips/batch_delete", status_code=204)
def batch_delete_trips(ids: List[UUID], db: Session = Depends(get_db)):
    try:
        trip_crud.batch_delete(db=db, ids=ids)
        return {"message": f"{len(ids)} Trip records deleted."}
    except Exception as e:
        logger.error(f"Error in batch delete Trip: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch deletion failed.")