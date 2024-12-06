from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
import logging

from safedrive.models.trip import Trip
from safedrive.schemas.trip import TripCreate, TripUpdate

logger = logging.getLogger(__name__)

class CRUDTrip:
    """
    CRUD operations for the Trip model.
    """

    def __init__(self, model):
        """
        Initialize the CRUD object with a database model.

        :param model: The SQLAlchemy model class.
        """
        self.model = model
        
    def batch_create(self, db: Session, data_in: List[TripCreate]) -> List[Trip]:
        try:
            db_objs = [self.model(**data.model_dump()) for data in data_in]
            db.bulk_save_objects(db_objs)
            db.commit()
            logger.info(f"Batch inserted {len(db_objs)} Trip records.")
            return db_objs
        except Exception as e:
            db.rollback()
            logger.error(f"Error during batch insertion of Trip: {str(e)}")
            raise e

    def batch_delete(self, db: Session, ids: List[int]) -> None:
        try:
            db.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session=False)
            db.commit()
            logger.info(f"Batch deleted {len(ids)} Trip records.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error during batch deletion of Trip: {str(e)}")
            raise e

    def create(self, db: Session, obj_in: TripCreate) -> Trip:
        """
        Create a new trip record in the database.

        :param db: The database session.
        :param obj_in: The schema with input data for creation.
        :return: The created trip.
        """
        try:
            obj_data = obj_in.model_dump()
            # Convert UUID fields to bytes
            if 'driver_profile_id' in obj_data and isinstance(obj_data['driver_profile_id'], UUID):
                obj_data['driver_profile_id'] = obj_data['driver_profile_id'].bytes
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created trip with ID: {db_obj.id.hex()}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.exception("Error creating trip in database.")
            raise

    def get(self, db: Session, id: UUID) -> Optional[Trip]:
        """
        Retrieve a trip record by ID.

        :param db: The database session.
        :param id: The UUID of the trip to retrieve.
        :return: The retrieved trip or None if not found.
        """
        try:
            trip = db.query(self.model).filter(self.model.id == id.bytes).first()
            if trip:
                logger.info(f"Found trip with ID: {id}")
            else:
                logger.warning(f"No trip found with ID: {id}")
            return trip
        except Exception as e:
            logger.exception("Error retrieving trip from database.")
            raise

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Trip]:
        """
        Retrieve all trip records from the database.

        :param db: The database session.
        :param skip: Number of records to skip.
        :param limit: Maximum number of records to retrieve.
        :return: A list of trip records.
        """
        try:
            trips = db.query(self.model).offset(skip).limit(limit).all()
            logger.info(f"Retrieved {len(trips)} trips from database.")
            return trips
        except Exception as e:
            logger.exception("Error retrieving trips from database.")
            raise

    def update(self, db: Session, db_obj: Trip, obj_in: TripUpdate) -> Trip:
        """
        Update an existing trip record.

        :param db: The database session.
        :param db_obj: The existing database object to update.
        :param obj_in: The schema with updated data.
        :return: The updated trip.
        """
        try:
            obj_data = obj_in.dict(exclude_unset=True)
            for field in obj_data:
                if field == 'driver_profile_id' and isinstance(obj_data[field], UUID):
                    setattr(db_obj, field, obj_data[field].bytes)
                else:
                    setattr(db_obj, field, obj_data[field])
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated trip with ID: {db_obj.id.hex()}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.exception("Error updating trip in database.")
            raise

    def delete(self, db: Session, id: UUID) -> Optional[Trip]:
        """
        Delete a trip record by ID.

        :param db: The database session.
        :param id: The UUID of the trip to delete.
        :return: The deleted trip or None if not found.
        """
        try:
            obj = db.query(self.model).filter(self.model.id == id.bytes).first()
            if obj:
                db.delete(obj)
                db.commit()
                logger.info(f"Deleted trip with ID: {id}")
                return obj
            else:
                logger.warning(f"Trip with ID {id} not found for deletion.")
                return None
        except Exception as e:
            db.rollback()
            logger.exception("Error deleting trip from database.")
            raise

# Initialize CRUD instance for Trip
trip_crud = CRUDTrip(Trip)