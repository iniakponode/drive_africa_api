from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from safedrive.database.db import get_db
from safedrive.models.admin_setting import AdminSetting
from safedrive.schemas.admin import CloudEndpointConfig

router = APIRouter()

CLOUD_ENDPOINTS_SETTING_KEY = "cloud_endpoints"


def _coerce_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


@router.get("/config/cloud-endpoints", response_model=CloudEndpointConfig)
def get_cloud_endpoints(db: Session = Depends(get_db)) -> CloudEndpointConfig:
    setting = (
        db.query(AdminSetting)
        .filter(AdminSetting.key == CLOUD_ENDPOINTS_SETTING_KEY)
        .first()
    )
    payload = _coerce_dict(setting.value) if setting else {}
    return CloudEndpointConfig(**payload)
