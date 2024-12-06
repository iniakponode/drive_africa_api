from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from safedrive.database.db import get_db
from safedrive.schemas.cause import CauseCreate, CauseUpdate, CauseResponse
from safedrive.crud.cause import cause_crud
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/causes/", response_model=CauseResponse)
def create_cause(*, db: Session = Depends(get_db), cause_in: CauseCreate) -> CauseResponse:
    try:
        new_cause = cause_crud.create(db=db, obj_in=cause_in)
        logger.info(f"Created Cause with ID: {new_cause.id}")
        return CauseResponse(id=new_cause.id_uuid, **cause_in.dict())
    except Exception as e:
        logger.error(f"Error creating Cause: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating cause")

@router.get("/causes/{cause_id}", response_model=CauseResponse)
def get_cause(cause_id: UUID, db: Session = Depends(get_db)) -> CauseResponse:
    cause = cause_crud.get(db=db, id=cause_id)
    if not cause:
        logger.warning(f"Cause with ID {cause_id} not found.")
        raise HTTPException(status_code=404, detail="Cause not found")
    return CauseResponse.model_validate(cause)

@router.get("/causes/", response_model=List[CauseResponse])
def get_all_causes(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)) -> List[CauseResponse]:
    causes = cause_crud.get_all(db=db, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(causes)} Causes.")
    return [CauseResponse.model_validate(cause) for cause in causes]

@router.put("/causes/{cause_id}", response_model=CauseResponse)
def update_cause(cause_id: UUID, *, db: Session = Depends(get_db), cause_in: CauseUpdate) -> CauseResponse:
    cause = cause_crud.get(db=db, id=cause_id)
    if not cause:
        logger.warning(f"Cause with ID {cause_id} not found for update.")
        raise HTTPException(status_code=404, detail="Cause not found")
    updated_cause = cause_crud.update(db=db, db_obj=cause, obj_in=cause_in)
    logger.info(f"Updated Cause with ID: {cause_id}")
    return CauseResponse.model_validate(updated_cause)

@router.delete("/causes/{cause_id}", response_model=CauseResponse)
def delete_cause(cause_id: UUID, db: Session = Depends(get_db)) -> CauseResponse:
    cause = cause_crud.get(db=db, id=cause_id)
    if not cause:
        logger.warning(f"Cause with ID {cause_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="Cause not found")
    deleted_cause = cause_crud.delete(db=db, id=cause_id)
    logger.info(f"Deleted Cause with ID: {cause_id}")
    return CauseResponse.model_validate(deleted_cause)