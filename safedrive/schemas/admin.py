from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class AdminSettingResponse(BaseModel):
    key: str
    value: dict
    updated_at: datetime


class CloudEndpointConfig(BaseModel):
    road_limits_url: Optional[str] = None
    driving_tips_url: Optional[str] = None
    model_response_url: Optional[str] = None

    model_config = {"protected_namespaces": ()}


class DatasetAccessConfig(BaseModel):
    datasets: Dict[str, List[str]]
