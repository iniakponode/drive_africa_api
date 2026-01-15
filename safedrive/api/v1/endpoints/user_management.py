from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from safedrive.core.security import (
    ApiClientContext,
    Role,
    require_roles,
)
from safedrive.database.db import get_db
from safedrive.models.auth import ApiClient
from safedrive.models.fleet import Fleet
from safedrive.models.insurance_partner import InsurancePartner
from safedrive.crud.user_management import crud_user_account
from safedrive.schemas import user_management as user_schemas

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_user_response(user: ApiClient, db: Session) -> dict:
    """Build user response dict with related data."""
    response_data = {
        "id": user.id,
        "email": getattr(user, 'email', user.name + "@generated.local"),
        "name": user.name,
        "role": user.role,
        "active": user.active,
        "fleet_id": user.fleet_id,
        "insurance_partner_id": user.insurance_partner_id,
        "driver_profile_id": user.driverProfileId,
        "created_at": user.created_at,
        "last_login_at": getattr(user, 'last_login_at', None),
    }

    # Add fleet details if fleet_id exists
    if user.fleet_id:
        fleet = db.query(Fleet).filter(Fleet.id == user.fleet_id).first()
        if fleet:
            response_data["fleet"] = {
                "id": fleet.id,
                "name": fleet.name,
                "description": fleet.description,
                "region": fleet.region,
                "created_at": fleet.created_at
            }
        else:
            response_data["fleet"] = None
    else:
        response_data["fleet"] = None

    # Add insurance partner details if exists
    if user.insurance_partner_id and user.insurance_partner:
        response_data["insurance_partner"] = {
            "id": user.insurance_partner.id,
            "name": user.insurance_partner.name,
            "label": user.insurance_partner.label,
            "active": user.insurance_partner.active,
            "created_at": user.insurance_partner.created_at
        }
    else:
        response_data["insurance_partner"] = None

    return response_data


@router.get(
    "/admin/users",
    response_model=user_schemas.UserAccountListResponse,
    summary="List users",
    description="Get a paginated, filterable list of user accounts (admin only)"
)
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role"),
    search: Optional[str] = Query(None, description="Search by email, name, or ID"),
    fleet_id: Optional[UUID] = Query(None, description="Filter by fleet ID"),
    insurance_partner_id: Optional[UUID] = Query(None, description="Filter by insurance partner ID"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN))
):
    """
    List all user accounts with optional filtering and pagination.
    
    **Authorization:** Admin only
    
    **Filters:**
    - role: Filter by user role (admin, driver, researcher, fleet_manager, insurance_partner)
    - search: Search by email, name, or user ID (case-insensitive partial match)
    - fleet_id: Filter by assigned fleet
    - insurance_partner_id: Filter by assigned insurance partner
    - active: Filter by active status
    
    **Pagination:**
    - page: Page number (1-indexed)
    - page_size: Items per page (max 100)
    """
    skip = (page - 1) * page_size
    
    users, total = crud_user_account.get_multi(
        db,
        skip=skip,
        limit=page_size,
        role=role,
        search=search,
        fleet_id=fleet_id,
        insurance_partner_id=insurance_partner_id,
        active=active
    )

    # Build response with related data
    user_responses = []
    for user in users:
        user_data = _build_user_response(user, db)
        user_responses.append(user_schemas.UserAccountResponse(**user_data))

    return user_schemas.UserAccountListResponse(
        users=user_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/admin/users/{user_id}",
    response_model=user_schemas.UserAccountResponse,
    summary="Get single user",
    description="Get detailed information about a specific user (admin only)"
)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN))
):
    """
    Get a single user account by ID.
    
    **Authorization:** Admin only
    
    **Returns:** Full user account details including related fleet and insurance partner data.
    """
    user = crud_user_account.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user_data = _build_user_response(user, db)
    return user_schemas.UserAccountResponse(**user_data)


@router.post(
    "/admin/users",
    response_model=user_schemas.UserAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    description="Create a new user account (admin only)"
)
def create_user(
    user_in: user_schemas.UserAccountCreate,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN))
):
    """
    Create a new user account.
    
    **Authorization:** Admin only
    
    **Validation:**
    - Email must be unique
    - Role must be valid (admin, driver, researcher, fleet_manager, insurance_partner)
    - fleet_id required for fleet_manager role
    - insurance_partner_id required for insurance_partner role
    - driver_profile_id required for driver role
    
    **Returns:** Created user account with generated API key logged to server.
    """
    # Validate role-specific requirements
    if user_in.role == "fleet_manager" and not user_in.fleet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fleet_id is required for fleet_manager role"
        )
    
    if user_in.role == "insurance_partner" and not user_in.insurance_partner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="insurance_partner_id is required for insurance_partner role"
        )
    
    if user_in.role == "driver" and not user_in.driver_profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="driver_profile_id is required for driver role"
        )

    # Verify foreign key references exist
    if user_in.fleet_id:
        fleet = db.query(Fleet).filter(Fleet.id == user_in.fleet_id.bytes).first()
        if not fleet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fleet not found"
            )

    if user_in.insurance_partner_id:
        partner = db.query(InsurancePartner).filter(
            InsurancePartner.id == user_in.insurance_partner_id.bytes
        ).first()
        if not partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance partner not found"
            )

    user = crud_user_account.create(db, user_in)
    user_data = _build_user_response(user, db)
    return user_schemas.UserAccountResponse(**user_data)


@router.patch(
    "/admin/users/{user_id}",
    response_model=user_schemas.UserAccountResponse,
    summary="Update user",
    description="Update an existing user account (admin only)"
)
def update_user(
    user_id: UUID,
    user_in: user_schemas.UserAccountUpdate,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN))
):
    """
    Update an existing user account.
    
    **Authorization:** Admin only
    
    **Note:** All fields are optional. Only provided fields will be updated.
    
    **Validation:**
    - If changing role, ensure role-specific fields are valid
    - Verify foreign key references exist
    """
    user = crud_user_account.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify foreign key references if provided
    if user_in.fleet_id:
        fleet = db.query(Fleet).filter(Fleet.id == user_in.fleet_id.bytes).first()
        if not fleet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fleet not found"
            )

    if user_in.insurance_partner_id:
        partner = db.query(InsurancePartner).filter(
            InsurancePartner.id == user_in.insurance_partner_id.bytes
        ).first()
        if not partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance partner not found"
            )

    user = crud_user_account.update(db, user, user_in)
    user_data = _build_user_response(user, db)
    return user_schemas.UserAccountResponse(**user_data)


@router.delete(
    "/admin/users/{user_id}",
    response_model=user_schemas.UserDeactivateResponse,
    summary="Deactivate user",
    description="Soft-delete a user by setting active=false (admin only)"
)
def deactivate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    client: ApiClientContext = Depends(require_roles(Role.ADMIN))
):
    """
    Deactivate a user account (soft delete).
    
    **Authorization:** Admin only
    
    **Note:** This sets active=false rather than deleting the record,
    preserving data integrity and audit trail.
    """
    user = crud_user_account.deactivate(db, user_id)
    return user_schemas.UserDeactivateResponse(
        message="User deactivated successfully",
        user_id=user.id
    )
