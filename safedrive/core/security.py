from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import false
from sqlalchemy.orm import Session

from safedrive.database.db import get_db
from safedrive.models.auth import ApiClient
from safedrive.models.admin_setting import AdminSetting
from safedrive.models.fleet import OldDriverFleetAssignment
from safedrive.models.insurance_partner import InsurancePartnerDriver
from safedrive.models.driver_profile import DriverProfile


class Role(str, Enum):
    ADMIN = "admin"
    DRIVER = "driver"
    RESEARCHER = "researcher"
    FLEET_MANAGER = "fleet_manager"
    INSURANCE_PARTNER = "insurance_partner"


@dataclass(frozen=True)
class ApiClientContext:
    id: UUID
    name: str
    role: Role
    driver_profile_id: Optional[UUID]
    fleet_id: Optional[UUID]
    insurance_partner_id: Optional[UUID]
    allowed_driver_ids: Optional[Set[UUID]]


DATASET_ACCESS_SETTING_KEY = "dataset_access"
DEFAULT_DATASET_ACCESS = {
    "researcher_unsafe_behaviours": ["admin", "researcher"],
    "researcher_raw_sensor_data": ["admin", "researcher"],
    "researcher_alcohol_trip_bundle": ["admin", "researcher"],
    "researcher_nlg_reports": ["admin", "researcher"],
    "researcher_raw_sensor_export": ["admin", "researcher"],
    "researcher_trips_export": ["admin", "researcher"],
    "researcher_aggregate_snapshot": ["admin", "researcher"],
    "researcher_ingestion_status": ["admin", "researcher"],
    "behaviour_metrics": ["admin", "researcher", "fleet_manager", "insurance_partner"],
    "fleet_monitoring": ["admin", "fleet_manager"],
    "fleet_assignments": ["admin", "fleet_manager"],
    "fleet_events": ["admin", "fleet_manager"],
    "fleet_trip_context": ["admin", "fleet_manager"],
    "fleet_reports": ["admin", "fleet_manager"],
    "insurance_telematics": ["admin", "insurance_partner"],
    "insurance_reports": ["admin", "insurance_partner"],
    "insurance_raw_sensor_export": ["admin", "insurance_partner"],
    "insurance_alerts": ["admin", "insurance_partner"],
    "insurance_aggregate_reports": ["admin", "insurance_partner"],
}


def hash_api_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_allowed_driver_ids(
    db: Session,
    role: Role,
    client: ApiClient,
) -> Optional[Set[UUID]]:
    if role == Role.DRIVER:
        if not client.driverProfileId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Driver scope is missing for this API key.",
            )
        return {client.driverProfileId}
    if role == Role.FLEET_MANAGER:
        if not client.fleet_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Fleet scope is missing for this API key.",
            )
        rows = (
            db.query(OldDriverFleetAssignment.driverProfileId)
            .filter(OldDriverFleetAssignment.fleet_id == client.fleet_id)
            .all()
        )
        return {row[0] for row in rows}
    if role == Role.INSURANCE_PARTNER:
        if not client.insurance_partner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insurance partner scope is missing for this API key.",
            )
        rows = (
            db.query(InsurancePartnerDriver.driverProfileId)
            .filter(InsurancePartnerDriver.partner_id == client.insurance_partner_id)
            .all()
        )
        return {row[0] for row in rows}
    return None


def get_current_client(
    api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> ApiClientContext:
    key_hash = hash_api_key(api_key)
    client = (
        db.query(ApiClient)
        .filter(ApiClient.api_key_hash == key_hash, ApiClient.active.is_(True))
        .first()
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key.",
        )
    try:
        role = Role(client.role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unsupported role for this API key.",
        ) from exc
    allowed_driver_ids = _load_allowed_driver_ids(db, role, client)
    return ApiClientContext(
        id=client.id,
        name=client.name,
        role=role,
        driver_profile_id=client.driverProfileId,
        fleet_id=client.fleet_id,
        insurance_partner_id=client.insurance_partner_id,
        allowed_driver_ids=allowed_driver_ids,
    )


def require_roles(*roles: Role):
    def _dependency(
        client: ApiClientContext = Depends(get_current_client),
    ) -> ApiClientContext:
        if roles and client.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this resource.",
            )
        return client

    return _dependency


def _dataset_access_config(db: Session) -> dict:
    setting = (
        db.query(AdminSetting)
        .filter(AdminSetting.key == DATASET_ACCESS_SETTING_KEY)
        .first()
    )
    if not setting or not isinstance(setting.value, dict):
        return DEFAULT_DATASET_ACCESS
    datasets = setting.value.get("datasets")
    if isinstance(datasets, dict):
        return datasets
    return setting.value


def ensure_dataset_access(
    db: Session,
    client: ApiClientContext,
    dataset_key: str,
) -> None:
    if client.role == Role.ADMIN:
        return
    access_map = _dataset_access_config(db)
    allowed_roles = access_map.get(dataset_key)
    if not allowed_roles:
        return
    if client.role.value not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dataset access denied.",
        )


def ensure_driver_access(client: ApiClientContext, driver_id: UUID) -> None:
    if client.role in {Role.ADMIN, Role.RESEARCHER}:
        return
    if not client.allowed_driver_ids or driver_id not in client.allowed_driver_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver scope access denied.",
        )


def filter_query_by_driver_ids(query, driver_column, client: ApiClientContext):
    if client.role in {Role.ADMIN, Role.RESEARCHER}:
        return query
    if not client.allowed_driver_ids:
        return query.filter(false())
    return query.filter(driver_column.in_(client.allowed_driver_ids))


# JWT + API Key combined authentication
security_bearer = HTTPBearer(auto_error=False)


def get_current_client_or_driver(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> ApiClientContext:
    """
    Accepts either API Key (X-API-Key header) OR JWT token (Authorization: Bearer header).
    Used for endpoints that support both authentication methods.
    """
    # Try API Key first
    if api_key:
        key_hash = hash_api_key(api_key)
        client = (
            db.query(ApiClient)
            .filter(ApiClient.api_key_hash == key_hash, ApiClient.active.is_(True))
            .first()
        )
        if client:
            try:
                role = Role(client.role)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unsupported role for this API key.",
                ) from exc
            allowed_driver_ids = _load_allowed_driver_ids(db, role, client)
            return ApiClientContext(
                id=client.id,
                name=client.name,
                role=role,
                driver_profile_id=client.driverProfileId,
                fleet_id=client.fleet_id,
                insurance_partner_id=client.insurance_partner_id,
                allowed_driver_ids=allowed_driver_ids,
            )
    
    # Try JWT token
    if credentials and credentials.credentials:
        from safedrive.core.jwt_auth import decode_token
        
        try:
            payload = decode_token(credentials.credentials)
            driver_id = UUID(payload.get("sub"))
            
            # Get driver profile from database
            driver = db.query(DriverProfile).filter(
                DriverProfile.driverProfileId == driver_id
            ).first()
            
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Driver not found.",
                )
            
            # Return ApiClientContext for driver
            return ApiClientContext(
                id=driver_id,  # Use driver ID as client ID
                name=driver.email,
                role=Role.DRIVER,
                driver_profile_id=driver_id,
                fleet_id=None,
                insurance_partner_id=None,
                allowed_driver_ids={driver_id},
            )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT token.",
            )
    
    # No authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either X-API-Key or Authorization: Bearer token.",
    )


def require_roles_or_jwt(*roles: Role):
    """
    Dependency that accepts both API Key and JWT authentication.
    Use this for endpoints that should work for both API key users and JWT driver users.
    """
    def _dependency(
        client: ApiClientContext = Depends(get_current_client_or_driver),
    ) -> ApiClientContext:
        if roles and client.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this resource.",
            )
        return client

    return _dependency
