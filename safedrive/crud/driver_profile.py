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
        """
        Creates a new driver profile in the database.
        - **db**: Database session.
        - **obj_in**: Data for creating the driver profile.

        Returns the created DriverProfile instance.
        """
        db_obj = self.model(**obj_in.model_dump(), driver_profile_id=generate_uuid_binary())
        db.add(db_obj)
        
        try:
            db.commit()
            logger.info(f"Created DriverProfile with ID: {db_obj.driver_profile_id}")
        
        except IntegrityError as e:
            db.rollback()
            logger.error(f"IntegrityError while creating DriverProfile: {str(e)}")
            # Check for specific error messages or codes, such as unique constraint violations
            if "Duplicate entry" in str(e.orig):
                raise HTTPException(status_code=400, detail="Duplicate entry: this email already exists.")
            else:
                raise HTTPException(status_code=400, detail="Database integrity error occurred.")
        
        except DataError as e:
            db.rollback()
            logger.error(f"DataError while creating DriverProfile: {str(e)}")
            # This error may occur due to type mismatch or data length issues
            raise HTTPException(status_code=400, detail="Invalid data provided.")
        
        except OperationalError as e:
            db.rollback()
            logger.error(f"OperationalError while creating DriverProfile: {str(e)}")
            # This error could indicate issues with the database connection or transaction
            raise HTTPException(status_code=503, detail="Database operation failed. Please try again later.")
        
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error while creating DriverProfile: {str(e)}")
            # Handle any other unexpected exceptions
            raise HTTPException(status_code=500, detail="An unexpected error occurred while creating the driver profile.")
        
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: UUID) -> Optional[DriverProfile]:
        profile = db.query(self.model).filter(self.model.driver_profile_id == id.bytes).first()
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
            logger.info(f"Updated DriverProfile with ID: {db_obj.driver_profile_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating DriverProfile: {str(e)}")
            raise e
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: UUID) -> Optional[DriverProfile]:
        obj = db.query(self.model).filter(self.model.driver_profile_id == id.bytes).first()
        if obj:
            db.delete(obj)
            try:
                db.commit()
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