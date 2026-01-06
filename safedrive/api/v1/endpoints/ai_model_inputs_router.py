from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging

from safedrive.database.db import get_db
from safedrive.core.security import ApiClientContext, Role, ensure_driver_access, filter_query_by_driver_ids, require_roles
from safedrive.schemas.ai_model_input import (
    AIModelInputCreate,
    AIModelInputUpdate,
    AIModelInputResponse,
)
from safedrive.crud.ai_model_inputs import ai_model_inputs_crud
from safedrive.models.ai_model_input import AIModelInput

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

# Endpoint to create a new AI model input
@router.post("/ai_model_inputs/", response_model=AIModelInputResponse)
def create_ai_model_input(
    *,
    db: Session = Depends(get_db),
    input_in: AIModelInputCreate,
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> AIModelInputResponse:
    """
    Create a new AI model input.

    - **trip_id**: The ID of the trip associated with this AI model input.
    - **timestamp**: Timestamp of the AI model input.
    - **date**: Date of the AI model input.
    - Other fields as required.
    """
    try:
        # Validation: Ensure necessary fields are not empty or invalid
        if not input_in.trip_id:
            logger.error("Trip ID is required to create AI model input.")
            raise HTTPException(status_code=400, detail="Trip ID is required")
        ensure_driver_access(current_client, input_in.driverProfileId)
        new_input = ai_model_inputs_crud.create(db=db, obj_in=input_in)
        logger.info(f"AI model input created with ID: {new_input.id}")
        return AIModelInputResponse.model_validate(new_input)
    except Exception as e:
        logger.exception("Error creating AI model input")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to get an AI model input by ID
@router.get("/ai_model_inputs/{input_id}", response_model=AIModelInputResponse)
def get_ai_model_input(
    input_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> AIModelInputResponse:
    """
    Retrieve an AI model input by ID.

    - **input_id**: The ID of the AI model input to retrieve.
    """
    try:
        ai_model_input = ai_model_inputs_crud.get(db=db, id=input_id)
        if not ai_model_input:
            logger.warning(f"AI model input with ID {input_id} not found.")
            raise HTTPException(status_code=404, detail="AI model input not found")
        ensure_driver_access(current_client, ai_model_input.driverProfileId)
        logger.info(f"Retrieved AI model input with ID: {input_id}")
        return AIModelInputResponse.model_validate(ai_model_input)
    except HTTPException as e:
        raise e  # Re-raise to allow FastAPI to handle it
    except Exception as e:
        logger.exception("Error retrieving AI model input")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to get all AI model inputs with optional pagination
@router.get("/ai_model_inputs/", response_model=List[AIModelInputResponse])
def get_all_ai_model_inputs(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> List[AIModelInputResponse]:
    """
    Retrieve all AI model inputs with optional pagination.

    - **skip**: Number of records to skip.
    - **limit**: Maximum number of records to retrieve (max 100).
    """
    try:
        if limit > 100:
            logger.error("Limit cannot exceed 100 items.")
            raise HTTPException(status_code=400, detail="Limit cannot exceed 100 items")
        if current_client.role == Role.ADMIN:
            inputs = ai_model_inputs_crud.get_all(db=db, skip=skip, limit=limit)
        else:
            query = db.query(AIModelInput)
            query = filter_query_by_driver_ids(query, AIModelInput.driverProfileId, current_client)
            inputs = query.offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(inputs)} AI model inputs.")
        return [AIModelInputResponse.model_validate(input) for input in inputs]
    except Exception as e:
        logger.exception("Error retrieving AI model inputs")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to update an existing AI model input
@router.put("/ai_model_inputs/{input_id}", response_model=AIModelInputResponse)
def update_ai_model_input(
    input_id: UUID,
    *,
    db: Session = Depends(get_db),
    input_in: AIModelInputUpdate,
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> AIModelInputResponse:
    """
    Update an existing AI model input.

    - **input_id**: The ID of the AI model input to update.
    - **input_in**: The updated data.
    """
    try:
        ai_model_input = ai_model_inputs_crud.get(db=db, id=input_id)
        if not ai_model_input:
            logger.warning(f"AI model input with ID {input_id} not found.")
            raise HTTPException(status_code=404, detail="AI model input not found")
        ensure_driver_access(current_client, ai_model_input.driverProfileId)
        if (
            current_client.role == Role.DRIVER
            and input_in.driverProfileId
            and input_in.driverProfileId != current_client.driver_profile_id
        ):
            raise HTTPException(status_code=403, detail="Driver scope access denied.")
        updated_input = ai_model_inputs_crud.update(db=db, db_obj=ai_model_input, obj_in=input_in)
        logger.info(f"Updated AI model input with ID: {input_id}")
        return AIModelInputResponse.model_validate(updated_input)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error updating AI model input")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to delete an AI model input by ID
@router.delete("/ai_model_inputs/{input_id}", response_model=AIModelInputResponse)
def delete_ai_model_input(
    input_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> AIModelInputResponse:
    """
    Delete an AI model input by ID.

    - **input_id**: The ID of the AI model input to delete.
    """
    try:
        ai_model_input = ai_model_inputs_crud.get(db=db, id=input_id)
        if not ai_model_input:
            logger.warning(f"AI model input with ID {input_id} not found.")
            raise HTTPException(status_code=404, detail="AI model input not found")
        ensure_driver_access(current_client, ai_model_input.driverProfileId)
        deleted_input = ai_model_inputs_crud.delete(db=db, id=input_id)
        logger.info(f"Deleted AI model input with ID: {input_id}")
        return AIModelInputResponse.model_validate(deleted_input)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error deleting AI model input")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.post("/ai_model_inputs/batch_create", status_code=201)
def batch_create_ai_model_inputs(
    data: List[AIModelInputCreate],
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    try:
        if current_client.role == Role.DRIVER:
            for item in data:
                ensure_driver_access(current_client, item.driverProfileId)
        created_inputs = ai_model_inputs_crud.batch_create(db=db, data_in=data)
        return {"message": f"{len(created_inputs)} AIModelInput records created."}
    except Exception as e:
        logger.error(f"Error in batch create AIModelInput: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch creation failed.")

@router.delete("/ai_model_inputs/batch_delete", status_code=204)
def batch_delete_ai_model_inputs(
    ids: List[UUID],
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    try:
        if current_client.role == Role.DRIVER:
            records = db.query(AIModelInput).filter(AIModelInput.id.in_(ids)).all()
            for record in records:
                ensure_driver_access(current_client, record.driverProfileId)
        ai_model_inputs_crud.batch_delete(db=db, ids=ids)
        return {"message": f"{len(ids)} AIModelInput records deleted."}
    except Exception as e:
        logger.error(f"Error in batch delete AIModelInput: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch deletion failed.")
