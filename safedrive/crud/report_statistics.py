from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from safedrive.models.report_statistics import ReportStatistics
from safedrive.schemas.report_statistics import ReportStatisticsCreate, ReportStatisticsUpdate

logger = logging.getLogger(__name__)


class CRUDReportStatistics:
    def __init__(self, model):
        self.model = model

    def _normalize(self, data: dict) -> dict:
        for field in ("id", "driverProfileId", "tripId"):
            value = data.get(field)
            if isinstance(value, str):
                data[field] = UUID(value)
        return data

    def create(self, db: Session, obj_in: ReportStatisticsCreate) -> ReportStatistics:
        try:
            data = jsonable_encoder(obj_in)
            data = self._normalize(data)
            db_obj = self.model(**data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as exc:
            db.rollback()
            logger.error("Error creating ReportStatistics: %s", exc)
            raise HTTPException(status_code=500, detail="Error creating report statistics.")

    def batch_create(self, db: Session, objs_in: List[ReportStatisticsCreate]) -> List[ReportStatistics]:
        db_objs: List[ReportStatistics] = []
        skipped = 0

        for obj_in in objs_in:
            data = jsonable_encoder(obj_in)
            data = self._normalize(data)
            existing = db.query(self.model).filter(self.model.id == data.get("id")).first()
            if existing:
                skipped += 1
                continue
            try:
                db_obj = self.model(**data)
                db.add(db_obj)
                db.flush()
                db_objs.append(db_obj)
            except Exception as exc:
                db.rollback()
                skipped += 1
                logger.warning("Skipping ReportStatistics due to error: %s", exc)

        db.commit()
        for obj in db_objs:
            db.refresh(obj)

        logger.info("Batch created %s ReportStatistics records. Skipped %s.", len(db_objs), skipped)
        return db_objs

    def get(self, db: Session, id: UUID) -> Optional[ReportStatistics]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[ReportStatistics]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def update(self, db: Session, db_obj: ReportStatistics, obj_in: ReportStatisticsUpdate) -> ReportStatistics:
        data = jsonable_encoder(obj_in, exclude_none=True)
        data = self._normalize(data)
        for field, value in data.items():
            setattr(db_obj, field, value)
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as exc:
            db.rollback()
            logger.error("Error updating ReportStatistics: %s", exc)
            raise HTTPException(status_code=500, detail="Error updating report statistics.")

    def delete(self, db: Session, id: UUID) -> Optional[ReportStatistics]:
        obj = db.query(self.model).filter(self.model.id == id).first()
        if not obj:
            return None
        db.delete(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def batch_delete(self, db: Session, ids: List[UUID]) -> int:
        try:
            deleted = (
                db.query(self.model)
                .filter(self.model.id.in_(ids))
                .delete(synchronize_session=False)
            )
            db.commit()
            logger.info("Batch deleted %s ReportStatistics records.", deleted)
            return deleted
        except Exception as exc:
            db.rollback()
            logger.error("Error deleting ReportStatistics in batch: %s", exc)
            raise HTTPException(status_code=500, detail="Error deleting report statistics.")


report_statistics_crud = CRUDReportStatistics(ReportStatistics)
