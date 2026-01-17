"""Fleet driver management API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from safedrive.core.security import Role, get_current_client, get_current_client_or_driver, require_roles
from safedrive.crud import fleet_driver as crud
from safedrive.database.db import get_db
from safedrive.models.auth import ApiClient
from safedrive.models.fleet import Fleet
from safedrive.models.fleet_driver import FleetInviteCode
from safedrive.schemas import fleet_driver as schemas

router = APIRouter()


# --- Scoped Endpoints for Fleet Managers (MUST BE FIRST) ---
# These routes match "/fleet/my/..." and must be defined BEFORE
# the parameterized routes like "/fleet/{fleet_id}/..." to avoid
# FastAPI treating "my" as a UUID parameter


@router.get(
    "/fleet/my/invite-codes",
    response_model=schemas.FleetInviteCodeListResponse,
    summary="List my fleet's invite codes",
)
def list_my_fleet_invite_codes(
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.FLEET_MANAGER)),
):
    """
    List all invite codes for the authenticated fleet manager's fleet.
    
    **Authorization:** Fleet manager only
    """
    if not current_client.fleet_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fleet manager must be assigned to a fleet",
        )
    
    invite_codes = crud.crud_fleet_invite_code.get_by_fleet(db, fleet_id=current_client.fleet_id)
    return {"invite_codes": invite_codes}


@router.post(
    "/fleet/my/invite-codes",
    response_model=schemas.FleetInviteCodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invite code for my fleet",
)
def create_my_fleet_invite_code(
    payload: schemas.FleetInviteCodeCreate,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.FLEET_MANAGER)),
):
    """
    Create an invite code for the authenticated fleet manager's fleet.
    
    **Authorization:** Fleet manager only
    """
    if not current_client.fleet_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fleet manager must be assigned to a fleet",
        )
    
    # Check if fleet exists
    fleet = db.query(Fleet).filter(Fleet.id == current_client.fleet_id).first()
    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")
    
    # Create invite code using fleet manager's fleet_id
    invite_code = crud.crud_fleet_invite_code.create(
        db,
        fleet_id=current_client.fleet_id,
        created_by=current_client.id,
        expires_at=payload.expires_at,
        max_uses=payload.max_uses,
    )
    
    return invite_code


@router.delete(
    "/fleet/my/invite-codes/{code_id}",
    response_model=dict,
    summary="Revoke invite code from my fleet",
)
def revoke_my_fleet_invite_code(
    code_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.FLEET_MANAGER)),
):
    """
    Revoke an invite code from the authenticated fleet manager's fleet.
    
    **Authorization:** Fleet manager only
    """
    if not current_client.fleet_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fleet manager must be assigned to a fleet",
        )
    
    # Verify the code belongs to the fleet manager's fleet
    code = db.query(FleetInviteCode).filter(FleetInviteCode.id == code_id).first()
    if not code or str(code.fleet_id) != str(current_client.fleet_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite code not found in your fleet",
        )
    
    success = crud.crud_fleet_invite_code.revoke(db, code_id=code_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite code not found",
        )
    
    return {"message": "Invite code revoked successfully"}


@router.get(
    "/fleet/my/driver-invites",
    response_model=schemas.DriverInviteListResponse,
    summary="List my fleet's driver invitations",
)
def list_my_fleet_driver_invites(
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.FLEET_MANAGER)),
):
    """
    List driver invitations for the authenticated fleet manager's fleet.
    
    **Authorization:** Fleet manager (fleet_id derived from auth token)
    """
    if not current_client.fleet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fleet manager is not associated with a fleet",
        )
    
    skip = (page - 1) * page_size
    invites, total = crud.crud_driver_invite.get_by_fleet(
        db,
        fleet_id=current_client.fleet_id,
        status=status_filter,
        skip=skip,
        limit=page_size,
    )
    
    return {
        "invites": invites,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "/fleet/my/driver-invites",
    response_model=schemas.DriverInviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite driver to my fleet",
)
def create_my_fleet_driver_invite(
    data: schemas.DriverInviteCreate,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.FLEET_MANAGER)),
):
    """
    Invite a driver to the authenticated fleet manager's fleet.
    
    **Authorization:** Fleet manager (fleet_id derived from auth token)
    """
    if not current_client.fleet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fleet manager is not associated with a fleet",
        )
    
    # TODO: Send email if data.send_email is True
    
    invite = crud.crud_driver_invite.create(
        db,
        fleet_id=current_client.fleet_id,
        email=data.email,
        created_by=current_client.id,
        vehicle_group_id=data.vehicle_group_id,
        expires_at=data.expires_at,
    )
    
    return invite


@router.post(
    "/fleet/my/driver-invites/{invite_id}/resend",
    response_model=dict,
    summary="Resend invitation email from my fleet",
)
def resend_my_fleet_driver_invite(
    invite_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.FLEET_MANAGER)),
):
    """
    Resend an invitation email from the authenticated fleet manager's fleet.
    
    **Authorization:** Fleet manager (fleet_id derived from auth token)
    """
    if not current_client.fleet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fleet manager is not associated with a fleet",
        )
    
    invite = crud.crud_driver_invite.get(db, invite_id=invite_id)
    if not invite or str(invite.fleet_id) != str(current_client.fleet_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    
    # TODO: Implement email sending
    
    return {"message": f"Invitation email resent to {invite.email}"}


@router.delete(
    "/fleet/my/driver-invites/{invite_id}",
    response_model=dict,
    summary="Cancel driver invitation from my fleet",
)
def cancel_my_fleet_driver_invite(
    invite_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.FLEET_MANAGER)),
):
    """
    Cancel a pending invitation from the authenticated fleet manager's fleet.
    
    **Authorization:** Fleet manager (fleet_id derived from auth token)
    """
    if not current_client.fleet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fleet manager is not associated with a fleet",
        )
    
    invite = crud.crud_driver_invite.get(db, invite_id=invite_id)
    if not invite or str(invite.fleet_id) != str(current_client.fleet_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found in your fleet",
        )
    
    success = crud.crud_driver_invite.cancel(db, invite_id=invite_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already processed",
        )
    
    return {"message": "Invitation cancelled successfully"}


@router.get(
    "/fleet/my/drivers",
    response_model=schemas.FleetDriverListResponse,
    summary="List my fleet's drivers",
)
def list_my_fleet_drivers(
    search: Optional[str] = Query(None, description="Search by name or email"),
    vehicle_group_id: Optional[UUID] = Query(
        None, description="Filter by vehicle group"
    ),
    has_vehicle: Optional[bool] = Query(
        None, description="Filter by vehicle assignment status"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.FLEET_MANAGER)),
):
    """
    List drivers for the authenticated fleet manager's fleet.
    
    **Authorization:** Fleet manager (fleet_id derived from auth token)
    """
    if not current_client.fleet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fleet manager is not associated with a fleet",
        )
    
    skip = (page - 1) * page_size
    assignments, total = crud.crud_driver_fleet_assignment.get_by_fleet(
        db,
        fleet_id=current_client.fleet_id,
        search=search,
        vehicle_group_id=vehicle_group_id,
        has_vehicle=has_vehicle,
        skip=skip,
        limit=page_size,
    )
    
    # Build driver list with details
    drivers = []
    for assignment in assignments:
        driver_profile = assignment.driver_profile
        if not driver_profile:
            continue
        
        vehicle_info = None
        
        assignment_info = {
            "id": assignment.id,
            "vehicle_group_id": assignment.vehicle_group_id,
            "vehicle_group_name": (
                assignment.vehicle_group.name if assignment.vehicle_group else None
            ),
            "onboarding_completed": assignment.onboarding_completed,
            "assigned_at": assignment.assigned_at,
        }
        
        driver_info = {
            "driverProfileId": driver_profile.driverProfileId,
            "email": driver_profile.email,
            "name": getattr(driver_profile, "name", None),
            "phone": getattr(driver_profile, "phoneNumber", None),
            "assignment": assignment_info,
            "vehicle": vehicle_info,
            "safety_score": None,
            "total_trips": 0,
            "last_active": None,
        }
        drivers.append(driver_info)
    
    return {
        "drivers": drivers,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/fleet/my/join-requests",
    response_model=schemas.JoinRequestListResponse,
    summary="List my fleet's join requests",
)
def list_my_fleet_join_requests(
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status"
    ),
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.FLEET_MANAGER)),
):
    """
    List pending join requests for the authenticated fleet manager's fleet.
    
    **Authorization:** Fleet manager (fleet_id derived from auth token)
    """
    if not current_client.fleet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fleet manager is not associated with a fleet",
        )
    
    requests = crud.crud_driver_join_request.get_by_fleet(
        db, fleet_id=current_client.fleet_id, status=status_filter
    )
    
    # Build response with driver info
    request_list = []
    for req in requests:
        request_info = {
            "id": req.id,
            "fleet_id": req.fleet_id,
            "driver_profile_id": req.driver_profile_id,
            "driver_email": req.driver_profile.email if req.driver_profile else None,
            "driver_name": (
                getattr(req.driver_profile, "name", None)
                if req.driver_profile
                else None
            ),
            "invite_code_used": req.invite_code.code if req.invite_code else None,
            "status": req.status,
            "requested_at": req.requested_at,
        }
        request_list.append(request_info)
    
    return {"requests": request_list}


# --- Parameterized Fleet Endpoints (After "my" routes) ---


# --- Fleet Invite Codes ---


@router.get(
    "/fleet/{fleet_id}/invite-codes",
    response_model=schemas.FleetInviteCodeListResponse,
    summary="List fleet invite codes",
)
def list_fleet_invite_codes(
    fleet_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    List all invite codes for a fleet.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own fleet's invite codes",
            )
    
    invite_codes = crud.crud_fleet_invite_code.get_by_fleet(db, fleet_id=fleet_id)
    return {"invite_codes": invite_codes}


@router.post(
    "/fleet/{fleet_id}/invite-codes",
    response_model=schemas.FleetInviteCodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create fleet invite code",
)
def create_fleet_invite_code(
    fleet_id: UUID,
    data: schemas.FleetInviteCodeCreate,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    Create a new invite code for a fleet.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create invite codes for your own fleet",
            )
    
    invite_code = crud.crud_fleet_invite_code.create(
        db,
        fleet_id=fleet_id,
        created_by=current_client.id,
        expires_at=data.expires_at,
        max_uses=data.max_uses,
    )
    return invite_code


@router.delete(
    "/fleet/{fleet_id}/invite-codes/{code_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke invite code",
)
def revoke_fleet_invite_code(
    fleet_id: UUID,
    code_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    Revoke an invite code.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only revoke your own fleet's invite codes",
            )
    
    success = crud.crud_fleet_invite_code.revoke(db, code_id=code_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite code not found",
        )
    
    return None


# --- Driver Email Invitations ---


@router.get(
    "/fleet/{fleet_id}/driver-invites",
    response_model=schemas.DriverInviteListResponse,
    summary="List driver invitations",
)
def list_driver_invites(
    fleet_id: UUID,
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    List driver invitations for a fleet.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own fleet's invitations",
            )
    
    skip = (page - 1) * page_size
    invites, total = crud.crud_driver_invite.get_by_fleet(
        db, fleet_id=fleet_id, status=status_filter, skip=skip, limit=page_size
    )
    
    return {
        "invites": invites,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "/fleet/{fleet_id}/driver-invites",
    response_model=schemas.DriverInviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite driver by email",
)
def create_driver_invite(
    fleet_id: UUID,
    data: schemas.DriverInviteCreate,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    Invite a driver by email. Creates a pending invitation.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only invite drivers to your own fleet",
            )
    
    # TODO: Send email if data.send_email is True
    
    invite = crud.crud_driver_invite.create(
        db,
        fleet_id=fleet_id,
        email=data.email,
        created_by=current_client.id,
        vehicle_group_id=data.vehicle_group_id,
        expires_at=data.expires_at,
    )
    
    return invite


@router.post(
    "/fleet/{fleet_id}/driver-invites/{invite_id}/resend",
    response_model=dict,
    summary="Resend invitation email",
)
def resend_driver_invite(
    fleet_id: UUID,
    invite_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    Resend the invitation email.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only resend invitations from your own fleet",
            )
    
    invite = crud.crud_driver_invite.get(db, invite_id=invite_id)
    if not invite or str(invite.fleet_id) != str(fleet_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    
    # TODO: Implement email sending
    
    return {"message": f"Invitation email resent to {invite.email}"}


@router.delete(
    "/fleet/{fleet_id}/driver-invites/{invite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel driver invitation",
)
def cancel_driver_invite(
    fleet_id: UUID,
    invite_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    Cancel a pending invitation.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel invitations from your own fleet",
            )
    
    success = crud.crud_driver_invite.cancel(db, invite_id=invite_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already processed",
        )
    
    return None


# --- Driver Join Requests ---


@router.get(
    "/fleet/{fleet_id}/join-requests",
    response_model=schemas.JoinRequestListResponse,
    summary="List join requests",
)
def list_join_requests(
    fleet_id: UUID,
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status"
    ),
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    List pending join requests for a fleet.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own fleet's join requests",
            )
    
    requests = crud.crud_driver_join_request.get_by_fleet(
        db, fleet_id=fleet_id, status=status_filter
    )
    
    # Build response with driver info
    request_list = []
    for req in requests:
        request_info = {
            "id": req.id,
            "fleet_id": req.fleet_id,
            "driver_profile_id": req.driver_profile_id,
            "driver_email": req.driver_profile.email if req.driver_profile else None,
            "driver_name": (
                getattr(req.driver_profile, "name", None)
                if req.driver_profile
                else None
            ),
            "invite_code_used": req.invite_code.code if req.invite_code else None,
            "status": req.status,
            "requested_at": req.requested_at,
        }
        request_list.append(request_info)
    
    return {"requests": request_list}


@router.post(
    "/fleet/{fleet_id}/join-requests/{request_id}/approve",
    response_model=dict,
    summary="Approve join request",
)
def approve_join_request(
    fleet_id: UUID,
    request_id: UUID,
    data: schemas.JoinRequestApprove,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    Approve a join request and create the fleet assignment.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only approve requests for your own fleet",
            )
    
    # Approve the request
    request = crud.crud_driver_join_request.approve(
        db,
        request_id=request_id,
        reviewed_by=current_client.id,
        vehicle_group_id=data.vehicle_group_id,
    )
    
    # Create the fleet assignment
    assignment = crud.crud_driver_fleet_assignment.create(
        db,
        fleet_id=fleet_id,
        driver_profile_id=request.driver_profile_id,
        vehicle_group_id=data.vehicle_group_id,
        assigned_by=current_client.id,
    )
    
    return {
        "message": "Driver approved and assigned to fleet",
        "assignment_id": str(assignment.id),
    }


@router.post(
    "/fleet/{fleet_id}/join-requests/{request_id}/reject",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reject join request",
)
def reject_join_request(
    fleet_id: UUID,
    request_id: UUID,
    data: schemas.JoinRequestReject,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    Reject a join request.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only reject requests for your own fleet",
            )
    
    crud.crud_driver_join_request.reject(
        db,
        request_id=request_id,
        reviewed_by=current_client.id,
        reason=data.reason,
    )
    
    return None


# --- Fleet Drivers Management ---


@router.get(
    "/fleet/{fleet_id}/drivers",
    response_model=schemas.FleetDriverListResponse,
    summary="List fleet drivers",
)
def list_fleet_drivers(
    fleet_id: UUID,
    search: Optional[str] = Query(None, description="Search by name or email"),
    vehicle_group_id: Optional[UUID] = Query(
        None, description="Filter by vehicle group"
    ),
    has_vehicle: Optional[bool] = Query(
        None, description="Filter by vehicle assignment status"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    List all drivers assigned to a fleet.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own fleet's drivers",
            )
    
    skip = (page - 1) * page_size
    assignments, total = crud.crud_driver_fleet_assignment.get_by_fleet(
        db,
        fleet_id=fleet_id,
        search=search,
        vehicle_group_id=vehicle_group_id,
        has_vehicle=has_vehicle,
        skip=skip,
        limit=page_size,
    )
    
    # Build driver list with details
    drivers = []
    for assignment in assignments:
        driver_profile = assignment.driver_profile
        if not driver_profile:
            continue
        
        # Get vehicle info if assigned
        vehicle_info = None
        # TODO: Get vehicle from driver_vehicle_assignment when available
        
        # Build assignment info
        assignment_info = {
            "id": assignment.id,
            "vehicle_group_id": assignment.vehicle_group_id,
            "vehicle_group_name": (
                assignment.vehicle_group.name if assignment.vehicle_group else None
            ),
            "onboarding_completed": assignment.onboarding_completed,
            "assigned_at": assignment.assigned_at,
        }
        
        driver_info = {
            "driverProfileId": driver_profile.driverProfileId,
            "email": driver_profile.email,
            "name": getattr(driver_profile, "name", None),
            "phone": getattr(driver_profile, "phoneNumber", None),
            "assignment": assignment_info,
            "vehicle": vehicle_info,
            "safety_score": None,  # TODO: Calculate from trips
            "total_trips": 0,  # TODO: Count from trips
            "last_active": None,  # TODO: Get from last trip
        }
        drivers.append(driver_info)
    
    return {
        "drivers": drivers,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "/fleet/{fleet_id}/drivers",
    response_model=schemas.FleetAssignmentInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Manually add driver to fleet",
)
def add_driver_to_fleet(
    fleet_id: UUID,
    data: schemas.FleetDriverAdd,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN)),
):
    """
    Manually add a driver to a fleet (admin only).
    
    **Authorization:** Admin only
    """
    assignment = crud.crud_driver_fleet_assignment.create(
        db,
        fleet_id=fleet_id,
        driver_profile_id=data.driver_profile_id,
        vehicle_group_id=data.vehicle_group_id,
        assigned_by=current_client.id,
    )
    
    return assignment


@router.put(
    "/fleet/{fleet_id}/drivers/{driver_profile_id}",
    response_model=schemas.FleetAssignmentInfo,
    summary="Update driver's fleet assignment",
)
@router.patch(
    "/fleet/{fleet_id}/drivers/{driver_profile_id}",
    response_model=schemas.FleetAssignmentInfo,
    summary="Update driver's fleet assignment",
)
def update_fleet_driver(
    fleet_id: UUID,
    driver_profile_id: UUID,
    data: schemas.FleetDriverUpdate,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    Update a driver's fleet assignment.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update drivers in your own fleet",
            )
    
    # Get assignment to get its ID
    assignment = crud.crud_driver_fleet_assignment.get_by_driver(
        db, driver_profile_id=driver_profile_id
    )
    if not assignment or str(assignment.fleet_id) != str(fleet_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found in this fleet",
        )
    
    updated_assignment = crud.crud_driver_fleet_assignment.update(
        db,
        assignment_id=assignment.id,
        vehicle_group_id=data.vehicle_group_id,
        onboarding_completed=data.onboarding_completed,
        compliance_note=data.compliance_note,
    )
    
    return updated_assignment


@router.delete(
    "/fleet/{fleet_id}/drivers/{driver_profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove driver from fleet",
)
def remove_driver_from_fleet(
    fleet_id: UUID,
    driver_profile_id: UUID,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER)),
):
    """
    Remove a driver from a fleet.
    
    **Authorization:** Fleet manager of this fleet, or admin
    """
    # Validate fleet access for fleet managers
    if current_client.role == Role.FLEET_MANAGER.value:
        if str(current_client.fleet_id) != str(fleet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only remove drivers from your own fleet",
            )
    
    # Verify driver is in this fleet
    assignment = crud.crud_driver_fleet_assignment.get_by_driver(
        db, driver_profile_id=driver_profile_id
    )
    if not assignment or str(assignment.fleet_id) != str(fleet_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found in this fleet",
        )
    
    success = crud.crud_driver_fleet_assignment.delete(
        db, driver_profile_id=driver_profile_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver assignment not found",
        )
    
    return None


# --- Admin Endpoints ---


@router.get(
    "/admin/drivers/unassigned",
    response_model=schemas.UnassignedDriverListResponse,
    summary="Get unassigned drivers",
)
def get_unassigned_drivers(
    search: Optional[str] = Query(None, description="Search by email or name"),
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.ADMIN)),
):
    """
    Search for drivers not assigned to any fleet.
    
    **Authorization:** Admin only
    """
    drivers = crud.crud_driver_fleet_assignment.get_unassigned_drivers(
        db, search=search
    )
    
    return {"drivers": drivers}


# --- Mobile App Endpoints ---


@router.post(
    "/driver/join-fleet",
    response_model=schemas.DriverJoinRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit join request with invite code",
)
def submit_join_request(
    data: schemas.DriverJoinRequestSubmit,
    db: Session = Depends(get_db),
    current_client = Depends(get_current_client_or_driver),
):
    """
    Submit a request to join a fleet using an invite code.
    
    **Authorization:** Authenticated driver (JWT or API Key)
    """
    # Verify user is a driver
    if current_client.role != Role.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can join fleets",
        )
    
    # Check if driver already has a fleet
    existing_assignment = crud.crud_driver_fleet_assignment.get_by_driver(
        db, driver_profile_id=current_client.driverProfileId
    )
    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "ALREADY_IN_FLEET",
                    "message": "You are already a member of a fleet",
                }
            },
        )
    
    # Validate invite code
    invite_code = crud.crud_fleet_invite_code.get_by_code(db, code=data.invite_code)
    if not invite_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_CODE",
                    "message": "This invite code is invalid or has been revoked.",
                }
            },
        )
    
    if not invite_code.is_active:
        if invite_code.revoked_at:
            error_code = "INVALID_CODE"
            message = "This invite code has been revoked."
        elif invite_code.expires_at and invite_code.expires_at < crud.datetime.utcnow():
            error_code = "EXPIRED_CODE"
            message = "This invite code has expired."
        elif invite_code.max_uses and invite_code.use_count >= invite_code.max_uses:
            error_code = "CODE_LIMIT_REACHED"
            message = "This invite code has reached its usage limit."
        else:
            error_code = "INVALID_CODE"
            message = "This invite code is no longer valid."
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": error_code, "message": message}},
        )
    
    # Create join request
    request = crud.crud_driver_join_request.create(
        db,
        fleet_id=invite_code.fleet_id,
        driver_profile_id=current_client.driverProfileId,
        invite_code_id=invite_code.id,
    )
    
    # Increment invite code use count
    crud.crud_fleet_invite_code.increment_use_count(db, code_id=invite_code.id)
    
    # Get fleet name
    fleet = db.query(Fleet).filter(Fleet.id == invite_code.fleet_id).first()
    fleet_name = fleet.name if fleet else "Unknown Fleet"
    
    return {
        "message": "Join request submitted",
        "request_id": request.id,
        "fleet_name": fleet_name,
        "status": "pending",
    }


@router.get(
    "/driver/fleet-status",
    response_model=schemas.FleetStatusResponse,
    summary="Get driver's fleet status",
)
def get_driver_fleet_status(
    db: Session = Depends(get_db),
    current_client = Depends(get_current_client_or_driver),
):
    """
    Get the driver's current fleet membership status.
    
    **Authorization:** Authenticated driver (JWT or API Key)
    """
    if current_client.role != Role.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can check fleet status",
        )
    
    # Check if driver is assigned to a fleet
    assignment = crud.crud_driver_fleet_assignment.get_by_driver(
        db, driver_profile_id=current_client.driverProfileId
    )
    
    if assignment:
        # Driver is assigned
        vehicle_info = None
        # TODO: Get vehicle from driver_vehicle_assignment
        
        return {
            "status": "assigned",
            "fleet": {"id": assignment.fleet.id, "name": assignment.fleet.name}
            if assignment.fleet
            else None,
            "vehicle_group": (
                {"id": assignment.vehicle_group.id, "name": assignment.vehicle_group.name}
                if assignment.vehicle_group
                else None
            ),
            "vehicle": vehicle_info,
            "pending_request": None,
        }
    
    # Check for pending request
    pending_request = crud.crud_driver_join_request.get_pending_by_driver(
        db, driver_profile_id=current_client.driverProfileId
    )
    
    if pending_request:
        # Driver has pending request
        return {
            "status": "pending",
            "fleet": None,
            "vehicle_group": None,
            "vehicle": None,
            "pending_request": {
                "id": pending_request.id,
                "fleet_name": pending_request.fleet.name if pending_request.fleet else "Unknown",
                "requested_at": pending_request.requested_at,
            },
        }
    
    # Driver is not in fleet and has no pending request
    return {
        "status": "none",
        "fleet": None,
        "vehicle_group": None,
        "vehicle": None,
        "pending_request": None,
    }


@router.delete(
    "/driver/join-request",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel pending join request",
)
def cancel_driver_join_request(
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(get_current_client),
):
    """
    Cancel the driver's pending join request.
    
    **Authorization:** Authenticated driver (JWT)
    """
    if current_client.role != Role.DRIVER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can cancel join requests",
        )
    
    success = crud.crud_driver_join_request.cancel_by_driver(
        db, driver_profile_id=current_client.driverProfileId
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NO_PENDING_REQUEST",
                    "message": "No pending join request found",
                }
            },
        )
    
    return None
