from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from datetime import datetime
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
            # Convert the Pydantic model to a dictionary
            data = obj_in.model_dump()
            
            # Convert UUID fields if they are provided as strings
            for uuid_field in ['tip_id', 'profile_id']:
                value = data.get(uuid_field)
                if value and isinstance(value, str):
                    try:
                        data[uuid_field] = UUID(value)
                    except Exception as e:
                        logger.error(f"Error converting {uuid_field} with value '{value}' to UUID: {e}")
                        raise ValueError(f"Invalid UUID format for field '{uuid_field}'")
            
            # Create the database object using the dumped data
            db_obj = self.model(**data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created DrivingTip with ID: {db_obj.tip_id}")
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
            tip = db.query(self.model).filter(self.model.tip_id == id).first()
            if tip:
                logger.info(f"Retrieved DrivingTip with ID: {id}")
            else:
                logger.warning(f"DrivingTip with ID {id} not found.")
            return tip
        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving DrivingTip: {str(e)}")
            raise ValueError("Error retrieving data from the database.")

    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        profile_id: Optional[UUID] = None,
        llm: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sync: Optional[bool] = None,
    ) -> List[DrivingTip]:
        try:
            query = db.query(self.model)
            if profile_id is not None:
                query = query.filter(self.model.profile_id == profile_id)
            if llm is not None:
                query = query.filter(self.model.llm == llm)
            if start_date is not None:
                query = query.filter(self.model.date >= start_date)
            if end_date is not None:
                query = query.filter(self.model.date <= end_date)
            if sync is not None:
                query = query.filter(self.model.sync == sync)
            tips = query.offset(skip).limit(limit).all()
            logger.info(f"Retrieved {len(tips)} DrivingTips.")
            return tips
        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving all DrivingTips: {str(e)}")
            raise ValueError("Error retrieving data from the database.")

    def update(self, db: Session, db_obj: DrivingTip, obj_in: DrivingTipUpdate) -> DrivingTip:
        
        
        
      
         # Convert UUID fields to strings
        for uuid_field in ['tip_id', 'profile_id']:  # Adjust the fields based on your schema
            if uuid_field in obj_in and isinstance(obj_in[uuid_field], str):
                obj_in[uuid_field] = UUID(obj_in[uuid_field])  # Convert to 36-character string format
        
        obj_data = obj_in.model_dump(exclude_unset=True)
       
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
        db.add(db_obj)
        try:
            db.commit()
            db.refresh(db_obj)
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
            obj = db.query(self.model).filter(self.model.tip_id == id).first()
            if obj:
                db.delete(obj)
                db.commit()
                db.refresh(obj)
                logger.info(f"Deleted DrivingTip with ID: {id}")
                return obj
            else:
                logger.warning(f"DrivingTip with ID {id} not found for deletion.")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error while deleting DrivingTip: {str(e)}")
            raise ValueError("Error deleting data from the database.")

    def batch_create(self, db: Session, data_in: List[DrivingTipCreate]) -> List[DrivingTip]:
        db_objs = []
        skipped_count = 0

        for tip in data_in:
            data = tip.model_dump()
            for uuid_field in ['tip_id', 'profile_id']:
                value = data.get(uuid_field)
                if value and isinstance(value, str):
                    try:
                        data[uuid_field] = UUID(value)
                    except Exception as e:
                        logger.error(f"Error converting {uuid_field} '{value}' to UUID: {e}")
                        skipped_count += 1
                        continue

            tip_id = data.get("tip_id")
            if tip_id:
                existing = db.query(self.model).filter_by(tip_id=tip_id).first()
                if existing:
                    logger.info(f"Skipping duplicate DrivingTip with ID {tip_id}")
                    skipped_count += 1
                    continue

            try:
                db_obj = self.model(**data)
                db.add(db_obj)
                db.flush()
                db_objs.append(db_obj)
            except Exception as e:
                db.rollback()
                skipped_count += 1
                logger.error(f"Error inserting DrivingTip: {str(e)}")

        db.commit()
        for obj in db_objs:
            db.refresh(obj)

        logger.info(f"Batch inserted {len(db_objs)} DrivingTips. Skipped {skipped_count}.")
        return db_objs

    def batch_delete(self, db: Session, ids: List[UUID]) -> None:
        try:
            db.query(self.model).filter(self.model.tip_id.in_(ids)).delete(synchronize_session=False)
            db.commit()
            logger.info(f"Batch deleted {len(ids)} DrivingTips.")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error while deleting DrivingTips: {str(e)}")
            raise ValueError("Error deleting data from the database.")
            
driving_tip_crud = CRUDDrivingTip(DrivingTip)
