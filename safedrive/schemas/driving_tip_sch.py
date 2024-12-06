from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class DrivingTipBase(BaseModel):
    """
    Base schema for DrivingTip containing common attributes.

    Attributes:
    - **tip_id**: Unique identifier for the driving tip.
    - **title**: Title of the driving tip.
    - **meaning**: Explanation of the tip's meaning.
    - **penalty**: Penalty details, if applicable.
    - **fine**: Fine amount associated with the tip.
    - **law**: Related law to the tip.
    - **hostility**: Hostility level, if applicable.
    - **summary_tip**: Summary of the tip.
    - **sync**: Flag indicating if the data has been synced.
    - **date**: Date the tip was recorded.
    - **profile_id**: UUID of the driver profile.
    - **llm**: The language model used for generating the tip.
    """
    tip_id: UUID
    title: str
    meaning: Optional[str] = None
    penalty: Optional[str] = None
    fine: Optional[str] = None
    law: Optional[str] = None
    hostility: Optional[str] = None
    summary_tip: Optional[str] = None
    sync: bool
    date: datetime
    profile_id: UUID
    llm: Optional[str] = None

    class Config:
        from_attributes = True

class DrivingTipCreate(BaseModel):
    """
    Schema for creating a new DrivingTip.
    """
    title: str
    meaning: Optional[str] = None
    penalty: Optional[str] = None
    fine: Optional[str] = None
    law: Optional[str] = None
    hostility: Optional[str] = None
    summary_tip: Optional[str] = None
    sync: bool
    date: datetime
    profile_id: UUID
    llm: Optional[str] = None

    class Config:
        from_attributes = True

class DrivingTipUpdate(BaseModel):
    """
    Schema for updating an existing DrivingTip.
    """
    title: Optional[str] = None
    meaning: Optional[str] = None
    penalty: Optional[str] = None
    fine: Optional[str] = None
    law: Optional[str] = None
    hostility: Optional[str] = None
    summary_tip: Optional[str] = None
    sync: Optional[bool] = None
    date: Optional[datetime] = None
    profile_id: Optional[UUID] = None
    llm: Optional[str] = None

    class Config:
        from_attributes = True

class DrivingTipResponse(DrivingTipBase):
    """
    Response schema for DrivingTip.
    """
    pass