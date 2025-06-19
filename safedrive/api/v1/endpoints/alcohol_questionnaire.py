from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from safedrive.schemas.alcohol_questionnaire import (
    AlcoholQuestionnaireCreateSchema,
    AlcoholQuestionnaireResponseSchema,
)
from safedrive.crud.alcohol_questionnaire import AlcoholQuestionnaireCRUD
from safedrive.database.db import get_db
import logging

router = APIRouter()
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
):
    """Submit a new alcohol questionnaire."""
    try:
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

# Endpoint to get an alcohol questionnaire by ID
@router.get("/questionnaire/{questionnaire_id}/", response_model=AlcoholQuestionnaireResponseSchema)
async def get_alcohol_questionnaire(
    questionnaire_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve a questionnaire by its ID."""
    try:
        crud = AlcoholQuestionnaireCRUD(db)
        questionnaire = crud.get_by_id(questionnaire_id)
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

# Endpoint to list all alcohol questionnaires
@router.get("/questionnaire/", response_model=list[AlcoholQuestionnaireResponseSchema])
async def list_alcohol_questionnaires(
    db: Session = Depends(get_db),
):
    """List all submitted alcohol questionnaires."""
    try:
        crud = AlcoholQuestionnaireCRUD(db)
        questionnaires = crud.get_all()
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
):
    """Update an existing questionnaire."""
    try:
        crud = AlcoholQuestionnaireCRUD(db)
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
):
    """Delete a questionnaire by its ID."""
    try:
        crud = AlcoholQuestionnaireCRUD(db)
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
