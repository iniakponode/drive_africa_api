from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from safedrive.database.db import get_db
from safedrive.schemas.nlg_report import NLGReportCreate, NLGReportUpdate, NLGReportResponse
from safedrive.crud.nlg_report import nlg_report_crud
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/nlg_reports/", response_model=NLGReportResponse)
def create_nlg_report(*, db: Session = Depends(get_db), report_in: NLGReportCreate) -> NLGReportResponse:
    try:
        new_report = nlg_report_crud.create(db=db, obj_in=report_in)
        logger.info(f"Created NLGReport with ID: {new_report.id}")
        return NLGReportResponse.model_validate(new_report)
    except Exception as e:
        logger.error(f"Error creating NLGReport: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating NLG report")

@router.get("/nlg_reports/{report_id}", response_model=NLGReportResponse)
def get_nlg_report(report_id: UUID, db: Session = Depends(get_db)) -> NLGReportResponse:
    report = nlg_report_crud.get(db=db, id=report_id)
    if not report:
        logger.warning(f"NLGReport with ID {report_id} not found.")
        raise HTTPException(status_code=404, detail="NLG report not found")
    return NLGReportResponse(id=report.id_uuid, driver_profile_id=report.driver_profile_id, report_text=report.report_text, generated_at=report.generated_at, synced=report.synced)

@router.get("/nlg_reports/", response_model=List[NLGReportResponse])
def get_all_nlg_reports(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)) -> List[NLGReportResponse]:
    reports = nlg_report_crud.get_all(db=db, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(reports)} NLGReports.")
    return [NLGReportResponse(id=report.id_uuid, driver_profile_id=report.driver_profile_id, report_text=report.report_text, generated_at=report.generated_at, synced=report.synced) for report in reports]

@router.put("/nlg_reports/{report_id}", response_model=NLGReportResponse)
def update_nlg_report(report_id: UUID, *, db: Session = Depends(get_db), report_in: NLGReportUpdate) -> NLGReportResponse:
    report = nlg_report_crud.get(db=db, id=report_id)
    if not report:
        logger.warning(f"NLGReport with ID {report_id} not found for update.")
        raise HTTPException(status_code=404, detail="NLG report not found")
    updated_report = nlg_report_crud.update(db=db, db_obj=report, obj_in=report_in)
    logger.info(f"Updated NLGReport with ID: {report_id}")
    return NLGReportResponse(id=updated_report.id_uuid, driver_profile_id=updated_report.driver_profile_id, report_text=updated_report.report_text, generated_at=updated_report.generated_at, synced=updated_report.synced)

@router.delete("/nlg_reports/{report_id}", response_model=NLGReportResponse)
def delete_nlg_report(report_id: UUID, db: Session = Depends(get_db)) -> NLGReportResponse:
    report = nlg_report_crud.get(db=db, id=report_id)
    if not report:
        logger.warning(f"NLGReport with ID {report_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="NLG report not found")
    deleted_report = nlg_report_crud.delete(db=db, id=report_id)
    logger.info(f"Deleted NLGReport with ID: {report_id}")
    return NLGReportResponse(id=deleted_report.id_uuid, driver_profile_id=deleted_report.driver_profile_id, report_text=deleted_report.report_text, generated_at=deleted_report.generated_at, synced=deleted_report.synced)