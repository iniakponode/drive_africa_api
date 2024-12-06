from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class NLGReportBase(BaseModel):
    """
    Base schema for NLG Report.

    Attributes:
    - **id**: Unique identifier for the report.
    - **user_id**: Identifier for the user who generated the report.
    - **report_text**: Full text content of the report.
    - **generated_at**: Generation date and time of the report.
    - **synced**: Indicates if the report has been synced.
    """
    id: UUID
    driver_profile_id: UUID
    report_text: str
    generated_at: datetime
    synced: bool

    class Config:
        from_attributes = True

class NLGReportCreate(BaseModel):
    """
    Schema for creating a new NLG Report.

    Attributes:
    - **user_id**: Identifier for the user who generated the report.
    - **report_text**: Text content of the report.
    - **generated_at**: Generation date and time of the report.
    - **synced**: Boolean indicating if the report has been synced.
    """
    driver_profile_id: UUID
    report_text: str
    generated_at: datetime
    synced: Optional[bool] = False

    class Config:
        from_attributes = True

class NLGReportUpdate(BaseModel):
    """
    Schema for updating an existing NLG Report.

    Attributes:
    - **report_text**: Optional update to the report content.
    - **synced**: Optional update to sync status.
    """
    report_text: Optional[str] = None
    synced: Optional[bool] = None

    class Config:
        from_attributes = True

class NLGReportResponse(NLGReportBase):
    """
    Schema for NLG Report response format, inherits from NLGReportBase.
    """
    pass