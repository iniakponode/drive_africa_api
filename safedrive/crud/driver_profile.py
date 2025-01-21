from fastapi import HTTPException
from pymysql import DataError, IntegrityError, OperationalError
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from safedrive.models.driver_profile import DriverProfile, generate_uuid_binary
from safedrive.schemas.driver_profile import DriverProfileCreate, DriverProfileUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDDriverProfile:
    """
    CRUD operations for DriverProfile.

    Methods:
    - **create**: Adds a new DriverProfile record.
    - **get**: Retrieves a DriverProfile by UUID.
    - **get_all**: Retrieves all DriverProfiles.
    - **update**: Updates a DriverProfile record.
    - **delete**: Deletes a DriverProfile record.
    """
    def __init__(self, model):
        self.model = model

    def create(self, db: Session, obj_in: DriverProfileCreate) -> DriverProfile:
        try:
            obj_data = obj_in.model_dump()

            # Convert to a UUID only if it's a string
            if 'driverProfileId' in obj_data and isinstance(obj_data['driverProfileId'], str):
                obj_data['driverProfileId'] = UUID(obj_data['driverProfileId'])

            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.flush()
            db.refresh(db_obj)
            logger.info(f"Created DriverProfile with ID: {db_obj.driverProfileId}")
            print(str(db_obj.driverProfileId))
            return db_obj

        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error while creating DriverProfile: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    def batch_create(self, db: Session, objs_in: List[DriverProfileCreate]) -> List[DriverProfile]:
        try:
            db_objs = []

            # Iterate over each input object to process and instantiate the model
            for obj_in in objs_in:
                obj_data = obj_in.model_dump()

                # Convert to a UUID only if it's a string
                if 'driverProfileId' in obj_data and isinstance(obj_data['driverProfileId'], str):
                    obj_data['driverProfileId'] = UUID(obj_data['driverProfileId'])

                db_obj = self.model(**obj_data)
                db_objs.append(db_obj)

            # Bulk add all new objects to the session
            db.add_all(db_objs)
            db.commit()
            db.flush()  # Flush pending changes to the database

            # Refresh each object to load any DB-generated fields and log creation
            for db_obj in db_objs:
                db.refresh(db_obj)
                logger.info(f"Created DriverProfile with ID: {db_obj.driverProfileId}")
                print(str(db_obj.driverProfileId))

            return db_objs

        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error while creating DriverProfile batch: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")


    def get(self, db: Session, id: UUID) -> Optional[DriverProfile]:
        profile = db.query(self.model).filter(self.model.driverProfileId == id).first()
        if profile:
            logger.info(f"Retrieved DriverProfile with ID: {id}")
        else:
            logger.warning(f"DriverProfile with ID {id} not found.")
        return profile

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[DriverProfile]:
        profiles = db.query(self.model).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(profiles)} DriverProfiles.")
        return profiles

    def update(self, db: Session, db_obj: DriverProfile, obj_in: DriverProfileUpdate) -> DriverProfile:
        obj_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
        db.add(db_obj)
        try:
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated DriverProfile with ID: {db_obj.driverProfileId}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating DriverProfile: {str(e)}")
            raise e
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: UUID) -> Optional[DriverProfile]:
        obj = db.query(self.model).filter(self.model.driverProfileId == id).first()
        if obj:
            db.delete(obj)
            try:
                db.commit()
                db.refresh(obj)
                logger.info(f"Deleted DriverProfile with ID: {id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Error deleting DriverProfile: {str(e)}")
                raise e
        else:
            logger.warning(f"DriverProfile with ID {id} not found for deletion.")
        return obj

# Initialize CRUD instance for DriverProfile
driver_profile_crud = CRUDDriverProfile(DriverProfile)