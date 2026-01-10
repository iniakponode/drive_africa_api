from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from uuid import UUID
from safedrive.schemas.alcohol_questionnaire import (
    AlcoholQuestionnaireCreateSchema,
    AlcoholQuestionnaireResponseSchema,
)
from safedrive.crud.alcohol_questionnaire import AlcoholQuestionnaireCRUD
from safedrive.database.db import get_db
from safedrive.core.security import ApiClientContext, Role, ensure_driver_access, require_roles, require_roles_or_jwt
import logging

router = APIRouter()
mobile_router = APIRouter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Endpoint to submit a new alcohol questionnaire
@router.post("/questionnaire/", response_model=AlcoholQuestionnaireResponseSchema)
async def submit_alcohol_questionnaire(
    questionnaire_data: AlcoholQuestionnaireCreateSchema,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(Role.ADMIN, Role.DRIVER)
    ),
):
    """Submit a new alcohol questionnaire."""
    try:
        ensure_driver_access(current_client, questionnaire_data.driverProfileId)
        crud = AlcoholQuestionnaireCRUD(db)
        saved_data = crud.create(questionnaire_data)
        logger.info(f"Successfully created alcohol questionnaire: {saved_data.id}")
        return saved_data
    except Exception as e:
        logger.error(f"Error creating alcohol questionnaire: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the alcohol questionnaire."
        )

# Mobile compatibility endpoint (matches /api/questionnaire/)
@mobile_router.post("/questionnaire/", response_model=AlcoholQuestionnaireResponseSchema)
async def submit_alcohol_questionnaire_mobile(
    questionnaire_data: AlcoholQuestionnaireCreateSchema,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    """Submit a new alcohol questionnaire (mobile compatibility)."""
    try:
        ensure_driver_access(current_client, questionnaire_data.driverProfileId)
        crud = AlcoholQuestionnaireCRUD(db)
        saved_data = crud.create(questionnaire_data)
        logger.info(f"Successfully created alcohol questionnaire (mobile): {saved_data.id}")
        return saved_data
    except Exception as e:
        logger.error(f"Error creating alcohol questionnaire (mobile): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the alcohol questionnaire."
        )

# Mobile batch-create endpoint (matches /api/questionnaire/batch_create)
@mobile_router.post("/questionnaire/batch_create", status_code=status.HTTP_201_CREATED)
async def submit_alcohol_questionnaire_batch_mobile(
    questionnaires: List[AlcoholQuestionnaireCreateSchema],
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    """Submit multiple alcohol questionnaires (mobile compatibility)."""
    try:
        if current_client.role == Role.DRIVER:
            for questionnaire in questionnaires:
                ensure_driver_access(current_client, questionnaire.driverProfileId)
        crud = AlcoholQuestionnaireCRUD(db)
        created, skipped = crud.batch_create(questionnaires)
        logger.info(
            "Successfully created alcohol questionnaires (mobile batch): %s created, %s skipped",
            created,
            skipped,
        )
        return {"created": created, "skipped": skipped}
    except Exception as e:
        logger.error(f"Error creating alcohol questionnaires (mobile batch): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the alcohol questionnaires."
        )
# Endpoint to get an alcohol questionnaire by ID
@router.get("/questionnaire/{questionnaire_id}/", response_model=AlcoholQuestionnaireResponseSchema)
async def get_alcohol_questionnaire(
    questionnaire_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    """Retrieve a questionnaire by its ID."""
    try:
        crud = AlcoholQuestionnaireCRUD(db)
        questionnaire = crud.get_by_id(questionnaire_id)
        ensure_driver_access(current_client, questionnaire.driverProfileId)
        logger.info(f"Successfully retrieved alcohol questionnaire: {questionnaire_id}")
        return questionnaire
    except HTTPException as http_exc:
        logger.warning(f"Alcohol questionnaire not found: {questionnaire_id}")
        raise http_exc
    except Exception as e:
        logger.error(f"Error retrieving alcohol questionnaire: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the alcohol questionnaire."
        )

# Mobile compatibility endpoint (matches /api/questionnaire/{userId})
@mobile_router.get("/questionnaire/{user_id}", response_model=List[AlcoholQuestionnaireResponseSchema])
async def get_alcohol_questionnaire_history(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    """Retrieve questionnaire history for a driver (mobile compatibility)."""
    try:
        ensure_driver_access(current_client, user_id)
        crud = AlcoholQuestionnaireCRUD(db)
        questionnaires = crud.get_by_driver_id(user_id)
        logger.info(f"Successfully retrieved alcohol questionnaire history: {user_id}")
        return questionnaires
    except Exception as e:
        logger.error(f"Error retrieving alcohol questionnaire history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the alcohol questionnaires."
        )

# Endpoint to list all alcohol questionnaires
@router.get("/questionnaire/", response_model=list[AlcoholQuestionnaireResponseSchema])
async def list_alcohol_questionnaires(
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    """List all submitted alcohol questionnaires."""
    try:
        crud = AlcoholQuestionnaireCRUD(db)
        if current_client.role == Role.ADMIN:
            questionnaires = crud.get_all()
        else:
            questionnaires = crud.get_by_driver_id(current_client.driver_profile_id)
        logger.info("Successfully retrieved all alcohol questionnaires")
        return questionnaires
    except Exception as e:
        logger.error(f"Error retrieving alcohol questionnaires: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the alcohol questionnaires."
        )

# Endpoint to update an alcohol questionnaire
@router.put("/questionnaire/{questionnaire_id}/", response_model=AlcoholQuestionnaireResponseSchema)
async def update_alcohol_questionnaire(
    questionnaire_id: UUID,
    updated_data: AlcoholQuestionnaireCreateSchema,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    """Update an existing questionnaire."""
    try:
        crud = AlcoholQuestionnaireCRUD(db)
        ensure_driver_access(current_client, updated_data.driverProfileId)
        updated_questionnaire = crud.update(questionnaire_id, updated_data)
        logger.info(f"Successfully updated alcohol questionnaire: {questionnaire_id}")
        return updated_questionnaire
    except HTTPException as http_exc:
        logger.warning(f"Alcohol questionnaire not found for update: {questionnaire_id}")
        raise http_exc
    except Exception as e:
        logger.error(f"Error updating alcohol questionnaire: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the alcohol questionnaire."
        )

# Endpoint to delete an alcohol questionnaire
@router.delete("/questionnaire/{questionnaire_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alcohol_questionnaire(
    questionnaire_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    """Delete a questionnaire by its ID."""
    try:
        crud = AlcoholQuestionnaireCRUD(db)
        questionnaire = crud.get_by_id(questionnaire_id)
        ensure_driver_access(current_client, questionnaire.driverProfileId)
        crud.delete(questionnaire_id)
        logger.info(f"Successfully deleted alcohol questionnaire: {questionnaire_id}")
    except HTTPException as http_exc:
        logger.warning(f"Alcohol questionnaire not found for deletion: {questionnaire_id}")
        raise http_exc
    except Exception as e:
        logger.error(f"Error deleting alcohol questionnaire: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the alcohol questionnaire."
        )
