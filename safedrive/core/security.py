from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import false
from sqlalchemy.orm import Session

from safedrive.database.db import get_db
from safedrive.models.auth import ApiClient
from safedrive.models.fleet import DriverFleetAssignment
from safedrive.models.insurance_partner import InsurancePartnerDriver


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
            db.query(DriverFleetAssignment.driverProfileId)
            .filter(DriverFleetAssignment.fleet_id == client.fleet_id)
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
