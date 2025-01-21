from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from uuid import UUID

from safedrive.database.db import get_db
from safedrive.models.alcohol_questionnaire import AlcoholQuestionnaire
from safedrive.schemas.alcohol_questionnaire import (
    AlcoholQuestionnaireCreateSchema,
    AlcoholQuestionnaireResponseSchema,
)

router = APIRouter()

class AlcoholQuestionnaireCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, questionnaire_data: AlcoholQuestionnaireCreateSchema) -> AlcoholQuestionnaire:
        try:
            db_questionnaire = AlcoholQuestionnaire(
                id=questionnaire_data.id,
                driverProfileId=questionnaire_data.driverProfileId,
                drankAlcohol=questionnaire_data.drankAlcohol,
                selectedAlcoholTypes=questionnaire_data.selectedAlcoholTypes,
                beerQuantity=questionnaire_data.beerQuantity,
                wineQuantity=questionnaire_data.wineQuantity,
                spiritsQuantity=questionnaire_data.spiritsQuantity,
                firstDrinkTime=questionnaire_data.firstDrinkTime,
                lastDrinkTime=questionnaire_data.lastDrinkTime,
                emptyStomach=questionnaire_data.emptyStomach,
                caffeinatedDrink=questionnaire_data.caffeinatedDrink,
                impairmentLevel=questionnaire_data.impairmentLevel,
                date=questionnaire_data.date,
                plansToDrive=questionnaire_data.plansToDrive,
            )

            self.db.add(db_questionnaire)
            self.db.commit()
            self.db.refresh(db_questionnaire)
            return db_questionnaire
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def get_by_id(self, questionnaire_id: UUID) -> AlcoholQuestionnaire:
        questionnaire = self.db.query(AlcoholQuestionnaire).filter(
            AlcoholQuestionnaire.id == questionnaire_id
        ).first()
        if not questionnaire:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alcohol questionnaire with ID {questionnaire_id} not found",
            )
        return questionnaire

    def get_all(self) -> List[AlcoholQuestionnaire]:
        try:
            return self.db.query(AlcoholQuestionnaire).all()
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def update(self, questionnaire_id: UUID, updated_data: AlcoholQuestionnaireCreateSchema) -> AlcoholQuestionnaire:
        questionnaire = self.get_by_id(questionnaire_id)
        try:
            for key, value in updated_data.dict().items():
                setattr(questionnaire, key, value)

            self.db.commit()
            self.db.refresh(questionnaire)
            return questionnaire
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def delete(self, questionnaire_id: UUID):
        questionnaire = self.get_by_id(questionnaire_id)
        try:
            self.db.delete(questionnaire)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )