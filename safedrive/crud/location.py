from pymysql import IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
import logging

from safedrive.models.location import Location
from safedrive.schemas.location import LocationCreate, LocationUpdate

logger = logging.getLogger(__name__)

class CRUDLocation:
    """
    CRUD operations for the Location model.
    """

    def __init__(self, model):
        """
        Initialize the CRUD object with a database model.

        :param model: The SQLAlchemy model class.
        """
        self.model = model

    def create(self, db: Session, obj_in: LocationCreate) -> Location:
        """
        Create a new Location record in the database.

        :param db: The database session.
        :param obj_in: The schema with input data for creation.
        :return: The created Location.
        """
        try:
            obj_data = obj_in.model_dump()

            # Convert UUID fields to string representation if necessary
            if 'id' in obj_data and isinstance(obj_data['id'], str):
                obj_data['id'] = UUID(obj_data['id'])  # Convert to 36-character string format

            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created location with ID: {db_obj.id}")
            return db_obj

        except Exception as e:
            db.rollback()
            logger.exception("Error creating location in database.")
            raise e


    def get(self, db: Session, id: UUID) -> Optional[Location]:
        """
        Retrieve a Location record by ID.

        :param db: The database session.
        :param id: The UUID of the Location to retrieve.
        :return: The retrieved Location or None if not found.
        """
        try:
            location = db.query(self.model).filter(self.model.id == id).first()
            if location:
                logger.info(f"Found location with ID: {id}")
            else:
                logger.warning(f"No location found with ID: {id}")
            return location
        except Exception as e:
            logger.exception("Error retrieving location from database.")
            raise e

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Location]:
        """
        Retrieve all Location records from the database.

        :param db: The database session.
        :param skip: Number of records to skip.
        :param limit: Maximum number of records to retrieve.
        :return: A list of Locations.
        """
        try:
            locations = db.query(self.model).offset(skip).limit(limit).all()
            logger.info(f"Retrieved {len(locations)} locations from database.")
            return locations
        except Exception as e:
            logger.exception("Error retrieving locations from database.")
            raise e

    def update(self, db: Session, db_obj: Location, obj_in: LocationUpdate) -> Location:
        """
        Update an existing Location record.

        :param db: The database session.
        :param db_obj: The existing database object to update.
        :param obj_in: The schema with updated data.
        :return: The updated Location.
        """
        try:
            obj_data = obj_in.dict(exclude_unset=True)
            for field in obj_data:
                setattr(db_obj, field, obj_data[field])
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated location with ID: {db_obj.id}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.exception("Error updating location in database.")
            raise e

    def delete(self, db: Session, id: UUID) -> Optional[Location]:
        """
        Delete a Location record by ID.

        :param db: The database session.
        :param id: The UUID of the Location to delete.
        :return: The deleted Location or None if not found.
        """
        try:
            obj = db.query(self.model).filter(self.model.id == id).first()
            if obj:
                db.delete(obj)
                db.commit()
                db.refresh(obj)
                logger.info(f"Deleted location with ID: {id}")
                return obj
            else:
                logger.warning(f"Location with ID {id} not found for deletion.")
                return None
        except Exception as e:
            db.rollback()
            logger.exception("Error deleting location from database.")
            raise e

    def batch_create(self, db: Session, data_in: List["LocationCreate"]) -> List["Location"]:
        """
        Batch create Location records, skipping any that fail constraints.
        """
        db_objs = []
        skipped_count = 0

        for data in data_in:
            obj_data = data.model_dump()

            # Convert string UUID to UUID object if needed
            if 'id' in obj_data and isinstance(obj_data['id'], str):
                obj_data['id'] = UUID(obj_data['id'])

            try:
                db_obj = self.model(**obj_data)
                db.add(db_obj)
                db.flush()  # Insert now
                db_objs.append(db_obj)
            except IntegrityError as e:
                db.rollback()
                skipped_count += 1
                logger.warning(f"Skipping Location due to IntegrityError: {str(e)}")
            except Exception as e:
                db.rollback()
                skipped_count += 1
                logger.error(f"Unexpected error inserting Location: {str(e)}")

        db.commit()

        for db_obj in db_objs:
            db.refresh(db_obj)

        logger.info(f"Batch created {len(db_objs)} Location records. Skipped {skipped_count}.")
        return db_objs


    def batch_delete(self, db: Session, ids: List[UUID]) -> None:
        """
        All-or-nothing batch delete. If you wanted partial success, you'd loop over each ID.
        """
        try:
            deleted_count = db.query(self.model).filter(
                self.model.id.in_([id_ for id_ in ids])
            ).delete(synchronize_session=False)
            db.commit()
            logger.info(f"Batch deleted {deleted_count} Location records.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error in batch delete Location: {str(e)}")
            raise e

# Initialize CRUD instance for Location
location_crud = CRUDLocation(Location)