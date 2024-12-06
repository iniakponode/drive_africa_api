from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class CauseBase(BaseModel):
    """
    Base schema for Cause containing common attributes.

    Attributes:
    - **id**: Unique identifier for the cause.
    - **unsafe_behaviour_id**: Identifier of the associated unsafe behavior.
    - **name**: Description of the cause.
    - **influence**: Indicates if the cause is influential.
    - **created_at**: Creation timestamp.
    - **updated_at**: Last update timestamp.
    """
    id: UUID
    unsafe_behaviour_id: UUID
    name: str
    influence: Optional[bool] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    synced: Optional[bool] = False

    class Config:
        from_attributes = True

class CauseCreate(BaseModel):
    """
    Schema for creating a new Cause.

    Attributes:
    - **unsafe_behaviour_id**: Identifier of the associated unsafe behavior.
    - **name**: Description of the cause.
    - **influence**: Indicates if the cause is influential.
    - **created_at**: Creation timestamp.
    """
    unsafe_behaviour_id: UUID
    name: str
    influence: Optional[bool] = None
    created_at: datetime
    synced: Optional[bool] = False

    class Config:
        from_attributes = True

class CauseUpdate(BaseModel):
    """
    Schema for updating an existing Cause.

    Attributes:
    - **name**: Optionally update the cause description.
    - **influence**: Optionally update the influence status.
    - **updated_at**: Optionally update the timestamp for last update.
    """
    name: Optional[str] = None
    influence: Optional[bool] = None
    updated_at: Optional[datetime] = None
    synced: Optional[bool] = None

    class Config:
        from_attributes = True

class CauseResponse(CauseBase):
    """
    Response schema for Cause, inheriting from CauseBase.
    """
    pass