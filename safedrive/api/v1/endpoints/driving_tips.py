from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from safedrive.database.db import get_db
from safedrive.schemas.driving_tip_sch import DrivingTipCreate, DrivingTipUpdate, DrivingTipResponse
from safedrive.crud.driving_tip import driving_tip_crud
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/driving_tips/", response_model=DrivingTipResponse)
def create_driving_tip(*, db: Session = Depends(get_db), tip_in: DrivingTipCreate) -> DrivingTipResponse:
    try:
        new_tip = driving_tip_crud.create(db=db, obj_in=tip_in)
        logger.info(f"Created DrivingTip with ID: {new_tip.tip_id}")
        return DrivingTipResponse(tip_id=new_tip.tip_id, **tip_in.model_dump())
    except ValueError as e:
        logger.error(f"Validation error while creating DrivingTip: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error while creating DrivingTip: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating driving tip")

@router.get("/driving_tips/{tip_id}", response_model=DrivingTipResponse)
def get_driving_tip(tip_id: UUID, db: Session = Depends(get_db)) -> DrivingTipResponse:
    try:
        tip = driving_tip_crud.get(db=db, id=tip_id)
        if not tip:
            logger.warning(f"DrivingTip with ID {tip_id} not found.")
            raise HTTPException(status_code=404, detail="Driving tip not found")
         # Convert SQLAlchemy objects to Pydantic response models
        return  DrivingTipResponse(
                tip_id=tip.tip_id,
                title=tip.title,
                meaning=tip.meaning,
                penalty=tip.penalty,
                fine=tip.fine,
                law=tip.law,
                hostility=tip.hostility,
                summary_tip=tip.summary_tip,
                sync=tip.sync,
                date=tip.date,
                profile_id=tip.profile_id,
                llm=tip.llm
            )
         
        
    except ValueError as e:
        logger.error(f"Error retrieving DrivingTip: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/driving_tips/", response_model=List[DrivingTipResponse])
def get_all_driving_tips(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)) -> List[DrivingTipResponse]:
    try:
        tips = driving_tip_crud.get_all(db=db, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(tips)} DrivingTips.")
        
        # Convert SQLAlchemy objects to Pydantic response models
        return [
            DrivingTipResponse(
                tip_id=tip.tip_id,
                title=tip.title,
                meaning=tip.meaning,
                penalty=tip.penalty,
                fine=tip.fine,
                law=tip.law,
                hostility=tip.hostility,
                summary_tip=tip.summary_tip,
                sync=tip.sync,
                date=tip.date,
                profile_id=tip.profile_id,
                llm=tip.llm
            )
            for tip in tips
        ]
    except Exception as e:
        logger.error(f"Error retrieving DrivingTips: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving driving tips")

@router.put("/driving_tips/{tip_id}", response_model=DrivingTipResponse)
def update_driving_tip(tip_id: UUID, *, db: Session = Depends(get_db), tip_in: DrivingTipUpdate) -> DrivingTipResponse:
    tip = driving_tip_crud.get(db=db, id=tip_id)
    if not tip:
        logger.warning(f"DrivingTip with ID {tip_id} not found for update.")
        raise HTTPException(status_code=404, detail="Driving tip not found")
    try:
        updated_tip = driving_tip_crud.update(db=db, db_obj=tip, obj_in=tip_in)
        logger.info(f"Updated DrivingTip with ID: {tip_id}")
        return DrivingTipResponse(tip_id=updated_tip.tip_id, **tip_in.dict())
    except ValueError as e:
        logger.error(f"Validation error while updating DrivingTip: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/driving_tips/{tip_id}", response_model=DrivingTipResponse)
def delete_driving_tip(tip_id: UUID, db: Session = Depends(get_db)) -> DrivingTipResponse:
    tip = driving_tip_crud.get(db=db, id=tip_id)
    if not tip:
        logger.warning(f"DrivingTip with ID {tip_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="Driving tip not found")
    try:
        deleted_tip = driving_tip_crud.delete(db=db, id=tip_id)
        logger.info(f"Deleted DrivingTip with ID: {tip_id}")
        return DrivingTipResponse(tip_id=deleted_tip.tip_id, 
                                  title=deleted_tip.title, 
                                  meaning=deleted_tip.meaning, 
                                  penalty=deleted_tip.penalty, 
                                  fine=deleted_tip.fine, 
                                  law=deleted_tip.law,
                                  hostility=deleted_tip.hostility, 
                                  summary_tip=deleted_tip.summary_tip, 
                                  sync=deleted_tip.sync, 
                                  date=deleted_tip.date, 
                                  profile_id=deleted_tip.profile_id, 
                                  llm=deleted_tip.llm)
    except ValueError as e:
        logger.error(f"Error deleting DrivingTip: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))