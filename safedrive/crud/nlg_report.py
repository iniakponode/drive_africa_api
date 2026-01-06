from sqlalchemy.orm import Session
from datetime import datetime
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
        """
        Create a new NLGReport record in the database.

        :param db: The database session.
        :param obj_in: The schema with input data for creation.
        :return: The created NLGReport.
        """
        try:
            obj_data = obj_in.model_dump()

            # Convert UUID fields to strings
            for uuid_field in ['id', 'driverProfileId']:  # Add more fields as needed
                if uuid_field in obj_data and isinstance(obj_data[uuid_field], str):
                    obj_data[uuid_field] = UUID(obj_data[uuid_field])  # Convert to 36-character string format

            # Create the database object
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()

            logger.info(f"Created NLGReport with ID: {db_obj.id}")

            # Refresh the object to reflect database-assigned values (e.g., timestamps)
            db.refresh(db_obj)

            return db_obj

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating NLGReport: {str(e)}")
            raise e



    def get(self, db: Session, id: UUID) -> Optional[NLGReport]:
        report = db.query(self.model).filter(self.model.id == id).first()
        if report:
            logger.info(f"Retrieved NLGReport with ID: {id}")
        else:
            logger.warning(f"NLGReport with ID {id} not found.")
        return report

    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        driver_profile_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sync: Optional[bool] = None,
    ) -> List[NLGReport]:
        query = db.query(self.model)
        if driver_profile_id is not None:
            query = query.filter(self.model.driverProfileId == driver_profile_id)
        if start_date is not None:
            query = query.filter(self.model.start_date >= start_date)
        if end_date is not None:
            query = query.filter(self.model.end_date <= end_date)
        if sync is not None:
            query = query.filter(self.model.sync == sync)
        reports = query.offset(skip).limit(limit).all()
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
        obj = db.query(self.model).filter(self.model.id == id).first()
        if obj:
            db.delete(obj)
            try:
                db.commit()
                db.refresh(obj)
                logger.info(f"Deleted NLGReport with ID: {id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Error deleting NLGReport: {str(e)}")
                raise e
        else:
            logger.warning(f"NLGReport with ID {id} not found for deletion.")
        return obj

    def batch_create(self, db: Session, data_in: List[NLGReportCreate]) -> List[NLGReport]:
        db_objs = []
        skipped_count = 0

        for report in data_in:
            obj_data = report.model_dump()
            for uuid_field in ["id", "driverProfileId"]:
                if uuid_field in obj_data and isinstance(obj_data[uuid_field], str):
                    obj_data[uuid_field] = UUID(obj_data[uuid_field])

            report_id = obj_data.get("id")
            if report_id:
                existing = db.query(self.model).filter_by(id=report_id).first()
                if existing:
                    logger.info(f"Skipping duplicate NLGReport with ID {report_id}")
                    skipped_count += 1
                    continue

            try:
                db_obj = self.model(**obj_data)
                db.add(db_obj)
                db.flush()
                db_objs.append(db_obj)
            except Exception as e:
                db.rollback()
                skipped_count += 1
                logger.warning(f"Skipping NLGReport due to error: {str(e)}")

        db.commit()
        for obj in db_objs:
            db.refresh(obj)

        logger.info(f"Batch inserted {len(db_objs)} NLGReports. Skipped {skipped_count}.")
        return db_objs

    def batch_delete(self, db: Session, ids: List[UUID]) -> None:
        try:
            db.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session=False)
            db.commit()
            logger.info(f"Batch deleted {len(ids)} NLGReports.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error during batch deletion of NLGReports: {str(e)}")
            raise e

# Initialize CRUD instance for NLGReport
nlg_report_crud = CRUDNLGReport(NLGReport)
