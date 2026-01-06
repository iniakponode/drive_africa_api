from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
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
    """Create a new NLG report."""
    try:
        new_report = nlg_report_crud.create(db=db, obj_in=report_in)
        logger.info(f"Created NLGReport with ID: {new_report.id}")
        return NLGReportResponse.model_validate(new_report)
    except Exception as e:
        logger.error(f"Error creating NLGReport: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating NLG report")

@router.get("/nlg_reports/{report_id}", response_model=NLGReportResponse)
def get_nlg_report(report_id: UUID, db: Session = Depends(get_db)) -> NLGReportResponse:
    """Retrieve a specific NLG report."""
    report = nlg_report_crud.get(db=db, id=report_id)
    if not report:
        logger.warning(f"NLGReport with ID {report_id} not found.")
        raise HTTPException(status_code=404, detail="NLG report not found")
    return NLGReportResponse.model_validate(report)

@router.get("/nlg_reports/", response_model=List[NLGReportResponse])
def get_all_nlg_reports(
    skip: int = 0,
    limit: int = 20,
    driver_profile_id: UUID | None = Query(None, alias="driverProfileId"),
    start_date: datetime | None = Query(None, alias="startDate"),
    end_date: datetime | None = Query(None, alias="endDate"),
    sync: bool | None = Query(None),
    db: Session = Depends(get_db),
) -> List[NLGReportResponse]:
    """List NLG reports with optional pagination."""
    reports = nlg_report_crud.get_all(
        db=db,
        skip=skip,
        limit=limit,
        driver_profile_id=driver_profile_id,
        start_date=start_date,
        end_date=end_date,
        sync=sync,
    )
    logger.info(f"Retrieved {len(reports)} NLGReports.")
    return [NLGReportResponse.model_validate(report) for report in reports]

@router.put("/nlg_reports/{report_id}", response_model=NLGReportResponse)
def update_nlg_report(report_id: UUID, *, db: Session = Depends(get_db), report_in: NLGReportUpdate) -> NLGReportResponse:
    """Update an existing NLG report."""
    report = nlg_report_crud.get(db=db, id=report_id)
    if not report:
        logger.warning(f"NLGReport with ID {report_id} not found for update.")
        raise HTTPException(status_code=404, detail="NLG report not found")
    updated_report = nlg_report_crud.update(db=db, db_obj=report, obj_in=report_in)
    logger.info(f"Updated NLGReport with ID: {report_id}")
    return NLGReportResponse.model_validate(updated_report)

@router.delete("/nlg_reports/{report_id}", response_model=NLGReportResponse)
def delete_nlg_report(report_id: UUID, db: Session = Depends(get_db)) -> NLGReportResponse:
    """Delete an NLG report."""
    report = nlg_report_crud.get(db=db, id=report_id)
    if not report:
        logger.warning(f"NLGReport with ID {report_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="NLG report not found")
    deleted_report = nlg_report_crud.delete(db=db, id=report_id)
    logger.info(f"Deleted NLGReport with ID: {report_id}")
    return NLGReportResponse.model_validate(deleted_report)

@router.post("/nlg_reports/batch_create", status_code=201)
def batch_create_nlg_reports(reports_in: List[NLGReportCreate], db: Session = Depends(get_db)):
    try:
        created = nlg_report_crud.batch_create(db=db, data_in=reports_in)
        return {"message": f"{len(created)} NLGReport records created."}
    except Exception as e:
        logger.error(f"Error in batch create NLGReport: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch creation failed.")

@router.delete("/nlg_reports/batch_delete", status_code=204)
def batch_delete_nlg_reports(ids: List[UUID], db: Session = Depends(get_db)):
    try:
        nlg_report_crud.batch_delete(db=db, ids=ids)
        return {"message": f"{len(ids)} NLGReport records deleted."}
    except Exception as e:
        logger.error(f"Error in batch delete NLGReport: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch deletion failed.")
