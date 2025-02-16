from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError  # <-- Use SQLAlchemy's IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
import logging

from safedrive.models.driver_profile import DriverProfile
from safedrive.schemas.driver_profile import DriverProfileCreate, DriverProfileUpdate

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class CRUDDriverProfile:
    def __init__(self, model):
        self.model = model

    def create(self, db: Session, obj_in: DriverProfileCreate) -> DriverProfile:
        try:
            obj_data = obj_in.model_dump()

            # Ensure driverProfileId is a proper UUID, regardless of input type.
            if 'driverProfileId' in obj_data:
                if isinstance(obj_data['driverProfileId'], str):
                    obj_data['driverProfileId'] = UUID(obj_data['driverProfileId'])
                elif isinstance(obj_data['driverProfileId'], bytes):
                    obj_data['driverProfileId'] = UUID(bytes=obj_data['driverProfileId'])

            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)

            logger.info(f"Created DriverProfile with ID: {db_obj.driverProfileId}")
            return db_obj

        except IntegrityError as e:
            db.rollback()
            # Log the database-level error message
            error_message = str(e.orig) if e.orig else str(e)
            logger.error(f"IntegrityError details: {error_message}")

            # Check if it's a duplicate entry error
            if "Duplicate entry" in error_message:
                email = obj_data.get("email")
                logger.warning(f"Duplicate entry for email '{email}'. Retrieving existing profile...")
                existing_profile = db.query(self.model).filter(self.model.email == email).first()
                if existing_profile:
                    return existing_profile
            
            # If it's not a duplicate or we can’t find the record, raise a 500
            logger.error(f"Unexpected error while creating DriverProfile: {error_message}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred again.")

    def get_by_email(self, db: Session, email: str) -> Optional[DriverProfile]:
        return db.query(self.model).filter(self.model.email == email).one_or_none()

    def batch_create(self, db: Session, objs_in: List[DriverProfileCreate]) -> List[DriverProfile]:
        db_objs = []
        skipped_count = 0

        for obj_in in objs_in:
            obj_data = obj_in.model_dump()
            if 'driverProfileId' in obj_data and isinstance(obj_data['driverProfileId'], str):
                obj_data['driverProfileId'] = UUID(obj_data['driverProfileId'])

            try:
                db_obj = self.model(**obj_data)
                db.add(db_obj)
                db.flush()  # Force insert, so we can catch IntegrityError now
                db_objs.append(db_obj)
            except IntegrityError as e:
                db.rollback()
                skipped_count += 1
                logger.warning(f"Skipping DriverProfile record due to IntegrityError: {str(e)}")
            except Exception as e:
                db.rollback()
                skipped_count += 1
                logger.error(f"Unexpected error inserting DriverProfile record: {str(e)}")

        db.commit()
        for db_obj in db_objs:
            db.refresh(db_obj)
            logger.info(f"Created DriverProfile with ID: {db_obj.driverProfileId}")

        logger.info(f"Batch inserted {len(db_objs)} DriverProfile records. Skipped {skipped_count}.")
        return db_objs

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
        obj_data = obj_in.model_dump(exclude_unset=True)
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
    
    def delete_by_email_cascade(self, db: Session, email: str) -> Optional[DriverProfile]:
        profile = self.get_by_email(db, email)
        if not profile:
            return None

        db.delete(profile)
        db.commit()
        return profile


# Initialize CRUD instance
driver_profile_crud = CRUDDriverProfile(DriverProfile)