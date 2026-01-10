"""Driver authentication endpoints for mobile app."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from safedrive.database.db import get_db
from safedrive.models.driver_profile import DriverProfile
from safedrive.schemas.auth import DriverRegister, DriverLogin, TokenResponse
from safedrive.schemas.driver_profile import DriverProfileResponse
from safedrive.core.jwt_auth import hash_password, verify_password, create_access_token, get_current_driver

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
    
    # Generate JWT token
    token = create_access_token(new_driver.driverProfileId, new_driver.email)
    
    return TokenResponse(
        access_token=token,
        driver_profile_id=new_driver.driverProfileId,
        email=new_driver.email
    )


@router.post("/driver/login", response_model=TokenResponse)
def login_driver(
    *,
    db: Session = Depends(get_db),
    credentials: DriverLogin
) -> TokenResponse:
    """
    Login an existing driver from the mobile app.
    Returns a JWT token.
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
    
    # Generate JWT token
    token = create_access_token(driver.driverProfileId, driver.email)
    
    return TokenResponse(
        access_token=token,
        driver_profile_id=driver.driverProfileId,
        email=driver.email
    )


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
