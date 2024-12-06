from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
import logging

from safedrive.models.unsafe_behaviour import UnsafeBehaviour
from safedrive.schemas.unsafe_behaviour import UnsafeBehaviourCreate, UnsafeBehaviourUpdate

logger = logging.getLogger(__name__)

class CRUDUnsafeBehaviour:
    """
    CRUD operations for the UnsafeBehaviour model.
    """

    def __init__(self, model):
        """
        Initialize the CRUD object with a database model.

        :param model: The SQLAlchemy model class.
        """
        self.model = model
        
    def batch_create(self, db: Session, data_in: List[UnsafeBehaviourCreate]) -> List[UnsafeBehaviour]:
        try:
            db_objs = [self.model(**data.model_dump()) for data in data_in]
            db.bulk_save_objects(db_objs)
            db.commit()
            logger.info(f"Batch inserted {len(db_objs)} UnsafeBehaviour records.")
            return db_objs
        except Exception as e:
            db.rollback()
            logger.error(f"Error during batch insertion of UnsafeBehaviour: {str(e)}")
            raise e

    def batch_delete(self, db: Session, ids: List[int]) -> None:
        try:
            db.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session=False)
            db.commit()
            logger.info(f"Batch deleted {len(ids)} UnsafeBehaviour records.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error during batch deletion of UnsafeBehaviour: {str(e)}")
            raise e

    def create(self, db: Session, obj_in: UnsafeBehaviourCreate) -> UnsafeBehaviour:
        """
        Create a new unsafe behaviour record in the database.

        :param db: The database session.
        :param obj_in: The schema with input data for creation.
        :return: The created unsafe behaviour.
        """
        try:
            obj_data = obj_in.model_dump()
            # Convert UUID fields to bytes
            if 'trip_id' in obj_data and isinstance(obj_data['trip_id'], UUID):
                obj_data['trip_id'] = obj_data['trip_id'].bytes
            if 'location_id' in obj_data and isinstance(obj_data['location_id'], UUID):
                obj_data['location_id'] = obj_data['location_id'].bytes
            if 'driver_profile_id' in obj_data and isinstance(obj_data['driver_profile_id'], UUID):
                obj_data['driver_profile_id'] = obj_data['driver_profile_id'].bytes
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created unsafe behaviour with ID: {db_obj.id.hex()}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.exception("Error creating unsafe behaviour in database.")
            raise e

    def get(self, db: Session, id: UUID) -> Optional[UnsafeBehaviour]:
        """
        Retrieve an unsafe behaviour record by ID.

        :param db: The database session.
        :param id: The UUID of the unsafe behaviour to retrieve.
        :return: The retrieved unsafe behaviour or None if not found.
        """
        try:
            behaviour = db.query(self.model).filter(self.model.id == id.bytes).first()
            if behaviour:
                logger.info(f"Found unsafe behaviour with ID: {id}")
            else:
                logger.warning(f"No unsafe behaviour found with ID: {id}")
            return behaviour
        except Exception as e:
            logger.exception("Error retrieving unsafe behaviour from database.")
            raise e

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[UnsafeBehaviour]:
        """
        Retrieve all unsafe behaviour records from the database.

        :param db: The database session.
        :param skip: Number of records to skip.
        :param limit: Maximum number of records to retrieve.
        :return: A list of unsafe behaviour records.
        """
        try:
            behaviours = db.query(self.model).offset(skip).limit(limit).all()
            logger.info(f"Retrieved {len(behaviours)} unsafe behaviour records from database.")
            return behaviours
        except Exception as e:
            logger.exception("Error retrieving unsafe behaviours from database.")
            raise e

    def update(self, db: Session, db_obj: UnsafeBehaviour, obj_in: UnsafeBehaviourUpdate) -> UnsafeBehaviour:
        """
        Update an existing unsafe behaviour record.

        :param db: The database session.
        :param db_obj: The existing database object to update.
        :param obj_in: The schema with updated data.
        :return: The updated unsafe behaviour.
        """
        try:
            obj_data = obj_in.dict(exclude_unset=True)
            for field in obj_data:
                if field in ['trip_id', 'location_id'] and isinstance(obj_data[field], UUID):
                    setattr(db_obj, field, obj_data[field].bytes)
                else:
                    setattr(db_obj, field, obj_data[field])
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated unsafe behaviour with ID: {db_obj.id.hex()}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.exception("Error updating unsafe behaviour in database.")
            raise e

    def delete(self, db: Session, id: UUID) -> Optional[UnsafeBehaviour]:
        """
        Delete an unsafe behaviour record by ID.

        :param db: The database session.
        :param id: The UUID of the unsafe behaviour to delete.
        :return: The deleted unsafe behaviour or None if not found.
        """
        try:
            obj = db.query(self.model).filter(self.model.id == id.bytes).first()
            if obj:
                db.delete(obj)
                db.commit()
                logger.info(f"Deleted unsafe behaviour with ID: {id}")
                return obj
            else:
                logger.warning(f"Unsafe behaviour with ID {id} not found for deletion.")
                return None
        except Exception as e:
            db.rollback()
            logger.exception("Error deleting unsafe behaviour from database.")
            raise e

# Initialize CRUD instance for UnsafeBehaviour
unsafe_behaviour_crud = CRUDUnsafeBehaviour(UnsafeBehaviour)