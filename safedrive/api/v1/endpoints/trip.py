from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging
from safedrive.crud.trip import trip_crud
from safedrive.crud.driver_profile import driver_profile_crud
from safedrive.database.db import get_db
from safedrive.core.security import (
    ApiClientContext,
    Role,
    ensure_driver_access,
    filter_query_by_driver_ids,
    require_roles_or_jwt,
)
from safedrive.models.trip import Trip
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
def create_trip(
    *,
    db: Session = Depends(get_db),
    trip_in: TripCreate,
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(Role.ADMIN, Role.DRIVER)
    ),
) -> TripResponse:
    try:
        # Check for required fields
        if not trip_in.driverProfileId or not trip_in.start_time:
            logger.warning("Driver Profile ID and start time are required to create a trip.")
            raise HTTPException(status_code=400, detail="Driver Profile ID and start time are required to create a trip.")
        ensure_driver_access(current_client, trip_in.driverProfileId)
        
        # Validate if the driver profile exists
        profile_exists = driver_profile_crud.get(db=db, id=trip_in.driverProfileId)
        if not profile_exists:
            logger.warning(f"DriverProfile with ID {trip_in.driverProfileId} not found.")
            raise HTTPException(status_code=404, detail="Driver Profile ID does not exist in the database.")
        
        # Create the new trip
        new_trip = trip_crud.create(db=db, obj_in=trip_in)
        logger.info(f"Created Trip with ID: {new_trip.id}")
        return TripResponse(
            id=new_trip.id,
            driverProfileId=new_trip.driverProfileId,
            start_date=new_trip.start_date,
            end_date=new_trip.end_date,
            start_time=new_trip.start_time,
            end_time=new_trip.end_time,
            sync=new_trip.sync,
            influence=new_trip.influence,
            trip_notes=new_trip.trip_notes,
            alcohol_probability=new_trip.alcohol_probability,
            user_alcohol_response=new_trip.user_alcohol_response,
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
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(Role.ADMIN, Role.DRIVER)
    ),
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
        ensure_driver_access(current_client, trip.driverProfileId)
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
    limit: int = 5000,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(Role.ADMIN, Role.DRIVER)
    ),
) -> List[TripResponse]:
    """
    Retrieve all trips with optional pagination.

    - **skip**: Number of records to skip.
    - **limit**: Maximum number of records to retrieve (max 100).
    """
    try:
        # if limit > 100:
        #     logger.error("Limit cannot exceed 100 items.")
        #     raise HTTPException(status_code=400, detail="Limit cannot exceed 100 items")
        if current_client.role == Role.ADMIN:
            trips = trip_crud.get_all(db=db, skip=skip, limit=limit)
        else:
            query = db.query(Trip)
            query = filter_query_by_driver_ids(query, Trip.driverProfileId, current_client)
            trips = query.offset(skip).limit(limit).all()
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
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(Role.ADMIN, Role.DRIVER)
    ),
) -> TripResponse:
    """
    Update an existing trip.
    """
    try:
        # 1) Retrieve trip from DB
        trip = trip_crud.get(db=db, id=trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        ensure_driver_access(current_client, trip.driverProfileId)
        if (
            current_client.role == Role.DRIVER
            and trip_in.driverProfileId
            and trip_in.driverProfileId != current_client.driver_profile_id
        ):
            raise HTTPException(status_code=403, detail="Driver scope access denied.")

        # 2) Perform the update
        updated_trip = trip_crud.update(db=db, db_obj=trip, obj_in=trip_in)
        
        # 3) Return the updated record
        return TripResponse.model_validate(updated_trip)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating trip")
        logger.debug(f"Trip update body: {trip_in.model_dump(exclude_unset=True)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/trips/{trip_id}", response_model=TripResponse)
def delete_trip(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(Role.ADMIN, Role.DRIVER)
    ),
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
        ensure_driver_access(current_client, trip.driverProfileId)
        deleted_trip = trip_crud.delete(db=db, id=trip_id)
        logger.info(f"Deleted trip with ID: {trip_id}")
        return TripResponse.model_validate(deleted_trip)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error deleting trip")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
# @router.post("/trips/batch_create", status_code=201)
# def batch_create_trips(data: List[TripCreate], db: Session = Depends(get_db)):
#     try:
#         created_trips = trip_crud.batch_create(db=db, data_in=data)
#         return {"message": f"{len(created_trips)} Trip records created."}
#     except Exception as e:
#         logger.error(f"Error in batch create Trip: {str(e)}")
#         raise HTTPException(status_code=500, detail="Batch creation failed.")

@router.delete("/trips/batch_delete", status_code=204)
def batch_delete_trips(
    ids: List[UUID],
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(Role.ADMIN, Role.DRIVER)
    ),
):
    try:
        if current_client.role == Role.DRIVER:
            trips = db.query(Trip).filter(Trip.id.in_(ids)).all()
            for trip in trips:
                ensure_driver_access(current_client, trip.driverProfileId)
        trip_crud.batch_delete(db=db, ids=ids)
        return {"message": f"{len(ids)} Trip records deleted."}
    except Exception as e:
        logger.error(f"Error in batch delete Trip: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch deletion failed.")

from sqlalchemy.exc import IntegrityError

@router.post("/trips/batch_create", response_model=List[TripResponse])
def batch_create_trips(
    *,
    db: Session = Depends(get_db),
    trips_in: List[TripCreate],
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(Role.ADMIN, Role.DRIVER)
    ),
) -> List[TripResponse]:
    try:
        if current_client.role == Role.DRIVER:
            for trip in trips_in:
                ensure_driver_access(current_client, trip.driverProfileId)
        new_trips = trip_crud.batch_create(db=db, objs_in=trips_in)

        if not new_trips:
            raise HTTPException(
                status_code=400,
                detail="No trips were created due to errors or duplicates."
            )

        return [
            TripResponse.from_attributes(new_trip)
            for new_trip in new_trips
        ]

    except IntegrityError as e:
        logger.exception("Integrity error in batch trip creation")
        raise HTTPException(
            status_code=400,
            detail=f"Foreign key or duplicate constraint failed: {str(e)}"
        )
    except Exception as e:
        logger.exception("Unexpected error creating trips")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating trips."
        )
