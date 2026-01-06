from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging

from safedrive.database.db import get_db
from safedrive.core.security import ApiClientContext, Role, ensure_driver_access, filter_query_by_driver_ids, require_roles
from safedrive.schemas.raw_sensor_data import (
    RawSensorDataCreate,
    RawSensorDataUpdate,
    RawSensorDataResponse,
)
from safedrive.crud.raw_sensor_data import raw_sensor_data_crud
from safedrive.models.trip import Trip

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

@router.post("/raw_sensor_data/", response_model=RawSensorDataResponse)
def create_raw_sensor_data(
    *,
    db: Session = Depends(get_db),
    raw_data_in: RawSensorDataCreate,
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> RawSensorDataResponse:
    """
    Create a new raw sensor data entry.

    - **sensor_type_name**: Name of the sensor type.
    - **timestamp**: Timestamp of the sensor reading.
    - **other fields**: Additional required fields.
    """
    try:
        if not raw_data_in.sensor_type_name or not raw_data_in.timestamp:
            logger.error("Sensor type name and timestamp are required to create raw sensor data.")
            raise HTTPException(status_code=400, detail="Sensor type name and timestamp are required")
        if current_client.role == Role.DRIVER:
            if not raw_data_in.trip_id:
                raise HTTPException(status_code=400, detail="Trip ID is required for driver uploads.")
            trip = db.query(Trip).filter(Trip.id == raw_data_in.trip_id).first()
            if not trip:
                raise HTTPException(status_code=404, detail="Trip not found")
            ensure_driver_access(current_client, trip.driverProfileId)
        new_data = raw_sensor_data_crud.create(db=db, obj_in=raw_data_in)
        logger.info(f"Raw sensor data created with ID: {new_data.id.hex()}")
        return RawSensorDataResponse.model_validate(new_data)
    except Exception as e:
        logger.exception("Error creating raw sensor data")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/raw_sensor_data/{data_id}", response_model=RawSensorDataResponse)
def get_raw_sensor_data(
    data_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> RawSensorDataResponse:
    """
    Retrieve a raw sensor data entry by ID.

    - **data_id**: The UUID of the raw sensor data to retrieve.
    """
    try:
        raw_data = raw_sensor_data_crud.get(db=db, id=data_id)
        if not raw_data:
            logger.warning(f"Raw sensor data with ID {data_id} not found.")
            raise HTTPException(status_code=404, detail="Raw sensor data not found")
        if current_client.role == Role.DRIVER:
            if not raw_data.trip_id:
                raise HTTPException(status_code=403, detail="Trip scope missing for sensor data.")
            trip = db.query(Trip).filter(Trip.id == raw_data.trip_id).first()
            if not trip:
                raise HTTPException(status_code=404, detail="Trip not found")
            ensure_driver_access(current_client, trip.driverProfileId)
        logger.info(f"Retrieved raw sensor data with ID: {data_id}")
        return RawSensorDataResponse.model_validate(raw_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error retrieving raw sensor data")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/raw_sensor_data/", response_model=List[RawSensorDataResponse])
def get_all_raw_sensor_data(
    skip: int = 0,
    limit: int = 5000,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> List[RawSensorDataResponse]:
    """
    Retrieve all raw sensor data entries with optional pagination.

    - **skip**: Number of records to skip.
    - **limit**: Maximum number of records to retrieve (max 100).
    """
    try:
        # if limit > 100:
        #     logger.error("Limit cannot exceed 100 items.")
        #     raise HTTPException(status_code=400, detail="Limit cannot exceed 100 items")
        if current_client.role == Role.ADMIN:
            data_list = raw_sensor_data_crud.get_all(db=db, skip=skip, limit=limit)
        else:
            query = (
                db.query(raw_sensor_data_crud.model)
                .join(Trip, raw_sensor_data_crud.model.trip_id == Trip.id)
            )
            query = filter_query_by_driver_ids(query, Trip.driverProfileId, current_client)
            data_list = query.offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(data_list)} raw sensor data entries.")
        return [RawSensorDataResponse.model_validate(data) for data in data_list]
    except Exception as e:
        logger.exception("Error retrieving raw sensor data entries")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/raw_sensor_data/{data_id}", response_model=RawSensorDataResponse)
def update_raw_sensor_data(
    data_id: UUID,
    *,
    db: Session = Depends(get_db),
    raw_data_in: RawSensorDataUpdate,
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> RawSensorDataResponse:
    """
    Update an existing raw sensor data entry.

    - **data_id**: The UUID of the raw sensor data to update.
    - **raw_data_in**: The updated data.
    """
    try:
        raw_data = raw_sensor_data_crud.get(db=db, id=data_id)
        if not raw_data:
            logger.warning(f"Raw sensor data with ID {data_id} not found.")
            raise HTTPException(status_code=404, detail="Raw sensor data not found")
        if current_client.role == Role.DRIVER:
            if not raw_data.trip_id:
                raise HTTPException(status_code=403, detail="Trip scope missing for sensor data.")
            trip = db.query(Trip).filter(Trip.id == raw_data.trip_id).first()
            if not trip:
                raise HTTPException(status_code=404, detail="Trip not found")
            ensure_driver_access(current_client, trip.driverProfileId)
        updated_data = raw_sensor_data_crud.update(db=db, db_obj=raw_data, obj_in=raw_data_in)
        logger.info(f"Updated raw sensor data with ID: {data_id}")
        return RawSensorDataResponse.model_validate(updated_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error updating raw sensor data")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/raw_sensor_data/{data_id}", response_model=RawSensorDataResponse)
def delete_raw_sensor_data(
    data_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> RawSensorDataResponse:
    """
    Delete a raw sensor data entry by ID.

    - **data_id**: The UUID of the raw sensor data to delete.
    """
    try:
        raw_data = raw_sensor_data_crud.get(db=db, id=data_id)
        if not raw_data:
            logger.warning(f"Raw sensor data with ID {data_id} not found.")
            raise HTTPException(status_code=404, detail="Raw sensor data not found")
        if current_client.role == Role.DRIVER:
            if not raw_data.trip_id:
                raise HTTPException(status_code=403, detail="Trip scope missing for sensor data.")
            trip = db.query(Trip).filter(Trip.id == raw_data.trip_id).first()
            if not trip:
                raise HTTPException(status_code=404, detail="Trip not found")
            ensure_driver_access(current_client, trip.driverProfileId)
        deleted_data = raw_sensor_data_crud.delete(db=db, id=data_id)
        logger.info(f"Deleted raw sensor data with ID: {data_id}")
        return RawSensorDataResponse.model_validate(deleted_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error deleting raw sensor data")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.post("/raw_sensor_data/batch_create", status_code=201)
def batch_create_raw_sensor_data(
    data: List[RawSensorDataCreate],
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    try:
        if current_client.role == Role.DRIVER:
            for item in data:
                if not item.trip_id:
                    raise HTTPException(status_code=400, detail="Trip ID is required for driver uploads.")
                trip = db.query(Trip).filter(Trip.id == item.trip_id).first()
                if not trip:
                    raise HTTPException(status_code=404, detail="Trip not found")
                ensure_driver_access(current_client, trip.driverProfileId)
        created_data = raw_sensor_data_crud.batch_create(db=db, data_in=data)
        return {"message": f"{len(created_data)} RawSensorData records created."}
    except Exception as e:
        logger.error(f"Error in batch create RawSensorData: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch creation failed.")

@router.delete("/raw_sensor_data/batch_delete", status_code=204)
def batch_delete_raw_sensor_data(
    ids: List[UUID],
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    try:
        if current_client.role == Role.DRIVER:
            records = (
                db.query(raw_sensor_data_crud.model)
                .filter(raw_sensor_data_crud.model.id.in_(ids))
                .all()
            )
            for record in records:
                if not record.trip_id:
                    raise HTTPException(status_code=403, detail="Trip scope missing for sensor data.")
                trip = db.query(Trip).filter(Trip.id == record.trip_id).first()
                if not trip:
                    raise HTTPException(status_code=404, detail="Trip not found")
                ensure_driver_access(current_client, trip.driverProfileId)
        raw_sensor_data_crud.batch_delete(db=db, ids=ids)
        return {"message": f"{len(ids)} RawSensorData records deleted."}
    except Exception as e:
        logger.error(f"Error in batch delete RawSensorData: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch deletion failed.")
