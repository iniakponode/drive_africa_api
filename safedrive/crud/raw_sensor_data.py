from fastapi import HTTPException
from pymysql import IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
import logging

from safedrive.models.raw_sensor_data import RawSensorData
from safedrive.schemas.raw_sensor_data import RawSensorDataCreate, RawSensorDataUpdate

logger = logging.getLogger(__name__)

class CRUDRawSensorData:
    """
    CRUD operations for the RawSensorData model.
    """

    def __init__(self, model):
        """
        Initialize the CRUD object with a database model.

        :param model: The SQLAlchemy model class.
        """
        self.model = model

    def batch_create(self, db: Session, data_in: List["RawSensorDataCreate"]) -> List["RawSensorData"]:
        db_objs = []
        skipped_count = 0

        for data in data_in:
            obj_data = data.model_dump()

            # Convert string UUID fields to actual UUID objects
            for uuid_field in ["id", "location_id", "driverProfileId", "trip_id"]:
                if uuid_field in obj_data and isinstance(obj_data[uuid_field], str):
                    obj_data[uuid_field] = UUID(obj_data[uuid_field])

            # Duplicate check
            record_id = obj_data.get("id")
            if record_id:
                existing_record = db.query(self.model).filter_by(id=record_id).first()
                if existing_record:
                    logger.info(f"Skipping duplicate RawSensorData with ID {record_id}")
                    skipped_count += 1
                    continue

            try:
                db_obj = self.model(**obj_data)
                db.add(db_obj)
                db.flush()
                db_objs.append(db_obj)
            except IntegrityError as e:
                db.rollback()
                skipped_count += 1
                logger.warning(f"Skipping RawSensorData due to IntegrityError: {str(e)}")
            except Exception as e:
                db.rollback()
                skipped_count += 1
                logger.error(f"Error inserting RawSensorData: {str(e)}")

        db.commit()

        for obj in db_objs:
            db.refresh(obj)

        inserted_count = len(db_objs)
        logger.info(f"Batch inserted {inserted_count} RawSensorData records. Skipped {skipped_count}.")
        return db_objs


    def create(self, db: Session, obj_in: RawSensorDataCreate) -> RawSensorData:
        try:
            # Convert UUID fields to 36-character strings
            obj_in_data = obj_in.model_dump(exclude={'values'})
            for uuid_field in ['id', 'location_id', 'driverProfileId', 'trip_id']:
                if uuid_field in obj_in_data and isinstance(obj_in_data[uuid_field], str):
                    obj_in_data[uuid_field] = UUID(obj_in_data[uuid_field])

            db_obj = self.model(
                **obj_in_data,  # Unpack the modified dictionary
                values=obj_in.values  # Automatically serialize list as JSON
            )

            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created RawSensorData with ID: {db_obj.id}")
            return db_obj

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating RawSensorData: {str(e)}")
            raise e


    def get(self, db: Session, id: UUID) -> Optional[RawSensorData]:
        """
        Retrieve a raw sensor data record by ID.

        :param db: The database session.
        :param id: The UUID of the raw sensor data to retrieve.
        :return: The retrieved raw sensor data or None if not found.
        """
        try:
            data = db.query(self.model).filter(self.model.id == id).first()
            if data:
                logger.info(f"Found raw sensor data with ID: {id}")
            else:
                logger.warning(f"No raw sensor data found with ID: {id}")
            return data
        except Exception as e:
            logger.exception("Error retrieving raw sensor data from database.")
            raise

    def get_all(self, db: Session, skip: int = 0, limit: int = 5000) -> List[RawSensorData]:
        """
        Retrieve all raw sensor data records from the database.

        :param db: The database session.
        :param skip: Number of records to skip.
        :param limit: Maximum number of records to retrieve.
        :return: A list of raw sensor data records.
        """
        try:
            data_list = db.query(self.model).offset(skip).limit(limit).all()
            logger.info(f"Retrieved {len(data_list)} raw sensor data records from database.")
            return data_list
        except Exception as e:
            logger.exception("Error retrieving raw sensor data from database.")
            raise

    def update(self, db: Session, db_obj: RawSensorData, obj_in: RawSensorDataUpdate) -> RawSensorData:
        """
        Update an existing raw sensor data record.

        :param db: The database session.
        :param db_obj: The existing database object to update.
        :param obj_in: The schema with updated data.
        :return: The updated raw sensor data.
        """
        try:
            obj_data = obj_in.dict(exclude_unset=True)
            for field in obj_data:
                if field in ['location_id', 'trip_id'] and isinstance(obj_data[field], UUID):
                    setattr(db_obj, field, obj_data[field])
                else:
                    setattr(db_obj, field, obj_data[field])
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated raw sensor data with ID: {db_obj.id}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.exception("Error updating raw sensor data in database.")
            raise

    def delete(self, db: Session, id: UUID) -> Optional[RawSensorData]:
        """
        Delete a raw sensor data record by ID.

        :param db: The database session.
        :param id: The UUID of the raw sensor data to delete.
        :return: The deleted raw sensor data or None if not found.
        """
        try:
            obj = db.query(self.model).filter(self.model.id == id).first()
            if obj:
                db.delete(obj)
                db.commit()
                db.refresh(obj)
                logger.info(f"Deleted raw sensor data with ID: {id}")
                return obj
            else:
                logger.warning(f"Raw sensor data with ID {id} not found for deletion.")
                return None
        except Exception as e:
            db.rollback()
            logger.exception("Error deleting raw sensor data from database.")
            raise

# Initialize CRUD instance for RawSensorData
raw_sensor_data_crud = CRUDRawSensorData(RawSensorData)