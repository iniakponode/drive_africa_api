from __future__ import annotations

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from safedrive.core.security import ApiClientContext, Role, ensure_driver_access, filter_query_by_driver_ids, require_roles
from safedrive.crud.report_statistics import report_statistics_crud
from safedrive.database.db import get_db
from safedrive.models.report_statistics import ReportStatistics
from safedrive.schemas.report_statistics import (
    ReportStatisticsCreate,
    ReportStatisticsResponse,
    ReportStatisticsUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/report_statistics/", response_model=ReportStatisticsResponse)
def create_report_statistics(
    *,
    db: Session = Depends(get_db),
    report_in: ReportStatisticsCreate,
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> ReportStatisticsResponse:
    ensure_driver_access(current_client, report_in.driverProfileId)
    report = report_statistics_crud.create(db=db, obj_in=report_in)
    return ReportStatisticsResponse.model_validate(report)


@router.get("/report_statistics/{report_id}", response_model=ReportStatisticsResponse)
def get_report_statistics(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> ReportStatisticsResponse:
    report = report_statistics_crud.get(db=db, id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report statistics not found.")
    ensure_driver_access(current_client, report.driverProfileId)
    return ReportStatisticsResponse.model_validate(report)


@router.get("/report_statistics/", response_model=List[ReportStatisticsResponse])
def list_report_statistics(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> List[ReportStatisticsResponse]:
    query = db.query(ReportStatistics)
    query = filter_query_by_driver_ids(query, ReportStatistics.driverProfileId, current_client)
    reports = query.offset(skip).limit(limit).all()
    return [ReportStatisticsResponse.model_validate(report) for report in reports]


@router.put("/report_statistics/{report_id}", response_model=ReportStatisticsResponse)
def update_report_statistics(
    report_id: UUID,
    *,
    db: Session = Depends(get_db),
    report_in: ReportStatisticsUpdate,
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> ReportStatisticsResponse:
    report = report_statistics_crud.get(db=db, id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report statistics not found.")
    ensure_driver_access(current_client, report.driverProfileId)
    updated = report_statistics_crud.update(db=db, db_obj=report, obj_in=report_in)
    return ReportStatisticsResponse.model_validate(updated)


@router.delete("/report_statistics/{report_id}", response_model=ReportStatisticsResponse)
def delete_report_statistics(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
) -> ReportStatisticsResponse:
    report = report_statistics_crud.get(db=db, id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report statistics not found.")
    ensure_driver_access(current_client, report.driverProfileId)
    deleted = report_statistics_crud.delete(db=db, id=report_id)
    return ReportStatisticsResponse.model_validate(deleted)


@router.post("/report_statistics/batch_create", status_code=201)
def batch_create_report_statistics(
    *,
    db: Session = Depends(get_db),
    reports_in: List[ReportStatisticsCreate],
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN, Role.DRIVER)
    ),
):
    if current_client.role == Role.DRIVER:
        for report in reports_in:
            ensure_driver_access(current_client, report.driverProfileId)
    created = report_statistics_crud.batch_create(db=db, objs_in=reports_in)
    return {"created": len(created)}


@router.delete("/report_statistics/batch_delete", status_code=204)
def batch_delete_report_statistics(
    *,
    db: Session = Depends(get_db),
    ids: List[UUID],
    current_client: ApiClientContext = Depends(
        require_roles(Role.ADMIN)
    ),
):
    deleted = report_statistics_crud.batch_delete(db=db, ids=ids)
    logger.info("Batch deleted %s ReportStatistics records.", deleted)
