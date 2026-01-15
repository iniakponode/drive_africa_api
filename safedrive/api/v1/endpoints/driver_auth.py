"""Driver authentication endpoints for mobile app."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from safedrive.database.db import get_db
from safedrive.models.driver_profile import DriverProfile
from safedrive.schemas.auth import DriverRegister, DriverLogin, TokenResponse
from safedrive.schemas.driver_profile import DriverProfileResponse
from safedrive.core.jwt_auth import hash_password, verify_password, create_access_token, get_current_driver
from safedrive.crud import fleet_driver as crud_fleet

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/driver/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_driver(
    *,
    db: Session = Depends(get_db),
    driver_in: DriverRegister
) -> TokenResponse:
    """
    Register a new driver from the mobile app.
    Returns a JWT token for immediate use.
    
    **AUTO-FLEET ASSIGNMENT**: If there's a pending email invitation for this email,
    the driver will be automatically assigned to the fleet.
    """
    # Check if email already exists
    existing = db.query(DriverProfile).filter(DriverProfile.email == driver_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create driver profile with hashed password
    hashed_pwd = hash_password(driver_in.password)
    new_driver = DriverProfile(
        driverProfileId=driver_in.driverProfileId,
        email=driver_in.email,
        password_hash=hashed_pwd,
        sync=driver_in.sync
    )
    
    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)
    
    logger.info(f"Driver registered: {new_driver.email} ({new_driver.driverProfileId})")
    
    # Check for pending email invitation
    fleet_assignment = None
    pending_invite = crud_fleet.crud_driver_invite.get_pending_by_email(
        db, email=driver_in.email
    )
    
    if pending_invite:
        logger.info(f"Found pending invite for {driver_in.email}, auto-assigning to fleet {pending_invite.fleet_id}")
        
        # Claim the invitation
        crud_fleet.crud_driver_invite.claim(
            db,
            invite_id=pending_invite.id,
            driver_profile_id=new_driver.driverProfileId,
        )
        
        # Create fleet assignment
        assignment = crud_fleet.crud_driver_fleet_assignment.create(
            db,
            fleet_id=pending_invite.fleet_id,
            driver_profile_id=new_driver.driverProfileId,
            vehicle_group_id=pending_invite.vehicle_group_id,
            assigned_by=pending_invite.created_by,
        )
        
        # Build fleet assignment info for response
        fleet_name = assignment.fleet.name if assignment.fleet else "Unknown Fleet"
        vehicle_group_name = (
            assignment.vehicle_group.name if assignment.vehicle_group else None
        )
        
        fleet_assignment = {
            "fleet_id": str(assignment.fleet_id),
            "fleet_name": fleet_name,
            "vehicle_group_id": str(assignment.vehicle_group_id) if assignment.vehicle_group_id else None,
            "vehicle_group_name": vehicle_group_name,
            "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
        }
    
    # Generate JWT token
    token = create_access_token(new_driver.driverProfileId, new_driver.email)
    
    response_data = {
        "access_token": token,
        "driver_profile_id": new_driver.driverProfileId,
        "email": new_driver.email,
    }
    
    # Add fleet_assignment to response if driver was auto-assigned
    if fleet_assignment:
        response_data["fleet_assignment"] = fleet_assignment
    
    return TokenResponse(**response_data)


@router.post("/driver/login", response_model=TokenResponse)
def login_driver(
    *,
    db: Session = Depends(get_db),
    credentials: DriverLogin
) -> TokenResponse:
    """
    Login an existing driver from the mobile app.
    Returns a JWT token with fleet status information.
    """
    # Find driver by email
    driver = db.query(DriverProfile).filter(DriverProfile.email == credentials.email).first()
    
    if not driver or not driver.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, driver.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    logger.info(f"Driver logged in: {driver.email} ({driver.driverProfileId})")
    
    # Get fleet status
    fleet_status = None
    assignment = crud_fleet.crud_driver_fleet_assignment.get_by_driver(
        db, driver_profile_id=driver.driverProfileId
    )
    
    if assignment:
        # Driver is assigned to a fleet
        vehicle_info = None
        # TODO: Get vehicle from driver_vehicle_assignment when available
        
        fleet_status = {
            "status": "assigned",
            "fleet": {
                "id": str(assignment.fleet.id),
                "name": assignment.fleet.name,
            } if assignment.fleet else None,
            "vehicle_group": {
                "id": str(assignment.vehicle_group.id),
                "name": assignment.vehicle_group.name,
            } if assignment.vehicle_group else None,
            "vehicle": vehicle_info,
            "pending_request": None,
        }
    else:
        # Check for pending request
        pending_request = crud_fleet.crud_driver_join_request.get_pending_by_driver(
            db, driver_profile_id=driver.driverProfileId
        )
        
        if pending_request:
            fleet_status = {
                "status": "pending",
                "fleet": None,
                "vehicle_group": None,
                "vehicle": None,
                "pending_request": {
                    "id": str(pending_request.id),
                    "fleet_name": pending_request.fleet.name if pending_request.fleet else "Unknown",
                    "requested_at": pending_request.requested_at.isoformat() if pending_request.requested_at else None,
                },
            }
        else:
            fleet_status = {
                "status": "none",
                "fleet": None,
                "vehicle_group": None,
                "vehicle": None,
                "pending_request": None,
            }
    
    # Generate JWT token
    token = create_access_token(driver.driverProfileId, driver.email)
    
    response_data = {
        "access_token": token,
        "driver_profile_id": driver.driverProfileId,
        "email": driver.email,
        "fleet_status": fleet_status,
    }
    
    return TokenResponse(**response_data)


@router.get("/driver/me", response_model=DriverProfileResponse)
def get_current_driver_profile(
    driver: DriverProfile = Depends(get_current_driver)
) -> DriverProfileResponse:
    """
    Get the current authenticated driver's profile.
    Requires JWT token in Authorization header.
    """
    return DriverProfileResponse(
        driverProfileId=driver.driverProfileId,
        email=driver.email,
        sync=driver.sync
    )
