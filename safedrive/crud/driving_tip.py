from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional
from safedrive.models.driving_tip import DrivingTip, generate_uuid_binary
from safedrive.schemas.driving_tip_sch import DrivingTipCreate, DrivingTipUpdate
import logging
from safedrive.crud.driver_profile import driver_profile_crud

logger = logging.getLogger(__name__)

class CRUDDrivingTip:
    """
    CRUD operations for DrivingTip.

    Methods:
    - **create**: Adds a new DrivingTip record.
    - **get**: Retrieves a DrivingTip by UUID.
    - **get_all**: Retrieves all DrivingTips.
    - **update**: Updates a DrivingTip record.
    - **delete**: Deletes a DrivingTip record.
    """
    def __init__(self, model):
        self.model = model

    def create(self, db: Session, obj_in: DrivingTipCreate) -> DrivingTip:
        try:
            # Convert UUID fields to the appropriate format for the database
            db_obj = self.model(
                **obj_in.model_dump(exclude={'profile_id'}),
                tip_id=generate_uuid_binary(),
                profile_id=obj_in.profile_id.bytes if isinstance(obj_in.profile_id, UUID) else obj_in.profile_id
            )
            db.add(db_obj)
            db.commit()
            logger.info(f"Created DrivingTip with ID: {db_obj.tip_id}")
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error while creating DrivingTip: {e.orig}")
            raise ValueError("Duplicate entry or integrity constraint violated.")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error while creating DrivingTip: {str(e)}")
            raise ValueError("Database error occurred.")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error while creating DrivingTip: {str(e)}")
            raise ValueError("Unexpected error occurred.")

    def get(self, db: Session, id: UUID) -> Optional[DrivingTip]:
        try:
            tip = db.query(self.model).filter(self.model.tip_id == id.bytes).first()
            if tip:
                logger.info(f"Retrieved DrivingTip with ID: {id}")
            else:
                logger.warning(f"DrivingTip with ID {id} not found.")
            return tip
        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving DrivingTip: {str(e)}")
            raise ValueError("Error retrieving data from the database.")

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[DrivingTip]:
        try:
            tips = db.query(self.model).offset(skip).limit(limit).all()
            logger.info(f"Retrieved {len(tips)} DrivingTips.")
            return tips
        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving all DrivingTips: {str(e)}")
            raise ValueError("Error retrieving data from the database.")

    def update(self, db: Session, db_obj: DrivingTip, obj_in: DrivingTipUpdate) -> DrivingTip:
        obj_data = obj_in.model_dump(exclude_unset=True)
        obj_data['profile_id'] = obj_in.profile_id.bytes if isinstance(obj_in.profile_id, UUID) else obj_in.profile_id
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
        db.add(db_obj)
        try:
            db.commit()
            logger.info(f"Updated DrivingTip with ID: {db_obj.tip_id}")
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error while updating DrivingTip: {e.orig}")
            raise ValueError("Duplicate entry or integrity constraint violated.")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error while updating DrivingTip: {str(e)}")
            raise ValueError("Database error occurred.")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error while updating DrivingTip: {str(e)}")
            raise ValueError("Unexpected error occurred.")

    def delete(self, db: Session, id: UUID) -> Optional[DrivingTip]:
        try:
            obj = db.query(self.model).filter(self.model.tip_id == id.bytes).first()
            if obj:
                db.delete(obj)
                db.commit()
                logger.info(f"Deleted DrivingTip with ID: {id}")
                return obj
            else:
                logger.warning(f"DrivingTip with ID {id} not found for deletion.")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error while deleting DrivingTip: {str(e)}")
            raise ValueError("Error deleting data from the database.")
            
driving_tip_crud = CRUDDrivingTip(DrivingTip)