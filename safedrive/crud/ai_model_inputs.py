from fastapi import HTTPException
from pymysql import IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional
import logging

from safedrive.models.ai_model_input import AIModelInput
from safedrive.schemas.ai_model_input import AIModelInputCreate, AIModelInputUpdate

logger = logging.getLogger(__name__)

class CRUDModelInputs:
    """
    CRUD operations for AIModelInput model.
    """

    def __init__(self, model):
        """
        Initialize the CRUD object with a database model.

        :param model: The SQLAlchemy model class.
        """
        self.model = model
    
    def batch_create(self, db: Session, data_in: List["AIModelInputCreate"]) -> List[str]:
        """
        Insert multiple AIModelInput records, skipping those that fail constraints.
        
        :param db: SQLAlchemy Session object.
        :param data_in: A list of `AIModelInputCreate` objects to insert.
        :return: A list of string IDs that were successfully inserted.
        """
        db_objs = []
        skipped_count = 0

        for data in data_in:
            fields = data.model_dump()

            # Convert string UUIDs to actual UUID objects if needed
            if isinstance(fields.get('id'), str):
                fields['id'] = UUID(fields['id'])
            if isinstance(fields.get('trip_id'), str):
                fields['trip_id'] = UUID(fields['trip_id'])
            if isinstance(fields.get('driverProfileId'), str):
                fields['driverProfileId'] = UUID(fields['driverProfileId'])

            record_id = fields.get('id')
            if record_id is not None:
                existing_record = db.query(self.model).filter_by(id=record_id).first()
                if existing_record:
                    logger.info(f"Skipping duplicate AIModelInput with ID {record_id}")
                    skipped_count += 1
                    continue

            # Attempt to create and flush each record individually
            try:
                db_obj = self.model(**fields)
                db.add(db_obj)
                db.flush()  # flush so we can catch any IntegrityErrors right here
                db_objs.append(db_obj)

            except IntegrityError as e:
                db.rollback()  # rollback this one record
                logger.warning(
                    f"Skipping AIModelInput due to IntegrityError: {str(e)}. "
                    f"Fields: {fields}"
                )
                skipped_count += 1
                continue  # move on to the next record

            except Exception as e:
                # If something else goes wrong, decide if you want to skip or raise
                db.rollback()
                logger.error(f"Unexpected error inserting AIModelInput: {str(e)}. Skipping this record.")
                skipped_count += 1
                continue

        # Commit all successfully flushed objects
        db.commit()

        # Refresh each to get updated data from DB (like auto-generated timestamps)
        for obj in db_objs:
            db.refresh(obj)

        logger.info(f"Batch inserted {len(db_objs)} records. Skipped {skipped_count} records.")
        return [str(obj.id) for obj in db_objs]



    def batch_delete(self, db: Session, ids: List[int]) -> None:
        try:
            db.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session=False)
            db.commit()

            logger.info(f"Batch deleted {len(ids)} AIModelInput records.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error during batch deletion of AIModelInput: {str(e)}")
            raise e

    def create(self, db: Session, obj_in: AIModelInputCreate) -> AIModelInput:
        """
        Create a new AI model input record in the database.

        :param db: The database session.
        :param obj_in: The schema with input data for creation.
        :return: The created AI model input.
        """
        try:
            obj_data = obj_in.model_dump()
            # Convert UUID fields to strings
            for uuid_field in ['trip_id', 'id', 'driver_profile_id']:
                if uuid_field in obj_data and isinstance(obj_data[uuid_field], str):
                    obj_data[uuid_field] = UUID(obj_data[uuid_field])  # Convert to 36-character UUID string

            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created AI model input with ID: {db_obj.id}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.exception("Error creating AI model input in database.")
            raise

    def get(self, db: Session, id: UUID) -> Optional[AIModelInput]:
        """
        Retrieve an AI model input record by ID.

        :param db: The database session.
        :param id: The UUID of the AI model input to retrieve.
        :return: The retrieved AI model input or None if not found.
        """
        try:
            ai_input = db.query(self.model).filter(self.model.id == id.bytes).first()
            if ai_input:
                logger.info(f"Found AI model input with ID: {id}")
            else:
                logger.warning(f"No AI model input found with ID: {id}")
            return ai_input
        except Exception as e:
            logger.exception("Error retrieving AI model input from database.")
            raise

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[AIModelInput]:
        """
        Retrieve all AI model input records from the database.

        :param db: The database session.
        :param skip: Number of records to skip.
        :param limit: Maximum number of records to retrieve.
        :return: A list of AI model inputs.
        """
        try:
            inputs = db.query(self.model).offset(skip).limit(limit).all()
            logger.info(f"Retrieved {len(inputs)} AI model inputs from database.")
            return inputs
        except Exception as e:
            logger.exception("Error retrieving AI model inputs from database.")
            raise

    def update(self, db: Session, db_obj: AIModelInput, obj_in: AIModelInputUpdate) -> AIModelInput:
        """
        Update an existing AI model input record.

        :param db: The database session.
        :param db_obj: The existing database object to update.
        :param obj_in: The schema with updated data.
        :return: The updated AI model input.
        """
        try:
            obj_data = obj_in.dict(exclude_unset=True)
            for field in obj_data:
                # Handle UUID fields if necessary
                if isinstance(getattr(db_obj, field), bytes) and isinstance(obj_data[field], UUID):
                    setattr(db_obj, field, obj_data[field])
                else:
                    setattr(db_obj, field, obj_data[field])
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated AI model input with ID: {db_obj.id}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.exception("Error updating AI model input in database.")
            raise

    def delete(self, db: Session, id: UUID) -> Optional[AIModelInput]:
        """
        Delete an AI model input record by ID.

        :param db: The database session.
        :param id: The UUID of the AI model input to delete.
        :return: The deleted AI model input or None if not found.
        """
        try:
            obj = db.query(self.model).filter(self.model.id == id.bytes).first()
            if obj:
                db.delete(obj)
                db.commit()
                db.refresh(obj)
                logger.info(f"Deleted AI model input with ID: {id}")
                return obj
            else:
                logger.warning(f"AI model input with ID {id} not found for deletion.")
                return None
        except Exception as e:
            db.rollback()
            logger.exception("Error deleting AI model input from database.")
            raise

# Initialize CRUD instance for AIModelInputs
ai_model_inputs_crud = CRUDModelInputs(AIModelInput)