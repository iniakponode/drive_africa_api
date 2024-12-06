from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from safedrive.models.cause import Cause, generate_uuid_binary
from safedrive.schemas.cause import CauseCreate, CauseUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDCause:
    """
    CRUD operations for Cause.

    Methods:
    - **create**: Adds a new Cause record.
    - **get**: Retrieves a Cause by UUID.
    - **get_all**: Retrieves all Causes.
    - **update**: Updates a Cause record.
    - **delete**: Deletes a Cause record.
    """
    def __init__(self, model):
        self.model = model

    def create(self, db: Session, obj_in: CauseCreate) -> Cause:
        # Initialize Cause instance with model_dump of obj_in
        db_obj = self.model(**obj_in.model_dump(), id=generate_uuid_binary())
        
        # Check if 'unsafe_behaviour_id' exists and is a UUID, then convert to binary if necessary
        if hasattr(db_obj, 'unsafe_behaviour_id') and isinstance(getattr(db_obj, 'unsafe_behaviour_id'), UUID):
            setattr(db_obj, 'unsafe_behaviour_id', getattr(db_obj, 'unsafe_behaviour_id').bytes)
        
        db.add(db_obj)
        try:
            db.commit()
            logger.info(f"Created Cause with ID: {db_obj.id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating Cause: {str(e)}")
            raise HTTPException(status_code=500, detail="Error creating Cause")
        
        db.refresh(db_obj)
        return db_obj


    def get(self, db: Session, id: UUID) -> Optional[Cause]:
        cause = db.query(self.model).filter(self.model.id == id.bytes).first()
        if cause:
            logger.info(f"Retrieved Cause with ID: {id}")
        else:
            logger.warning(f"Cause with ID {id} not found.")
        return cause

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Cause]:
        causes = db.query(self.model).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(causes)} Causes.")
        return causes

    def update(self, db: Session, db_obj: Cause, obj_in: CauseUpdate) -> Cause:
        obj_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
        db.add(db_obj)
        try:
            db.commit()
            logger.info(f"Updated Cause with ID: {db_obj.id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating Cause: {str(e)}")
            raise e
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: UUID) -> Optional[Cause]:
        obj = db.query(self.model).filter(self.model.id == id.bytes).first()
        if obj:
            db.delete(obj)
            try:
                db.commit()
                logger.info(f"Deleted Cause with ID: {id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Error deleting Cause: {str(e)}")
                raise e
        else:
            logger.warning(f"Cause with ID {id} not found for deletion.")
        return obj

# Initialize CRUD instance for Cause
cause_crud = CRUDCause(Cause)