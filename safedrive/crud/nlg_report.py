from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from safedrive.models.nlg_report import NLGReport, generate_uuid_binary
from safedrive.schemas.nlg_report import NLGReportCreate, NLGReportUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDNLGReport:
    """
    CRUD operations for NLGReport.
    """
    def __init__(self, model):
        self.model = model

    def create(self, db: Session, obj_in: NLGReportCreate) -> NLGReport:
        db_obj = self.model(**obj_in.model_dump(), id=generate_uuid_binary())
        if hasattr(db_obj,'driver_profile_id') and isinstance(getattr(db_obj,'driver_profile_id'), UUID):
            setattr(db_obj, 'driver_profile_id', getattr(db_obj,'driver_profile_id').bytes)
        db.add(db_obj)
        try:
            db.commit()
            logger.info(f"Created NLGReport with ID: {db_obj.id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating NLGReport: {str(e)}")
            raise e
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: UUID) -> Optional[NLGReport]:
        report = db.query(self.model).filter(self.model.id == id.bytes).first()
        if report:
            logger.info(f"Retrieved NLGReport with ID: {id}")
        else:
            logger.warning(f"NLGReport with ID {id} not found.")
        return report

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[NLGReport]:
        reports = db.query(self.model).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(reports)} NLGReports.")
        return reports

    def update(self, db: Session, db_obj: NLGReport, obj_in: NLGReportUpdate) -> NLGReport:
        obj_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
        db.add(db_obj)
        try:
            db.commit()
            logger.info(f"Updated NLGReport with ID: {db_obj.id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating NLGReport: {str(e)}")
            raise e
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: UUID) -> Optional[NLGReport]:
        obj = db.query(self.model).filter(self.model.id == id.bytes).first()
        if obj:
            db.delete(obj)
            try:
                db.commit()
                logger.info(f"Deleted NLGReport with ID: {id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Error deleting NLGReport: {str(e)}")
                raise e
        else:
            logger.warning(f"NLGReport with ID {id} not found for deletion.")
        return obj

# Initialize CRUD instance for NLGReport
nlg_report_crud = CRUDNLGReport(NLGReport)