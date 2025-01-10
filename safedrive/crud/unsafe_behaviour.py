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
            db_objs = []
            skipped_count = 0

            for data in data_in:
                obj_data = data.model_dump()

                # Convert string UUID fields to actual UUID objects
                for uuid_field in ['id', 'trip_id', 'location_id', 'driver_profile_id']:
                    if uuid_field in obj_data and isinstance(obj_data[uuid_field], str):
                        obj_data[uuid_field] = UUID(obj_data[uuid_field])

                # If an ID is provided, check for duplicates
                record_id = obj_data.get('id')
                if record_id is not None:
                    existing_record = db.query(self.model).filter_by(id=record_id).first()
                    if existing_record:
                        logger.info(f"Skipping duplicate UnsafeBehaviour with ID {record_id}")
                        skipped_count += 1
                        continue

                db_obj = self.model(**obj_data)
                db.add(db_obj)
                db_objs.append(db_obj)

            db.flush()
            db.commit()

            for obj in db_objs:
                db.refresh(obj)

            logger.info(f"Batch inserted {len(db_objs)} UnsafeBehaviour records. Skipped {skipped_count} duplicates.")
            return db_objs

        except IntegrityError as e:
            db.rollback()
            logger.error(f"IntegrityError during batch insertion of UnsafeBehaviour: {str(e)}")
            raise HTTPException(status_code=400, detail="Database integrity error occurred.")
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

            # Convert UUID fields to strings
            for uuid_field in ['id', 'trip_id', 'location_id', 'driverProfileId']:
                if uuid_field in obj_data and isinstance(obj_data[uuid_field], str):
                    obj_data[uuid_field] = UUID(obj_data[uuid_field])  # Convert to 36-character string format

            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created unsafe behaviour with ID: {db_obj.id}")
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
            behaviour = db.query(self.model).filter(self.model.id == id).first()
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
                    setattr(db_obj, field, obj_data[field])
                else:
                    setattr(db_obj, field, obj_data[field])
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated unsafe behaviour with ID: {db_obj.id}")
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
            obj = db.query(self.model).filter(self.model.id == id).first()
            if obj:
                db.delete(obj)
                db.commit()
                db.refresh(obj)
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