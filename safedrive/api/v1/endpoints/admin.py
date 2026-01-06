import secrets
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from safedrive.core.security import (
    DATASET_ACCESS_SETTING_KEY,
    DEFAULT_DATASET_ACCESS,
    hash_api_key,
)
from safedrive.database.db import get_db
from safedrive.models.admin_setting import AdminSetting
from safedrive.models.auth import ApiClient
from safedrive.models.driver_profile import DriverProfile
from safedrive.models.insurance_partner import InsurancePartner, InsurancePartnerDriver
from safedrive.schemas.admin import CloudEndpointConfig, DatasetAccessConfig
from safedrive.schemas.auth import (
    ApiClientCreate,
    ApiClientCreated,
    ApiClientResponse,
    ApiClientUpdate,
)
from safedrive.schemas.insurance_partner import (
    InsurancePartnerCreate,
    InsurancePartnerDriverCreate,
    InsurancePartnerDriverResponse,
    InsurancePartnerResponse,
)

router = APIRouter()

CLOUD_ENDPOINTS_SETTING_KEY = "cloud_endpoints"


def _get_setting(db: Session, key: str) -> Optional[AdminSetting]:
    return db.query(AdminSetting).filter(AdminSetting.key == key).first()


def _upsert_setting(db: Session, key: str, value: dict) -> AdminSetting:
    setting = _get_setting(db, key)
    if not setting:
        setting = AdminSetting(key=key, value=value)
        db.add(setting)
    else:
        setting.value = value
    db.commit()
    db.refresh(setting)
    return setting


def _coerce_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


@router.post(
    "/admin/api-clients/",
    response_model=ApiClientCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_api_client(
    payload: ApiClientCreate,
    db: Session = Depends(get_db),
) -> ApiClientCreated:
    raw_key = payload.api_key or secrets.token_urlsafe(32)
    client = ApiClient(
        name=payload.name,
        role=payload.role,
        active=payload.active,
        driverProfileId=payload.driverProfileId,
        fleet_id=payload.fleet_id,
        insurance_partner_id=payload.insurance_partner_id,
        api_key_hash=hash_api_key(raw_key),
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return ApiClientCreated(
        id=client.id,
        name=client.name,
        role=client.role,
        active=client.active,
        driverProfileId=client.driverProfileId,
        fleet_id=client.fleet_id,
        insurance_partner_id=client.insurance_partner_id,
        created_at=client.created_at,
        api_key=raw_key,
    )


@router.get("/admin/api-clients/", response_model=List[ApiClientResponse])
def list_api_clients(db: Session = Depends(get_db)) -> List[ApiClientResponse]:
    clients = db.query(ApiClient).order_by(ApiClient.created_at.desc()).all()
    return [ApiClientResponse.model_validate(client) for client in clients]


@router.patch("/admin/api-clients/{client_id}", response_model=ApiClientResponse)
def update_api_client(
    client_id: UUID,
    payload: ApiClientUpdate,
    db: Session = Depends(get_db),
) -> ApiClientResponse:
    client = db.query(ApiClient).filter(ApiClient.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="API client not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return ApiClientResponse.model_validate(client)


@router.post(
    "/admin/insurance-partners/",
    response_model=InsurancePartnerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_insurance_partner(
    payload: InsurancePartnerCreate,
    db: Session = Depends(get_db),
) -> InsurancePartnerResponse:
    partner = InsurancePartner(
        name=payload.name,
        label=payload.label,
        active=payload.active,
    )
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return InsurancePartnerResponse.model_validate(partner)


@router.get(
    "/admin/insurance-partners/",
    response_model=List[InsurancePartnerResponse],
)
def list_insurance_partners(
    db: Session = Depends(get_db),
) -> List[InsurancePartnerResponse]:
    partners = db.query(InsurancePartner).order_by(InsurancePartner.created_at.desc()).all()
    return [InsurancePartnerResponse.model_validate(partner) for partner in partners]


@router.post(
    "/admin/insurance-partners/{partner_id}/drivers",
    response_model=InsurancePartnerDriverResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_driver_to_partner(
    partner_id: UUID,
    payload: InsurancePartnerDriverCreate,
    db: Session = Depends(get_db),
) -> InsurancePartnerDriverResponse:
    partner = db.query(InsurancePartner).filter(InsurancePartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Insurance partner not found")
    driver = (
        db.query(DriverProfile)
        .filter(DriverProfile.driverProfileId == payload.driverProfileId)
        .first()
    )
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    link = InsurancePartnerDriver(
        partner_id=partner_id,
        driverProfileId=payload.driverProfileId,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return InsurancePartnerDriverResponse.model_validate(link)


@router.delete(
    "/admin/insurance-partners/{partner_id}/drivers/{driver_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_driver_from_partner(
    partner_id: UUID,
    driver_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    link = (
        db.query(InsurancePartnerDriver)
        .filter(
            InsurancePartnerDriver.partner_id == partner_id,
            InsurancePartnerDriver.driverProfileId == driver_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="Partner driver mapping not found")
    db.delete(link)
    db.commit()


@router.get("/admin/cloud-endpoints", response_model=CloudEndpointConfig)
def get_cloud_endpoints(db: Session = Depends(get_db)) -> CloudEndpointConfig:
    setting = _get_setting(db, CLOUD_ENDPOINTS_SETTING_KEY)
    payload = _coerce_dict(setting.value) if setting else {}
    return CloudEndpointConfig(**payload)


@router.put("/admin/cloud-endpoints", response_model=CloudEndpointConfig)
def update_cloud_endpoints(
    payload: CloudEndpointConfig,
    db: Session = Depends(get_db),
) -> CloudEndpointConfig:
    setting = _get_setting(db, CLOUD_ENDPOINTS_SETTING_KEY)
    current = _coerce_dict(setting.value) if setting else {}
    updates = payload.model_dump(exclude_unset=True)
    current.update(updates)
    _upsert_setting(db, CLOUD_ENDPOINTS_SETTING_KEY, current)
    return CloudEndpointConfig(**current)


@router.get("/admin/dataset-access", response_model=DatasetAccessConfig)
def get_dataset_access(db: Session = Depends(get_db)) -> DatasetAccessConfig:
    setting = _get_setting(db, DATASET_ACCESS_SETTING_KEY)
    payload = _coerce_dict(setting.value) if setting else {}
    datasets = payload.get("datasets") if payload else None
    if not isinstance(datasets, dict):
        datasets = DEFAULT_DATASET_ACCESS
    return DatasetAccessConfig(datasets=datasets)


@router.put("/admin/dataset-access", response_model=DatasetAccessConfig)
def update_dataset_access(
    payload: DatasetAccessConfig,
    db: Session = Depends(get_db),
) -> DatasetAccessConfig:
    value = payload.model_dump()
    _upsert_setting(db, DATASET_ACCESS_SETTING_KEY, value)
    return payload
