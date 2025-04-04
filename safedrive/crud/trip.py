from fastapi import HTTPException
from pymysql import IntegrityError
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
        
    def batch_create(self, db: Session, objs_in: List["TripCreate"]) -> List["Trip"]:
            db_objs = []
            skipped_count = 0

            for obj_in in objs_in:
                obj_data = obj_in.model_dump()

                # Convert UUID fields if needed
                if 'driverProfileId' in obj_data and isinstance(obj_data['driverProfileId'], str):
                    obj_data['driverProfileId'] = UUID(obj_data['driverProfileId'])

                try:
                    db_obj = self.model(**obj_data)
                    db.add(db_obj)
                    db.flush()
                    db_objs.append(db_obj)
                except IntegrityError as e:
                    db.rollback()
                    skipped_count += 1
                    logger.warning(f"Skipping Trip record due to IntegrityError: {str(e)}")
                except Exception as e:
                    db.rollback()
                    skipped_count += 1
                    logger.error(f"Unexpected error inserting Trip record: {str(e)}")

            db.commit()

            for db_obj in db_objs:
                db.refresh(db_obj)
                # Optionally log: logger.info(f"Created Trip with ID: {db_obj.id}")

            logger.info(f"Batch inserted {len(db_objs)} Trip records. Skipped {skipped_count}.")
            return db_objs

    def batch_delete(self, db: Session, ids: List[int]) -> None:
        """
        All-or-nothing batch delete. 
        """
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
          
            # Convert UUID fields to strings
            for uuid_field in ['trip_id', 'driverProfileId']:  # Adjust the fields based on your schema
                if uuid_field in obj_data and isinstance(obj_data[uuid_field], str):
                    obj_data[uuid_field] = UUID(obj_data[uuid_field])  # Convert to 36-character string format

            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created trip with ID: {db_obj.id}")
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

    def get_all(self, db: Session, skip: int = 0, limit: int = 5000) -> List[Trip]:
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

            # Convert UUID fields to strings
            for uuid_field in ['id', 'driverProfileId']:
                if uuid_field in obj_data and isinstance(obj_data[uuid_field], str):
                    obj_data[uuid_field] = UUID(obj_data[uuid_field])

            # Set updated fields
            for field, value in obj_data.items():
                setattr(db_obj, field, value)

            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated trip with ID: {db_obj.id}")
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
            obj = db.query(self.model).filter(self.model.id == id).first()
            if obj:
                db.delete(obj)
                db.commit()
                db.refresh(obj)
                logger.info(f"Deleted trip with ID: {id}")
                return obj
            else:
                logger.warning(f"Trip with ID {id} not found for deletion.")
                return None
        except Exception as e:
            db.rollback()
            logger.exception("Error deleting trip from database.")
            raise

    def batch_create(self, db: Session, objs_in: List[TripCreate]) -> List[Trip]:
        try:
            db_objs = []

            for obj_in in objs_in:
                obj_data = obj_in.model_dump()

                # Convert UUID fields if needed
                if 'driverProfileId' in obj_data and isinstance(obj_data['driverProfileId'], str):
                    obj_data['driverProfileId'] = UUID(obj_data['driverProfileId'])

                # Create a new Trip instance
                db_obj = self.model(**obj_data)
                db_objs.append(db_obj)

            db.add_all(db_objs)
            db.commit()
            db.flush()

            for db_obj in db_objs:
                db.refresh(db_obj)
                # Optionally log creation: logger.info(f"Created Trip with ID: {db_obj.id}")

            return db_objs

        except Exception as e:
            db.rollback()
            # Log error as appropriate
            raise HTTPException(status_code=500, detail="An unexpected error occurred during batch creation.\n"+e)

# Initialize CRUD instance for Trip
trip_crud = CRUDTrip(Trip)