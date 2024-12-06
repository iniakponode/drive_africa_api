from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging

from safedrive.database.db import get_db
from safedrive.schemas.unsafe_behaviour import (
    UnsafeBehaviourCreate,
    UnsafeBehaviourUpdate,
    UnsafeBehaviourResponse,
)
from safedrive.crud.unsafe_behaviour import unsafe_behaviour_crud

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

@router.post("/unsafe_behaviours/", response_model=UnsafeBehaviourResponse)
def create_unsafe_behaviour(
    *,
    db: Session = Depends(get_db),
    unsafe_behaviour_in: UnsafeBehaviourCreate,
) -> UnsafeBehaviourResponse:
    """
    Create a new unsafe behaviour.

    - **trip_id**: UUID of the associated trip.
    - **behaviour_type**: Type of unsafe behaviour.
    - **severity**: Severity level of the unsafe behaviour.
    - **timestamp**: Timestamp when the behaviour was recorded.
    - Other optional fields.
    """
    try:
        # Validation: Ensure necessary fields are not empty or invalid
        if not unsafe_behaviour_in.trip_id or not unsafe_behaviour_in.behaviour_type:
            logger.error("Trip ID and behaviour type are required to create an unsafe behaviour.")
            raise HTTPException(status_code=400, detail="Trip ID and behaviour type are required")
        new_behaviour = unsafe_behaviour_crud.create(db=db, obj_in=unsafe_behaviour_in)
        logger.info(f"Unsafe behaviour created with ID: {new_behaviour.id.hex()}")
        return UnsafeBehaviourResponse.model_validate(new_behaviour)
    except Exception as e:
        logger.exception("Error creating unsafe behaviour")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/unsafe_behaviours/{unsafe_behaviour_id}", response_model=UnsafeBehaviourResponse)
def get_unsafe_behaviour(
    unsafe_behaviour_id: UUID,
    db: Session = Depends(get_db),
) -> UnsafeBehaviourResponse:
    """
    Retrieve an unsafe behaviour by ID.

    - **unsafe_behaviour_id**: The UUID of the unsafe behaviour to retrieve.
    """
    try:
        unsafe_behaviour = unsafe_behaviour_crud.get(db=db, id=unsafe_behaviour_id)
        if not unsafe_behaviour:
            logger.warning(f"Unsafe behaviour with ID {unsafe_behaviour_id} not found.")
            raise HTTPException(status_code=404, detail="Unsafe behaviour not found")
        logger.info(f"Retrieved unsafe behaviour with ID: {unsafe_behaviour_id}")
        return UnsafeBehaviourResponse.model_validate(unsafe_behaviour)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error retrieving unsafe behaviour")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/unsafe_behaviours/", response_model=List[UnsafeBehaviourResponse])
def get_all_unsafe_behaviours(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> List[UnsafeBehaviourResponse]:
    """
    Retrieve all unsafe behaviours with optional pagination.

    - **skip**: Number of records to skip.
    - **limit**: Maximum number of records to retrieve (max 100).
    """
    try:
        if limit > 100:
            logger.error("Limit cannot exceed 100 items.")
            raise HTTPException(status_code=400, detail="Limit cannot exceed 100 items")
        behaviours = unsafe_behaviour_crud.get_all(db=db, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(behaviours)} unsafe behaviours.")
        return [UnsafeBehaviourResponse.model_validate(behaviour) for behaviour in behaviours]
    except Exception as e:
        logger.exception("Error retrieving unsafe behaviours")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/unsafe_behaviours/{unsafe_behaviour_id}", response_model=UnsafeBehaviourResponse)
def update_unsafe_behaviour(
    unsafe_behaviour_id: UUID,
    *,
    db: Session = Depends(get_db),
    unsafe_behaviour_in: UnsafeBehaviourUpdate,
) -> UnsafeBehaviourResponse:
    """
    Update an existing unsafe behaviour.

    - **unsafe_behaviour_id**: The UUID of the unsafe behaviour to update.
    - **unsafe_behaviour_in**: The updated data.
    """
    try:
        unsafe_behaviour = unsafe_behaviour_crud.get(db=db, id=unsafe_behaviour_id)
        if not unsafe_behaviour:
            logger.warning(f"Unsafe behaviour with ID {unsafe_behaviour_id} not found.")
            raise HTTPException(status_code=404, detail="Unsafe behaviour not found")
        updated_behaviour = unsafe_behaviour_crud.update(db=db, db_obj=unsafe_behaviour, obj_in=unsafe_behaviour_in)
        logger.info(f"Updated unsafe behaviour with ID: {unsafe_behaviour_id}")
        return UnsafeBehaviourResponse.model_validate(updated_behaviour)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error updating unsafe behaviour")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/unsafe_behaviours/{unsafe_behaviour_id}", response_model=UnsafeBehaviourResponse)
def delete_unsafe_behaviour(
    unsafe_behaviour_id: UUID,
    db: Session = Depends(get_db),
) -> UnsafeBehaviourResponse:
    """
    Delete an unsafe behaviour by ID.

    - **unsafe_behaviour_id**: The UUID of the unsafe behaviour to delete.
    """
    try:
        unsafe_behaviour = unsafe_behaviour_crud.get(db=db, id=unsafe_behaviour_id)
        if not unsafe_behaviour:
            logger.warning(f"Unsafe behaviour with ID {unsafe_behaviour_id} not found.")
            raise HTTPException(status_code=404, detail="Unsafe behaviour not found")
        deleted_behaviour = unsafe_behaviour_crud.delete(db=db, id=unsafe_behaviour_id)
        logger.info(f"Deleted unsafe behaviour with ID: {unsafe_behaviour_id}")
        return UnsafeBehaviourResponse.model_validate(deleted_behaviour)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error deleting unsafe behaviour")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.post("/unsafe_behaviours/batch_create", status_code=201)
def batch_create_unsafe_behaviours(data: List[UnsafeBehaviourCreate], db: Session = Depends(get_db)):
    try:
        created_behaviours = unsafe_behaviour_crud.batch_create(db=db, data_in=data)
        return {"message": f"{len(created_behaviours)} UnsafeBehaviour records created."}
    except Exception as e:
        logger.error(f"Error in batch create UnsafeBehaviour: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch creation failed.")

@router.delete("/unsafe_behaviours/batch_delete", status_code=204)
def batch_delete_unsafe_behaviours(ids: List[UUID], db: Session = Depends(get_db)):
    try:
        unsafe_behaviour_crud.batch_delete(db=db, ids=ids)
        return {"message": f"{len(ids)} UnsafeBehaviour records deleted."}
    except Exception as e:
        logger.error(f"Error in batch delete UnsafeBehaviour: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch deletion failed.")