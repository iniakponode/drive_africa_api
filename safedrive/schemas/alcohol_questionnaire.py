from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class AlcoholQuestionnaireBaseSchema(BaseModel):
    id: UUID
    driverProfileId: UUID
    drankAlcohol: bool
    selectedAlcoholTypes: Optional[str] = None
    beerQuantity: Optional[str] = None
    wineQuantity: Optional[str] = None
    spiritsQuantity: Optional[str] = None
    firstDrinkTime: Optional[str] = None
    lastDrinkTime: Optional[str] = None
    emptyStomach: bool
    caffeinatedDrink: bool
    impairmentLevel: int
    plansToDrive: bool

    class Config:
        from_attributes = True

class AlcoholQuestionnaireCreateSchema(BaseModel):
    id: UUID
    driverProfileId: UUID = Field(..., description="userId")
    drankAlcohol: bool = Field(..., description="drankAlcohol")
    selectedAlcoholTypes: Optional[str] = Field(..., description="selectedAlcoholTypes")
    beerQuantity: Optional[str] = Field(..., description="beerQuantity")
    wineQuantity: Optional[str] = Field(..., description="wineQuantity")
    spiritsQuantity: Optional[str] = Field(..., description="spiritsQuantity")
    firstDrinkTime: str = Field(..., description="firstDrinkTime")
    lastDrinkTime: str = Field(..., description="lastDrinkTime")
    emptyStomach: bool = Field(..., description="emptyStomach")
    caffeinatedDrink: bool = Field(..., description="caffeinatedDrink")
    impairmentLevel: int = Field(..., description="impairmentLevel")
    plansToDrive: bool = Field(..., description="plansToDrive")

    class Config:
       from_attributes = True

class AlcoholQuestionnaireResponseSchema(AlcoholQuestionnaireBaseSchema):
    pass
