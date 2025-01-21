from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from safedrive.models.road import Road
from safedrive.schemas.road import RoadCreate, RoadUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDRoad:
    def __init__(self, model):
        self.model = model

    def create(self, db: Session, obj_in: RoadCreate) -> Road:
        try:
            obj_data = obj_in.dict()
            # Convert UUID strings to UUID objects if necessary
            for uuid_field in ['id', 'driverProfileId']:
                if uuid_field in obj_data and isinstance(obj_data[uuid_field], str):
                    obj_data[uuid_field] = UUID(obj_data[uuid_field])
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            logger.info(f"Created Road with ID: {db_obj.id}")
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating Road: {str(e)}")
            raise e

# Assuming `self.model` is set to the Road SQLAlchemy model
    def batch_create(self, db: Session, objs_in: List[RoadCreate]) -> List[Road]:
        try:
            db_objs = []

            for obj_in in objs_in:
                obj_data = obj_in.model_dump()

                # Convert UUID fields if needed
                if 'driverProfileId' in obj_data and isinstance(obj_data['driverProfileId'], str):
                    obj_data['driverProfileId'] = UUID(obj_data['driverProfileId'])

                # Create a new Road instance
                db_obj = self.model(**obj_data)
                db_objs.append(db_obj)

            db.add_all(db_objs)
            db.commit()
            db.flush()

            for db_obj in db_objs:
                db.refresh(db_obj)
                # Optionally log creation: logger.info(f"Created Road with ID: {db_obj.id}")

            return db_objs

        except Exception as e:
            db.rollback()
            # Log error as appropriate
            raise HTTPException(status_code=500, detail="An unexpected error occurred during batch creation.")

    def get(self, db: Session, id: UUID) -> Optional[Road]:
        road = db.query(self.model).filter(self.model.id == id).first()
        if road:
            logger.info(f"Retrieved Road with ID: {id}")
        else:
            logger.warning(f"Road with ID {id} not found.")
        return road

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Road]:
        roads = db.query(self.model).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(roads)} Roads.")
        return roads

    def update(self, db: Session, db_obj: Road, obj_in: RoadUpdate) -> Road:
        obj_data = obj_in.dict(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        try:
            db.commit()
            logger.info(f"Updated Road with ID: {db_obj.id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating Road: {str(e)}")
            raise e
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: UUID) -> Optional[Road]:
        obj = db.query(self.model).filter(self.model.id == id).first()
        if obj:
            db.delete(obj)
            try:
                db.commit()
                logger.info(f"Deleted Road with ID: {id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Error deleting Road: {str(e)}")
                raise e
        else:
            logger.warning(f"Road with ID {id} not found for deletion.")
        return obj

# Initialize CRUD instance for Road
crud_road = CRUDRoad(Road)