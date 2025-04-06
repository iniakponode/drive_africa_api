from fastapi import HTTPException
from pymysql import IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
import logging

from safedrive.models.driver_profile import DriverProfile
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

        for idx, obj_in in enumerate(objs_in):
            obj_data = obj_in.model_dump()

            # 1) Log the incoming data
            logger.info(f"[batch_create] Processing item {idx+1}/{len(objs_in)}: {obj_data}")

            # 2) Convert driverProfileId if needed
            if 'driverProfileId' in obj_data and isinstance(obj_data['driverProfileId'], str):
                raw_str = obj_data['driverProfileId']
                logger.debug(f"[batch_create] Converting driverProfileId from string '{raw_str}' to UUID.")
                try:
                    obj_data['driverProfileId'] = UUID(raw_str)
                except ValueError as e:
                    logger.error(f"[batch_create] Invalid UUID string for driverProfileId '{raw_str}': {e}")
                    skipped_count += 1
                    continue

            # 3) (Optional) Check that driverProfileId exists in DB
            driver_profile_id = obj_data.get("driverProfileId")
            if driver_profile_id:
                profile = (
                    db.query(DriverProfile)
                    .filter(DriverProfile.driverProfileId == driver_profile_id.bytes)
                    .first()
                )
                if not profile:
                    logger.warning(
                        f"[batch_create] Skipping Trip record: driverProfileId {driver_profile_id} "
                        "not found in driver_profile table."
                    )
                    skipped_count += 1
                    continue

            # 4) Attempt to create & flush
            try:
                db_obj = self.model(**obj_data)
                db.add(db_obj)
                db.flush()  # If this fails, we rollback & skip below
                # Only append if flush succeeded (object is now persistent)
                db_objs.append(db_obj)
                logger.debug(
                    f"[batch_create] Inserted Trip with ID = {db_obj.id_uuid} "
                    f"and driverProfileId = {db_obj.driver_profile_id_uuid}"
                )
            except IntegrityError as e:
                db.rollback()
                skipped_count += 1
                logger.warning(f"[batch_create] Skipping Trip record due to IntegrityError: {str(e)}")
                # continue to next trip
            except Exception as e:
                db.rollback()
                skipped_count += 1
                logger.error(f"[batch_create] Unexpected error inserting Trip record: {str(e)}")
                # continue to next trip

        # 5) Commit all successful inserts (i.e., those that didn't rollback)
        db.commit()

        # 6) Refresh each successfully inserted object
        for db_obj in db_objs:
            db.refresh(db_obj)
            logger.debug(f"[batch_create] Refreshed Trip after commit: ID = {db_obj.id_uuid}")

        # 7) Final summary
        logger.info(f"[batch_create] Successfully inserted {len(db_objs)} Trip records. Skipped {skipped_count}.")
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
        :param db_obj: The existing database object to update (must not be None).
        :param obj_in: The schema with updated data.
        :return: The updated Trip object.
        :raises HTTPException(404): if trip not found.
        :raises HTTPException(400): for foreign key or data integrity errors.
        """
        # 1) If the trip does not exist in DB, raise a 404
        if not db_obj:
            logger.warning("Attempted to update a trip that does not exist in DB.")
            raise HTTPException(status_code=404, detail="Trip not found")

        try:
            # 2) Only allow partial updates (exclude unset fields)
            obj_data = obj_in.model_dump(exclude_unset=True)

            # 3) Convert UUID fields from string → Python UUID (if needed)
            #    Typically we do not update 'id' if it's the primary key.
            if 'id' in obj_data:
                logger.warning("Attempted to update trip primary key 'id'—skipping.")
                obj_data.pop('id')  # Usually you don't allow this, or you raise an error.

            if 'driverProfileId' in obj_data and isinstance(obj_data['driverProfileId'], str):
                raw_str = obj_data['driverProfileId']
                try:
                    obj_data['driverProfileId'] = UUID(raw_str)
                except ValueError as exc:
                    logger.exception(f"Invalid driverProfileId UUID string '{raw_str}'.")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid UUID for driverProfileId: {raw_str}"
                    )

            # 4) (Optional) If driverProfileId is changing, check that it exists
            new_driver_profile_id = obj_data.get('driverProfileId')
            if new_driver_profile_id is not None:
                driver_profile_exists = db.query(DriverProfile).filter(
                    DriverProfile.driverProfileId == new_driver_profile_id.bytes
                ).first()
                if not driver_profile_exists:
                    logger.warning(
                        f"Update request provided driverProfileId={new_driver_profile_id}, "
                        f"but no matching DriverProfile was found."
                    )
                    raise HTTPException(
                        status_code=400,
                        detail="No matching driver profile found for provided driverProfileId."
                    )

            # 5) Update fields on db_obj
            for field, value in obj_data.items():
                setattr(db_obj, field, value)

            # 6) Commit & refresh
            db.commit()
            db.refresh(db_obj)

            logger.info(f"Updated trip with ID: {db_obj.id_uuid} (db primary key bytes={db_obj.id}).")
            return db_obj

        except IntegrityError as e:
            # Commonly foreign key violations or uniqueness constraints
            db.rollback()
            logger.exception(f"IntegrityError while updating trip: {e}")
            raise HTTPException(
                status_code=400,
                detail="Foreign key or unique constraint failed."
            )
        except Exception as e:
            # Catch-all for other unexpected errors
            db.rollback()
            logger.exception("Error updating trip in database.")
            raise HTTPException(status_code=500, detail="Internal Server Error")


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
            raise HTTPException(status_code=500, detail="An unexpected error occurred during batch creation.\n"+e)

# Initialize CRUD instance for Trip
trip_crud = CRUDTrip(Trip)