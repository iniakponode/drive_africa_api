from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from safedrive.database.db import get_db
from safedrive.schemas.road import RoadCreate, RoadUpdate, RoadResponse
from safedrive.crud.road import crud_road
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/roads/", response_model=RoadResponse)
def create_road(*, db: Session = Depends(get_db), road_in: RoadCreate) -> RoadResponse:
    try:
        new_road = crud_road.create(db=db, obj_in=road_in)
        logger.info(f"Created Road with ID: {new_road.id}")
        return RoadResponse.model_validate(new_road)
    except Exception as e:
        logger.error(f"Error creating Road: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating road")

@router.get("/roads/{road_id}", response_model=RoadResponse)
def get_road(road_id: UUID, db: Session = Depends(get_db)) -> RoadResponse:
    road = crud_road.get(db=db, id=road_id)
    if not road:
        logger.warning(f"Road with ID {road_id} not found.")
        raise HTTPException(status_code=404, detail="Road not found")
    return RoadResponse.model_validate(road)

@router.get("/roads/", response_model=List[RoadResponse])
def get_all_roads(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)) -> List[RoadResponse]:
    roads = crud_road.get_all(db=db, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(roads)} Roads.")
    return [RoadResponse.model_validate(road) for road in roads]

@router.put("/roads/{road_id}", response_model=RoadResponse)
def update_road(road_id: UUID, *, db: Session = Depends(get_db), road_in: RoadUpdate) -> RoadResponse:
    road = crud_road.get(db=db, id=road_id)
    if not road:
        logger.warning(f"Road with ID {road_id} not found for update.")
        raise HTTPException(status_code=404, detail="Road not found")
    updated_road = crud_road.update(db=db, db_obj=road, obj_in=road_in)
    logger.info(f"Updated Road with ID: {road_id}")
    return RoadResponse.model_validate(updated_road)

@router.delete("/roads/{road_id}", response_model=RoadResponse)
def delete_road(road_id: UUID, db: Session = Depends(get_db)) -> RoadResponse:
    road = crud_road.get(db=db, id=road_id)
    if not road:
        logger.warning(f"Road with ID {road_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="Road not found")
    deleted_road = crud_road.delete(db=db, id=road_id)
    logger.info(f"Deleted Road with ID: {road_id}")
    return RoadResponse.model_validate(deleted_road)

@router.post("/roads/batch_create", response_model=List[RoadResponse])
def batch_create_roads(
        *,
        db: Session = Depends(get_db),
        roads_in: List[RoadCreate]
    ) -> List[RoadResponse]:
    try:
        new_roads = crud_road.batch_create(db=db, objs_in=roads_in)

        if not new_roads:
            raise HTTPException(
                status_code=400,
                detail="No roads were created due to errors or duplicates."
            )

        created_roads = [RoadResponse.model_validate(new_road) for new_road in new_roads]

        return created_roads

    except Exception as e:
        # Log error appropriately
        logger.exception("Batch‐create roads failed")
        raise 
    # HTTPException(status_code=500, detail="An unexpected error occurred while creating roads.")
