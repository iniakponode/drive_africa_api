"""CRUD operations for fleet driver management."""

import secrets
import string
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from safedrive.models.fleet_driver import (
    DriverFleetAssignment,
    DriverInvite,
    DriverJoinRequest,
    FleetInviteCode,
)
from safedrive.models.driver_profile import DriverProfile
from safedrive.models.fleet import Fleet, VehicleGroup


def generate_invite_code(fleet_name: str) -> str:
    """
    Generate a human-readable invite code.
    
    Format: {FLEET_PREFIX}-{RANDOM}
    Example: ABCT-X7K2M9
    """
    # Extract prefix from fleet name (first 3-4 alphabetic chars)
    prefix = "".join(c.upper() for c in fleet_name if c.isalpha())[:4]
    if len(prefix) < 3:
        prefix = prefix.ljust(3, "X")
    
    # Generate random suffix (6 characters)
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(chars) for _ in range(6))
    
    return f"{prefix}-{suffix}"


def generate_invite_token() -> str:
    """Generate a secure random invite token."""
    return secrets.token_urlsafe(32)


class CRUDFleetInviteCode:
    """CRUD operations for fleet invite codes."""

    def get_by_code(
        self, db: Session, *, code: str
    ) -> Optional[FleetInviteCode]:
        """Get invite code by code string."""
        return (
            db.query(FleetInviteCode)
            .filter(FleetInviteCode.code == code.upper())
            .first()
        )

    def get_by_fleet(
        self, db: Session, *, fleet_id: UUID
    ) -> List[FleetInviteCode]:
        """Get all invite codes for a fleet."""
        return (
            db.query(FleetInviteCode)
            .filter(FleetInviteCode.fleet_id == fleet_id)
            .order_by(FleetInviteCode.created_at.desc())
            .all()
        )

    def create(
        self,
        db: Session,
        *,
        fleet_id: UUID,
        created_by: UUID,
        expires_at: Optional[datetime] = None,
        max_uses: Optional[int] = None,
    ) -> FleetInviteCode:
        """Create a new fleet invite code."""
        # Get fleet name for code generation
        fleet = db.query(Fleet).filter(Fleet.id == fleet_id).first()
        if not fleet:
            raise HTTPException(status_code=404, detail="Fleet not found")
        
        # Generate unique code
        while True:
            code = generate_invite_code(fleet.name)
            existing = self.get_by_code(db, code=code)
            if not existing:
                break
        
        invite_code = FleetInviteCode(
            fleet_id=fleet_id,
            code=code,
            expires_at=expires_at,
            max_uses=max_uses,
            created_by=created_by,
        )
        db.add(invite_code)
        db.commit()
        db.refresh(invite_code)
        return invite_code

    def revoke(self, db: Session, *, code_id: UUID) -> bool:
        """Revoke an invite code."""
        invite_code = db.query(FleetInviteCode).filter(FleetInviteCode.id == code_id).first()
        if not invite_code:
            return False
        
        invite_code.revoked_at = datetime.utcnow()
        db.commit()
        return True

    def increment_use_count(self, db: Session, *, code_id: UUID) -> None:
        """Increment the use count of an invite code."""
        invite_code = db.query(FleetInviteCode).filter(FleetInviteCode.id == code_id).first()
        if invite_code:
            invite_code.use_count += 1
            db.commit()


class CRUDDriverInvite:
    """CRUD operations for driver email invitations."""

    def get(self, db: Session, *, invite_id: UUID) -> Optional[DriverInvite]:
        """Get a driver invite by ID."""
        return db.query(DriverInvite).filter(DriverInvite.id == invite_id).first()

    def get_by_email_and_fleet(
        self, db: Session, *, email: str, fleet_id: UUID
    ) -> Optional[DriverInvite]:
        """Get a pending invitation by email and fleet."""
        return (
            db.query(DriverInvite)
            .filter(
                and_(
                    DriverInvite.email == email.lower(),
                    DriverInvite.fleet_id == fleet_id,
                    DriverInvite.status == "pending",
                )
            )
            .first()
        )

    def get_pending_by_email(
        self, db: Session, *, email: str
    ) -> Optional[DriverInvite]:
        """Get any pending invitation for an email address."""
        return (
            db.query(DriverInvite)
            .filter(
                and_(
                    DriverInvite.email == email.lower(),
                    DriverInvite.status == "pending",
                )
            )
            .first()
        )

    def get_by_fleet(
        self,
        db: Session,
        *,
        fleet_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> tuple[List[DriverInvite], int]:
        """Get invitations for a fleet with optional status filter."""
        query = db.query(DriverInvite).filter(DriverInvite.fleet_id == fleet_id)
        
        if status:
            query = query.filter(DriverInvite.status == status)
        
        total = query.count()
        invites = query.order_by(DriverInvite.created_at.desc()).offset(skip).limit(limit).all()
        
        return invites, total

    def create(
        self,
        db: Session,
        *,
        fleet_id: UUID,
        email: str,
        created_by: UUID,
        vehicle_group_id: Optional[UUID] = None,
        expires_at: Optional[datetime] = None,
    ) -> DriverInvite:
        """Create a new driver invitation."""
        # Check for existing pending invitation
        existing = self.get_by_email_and_fleet(db, email=email, fleet_id=fleet_id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Active invitation already exists for this email",
            )
        
        # Generate unique invite token
        invite_token = generate_invite_token()
        
        invite = DriverInvite(
            fleet_id=fleet_id,
            email=email.lower(),
            invite_token=invite_token,
            created_by=created_by,
            vehicle_group_id=vehicle_group_id,
            expires_at=expires_at,
        )
        db.add(invite)
        db.commit()
        db.refresh(invite)
        return invite

    def claim(
        self,
        db: Session,
        *,
        invite_id: UUID,
        driver_profile_id: UUID,
    ) -> DriverInvite:
        """Claim an invitation when driver registers."""
        invite = self.get(db, invite_id=invite_id)
        if not invite:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        invite.status = "claimed"
        invite.claimed_at = datetime.utcnow()
        invite.driver_profile_id = driver_profile_id
        db.commit()
        db.refresh(invite)
        return invite

    def cancel(self, db: Session, *, invite_id: UUID) -> bool:
        """Cancel a pending invitation."""
        invite = self.get(db, invite_id=invite_id)
        if not invite or invite.status != "pending":
            return False
        
        invite.status = "cancelled"
        db.commit()
        return True


class CRUDDriverJoinRequest:
    """CRUD operations for driver join requests."""

    def get(
        self, db: Session, *, request_id: UUID
    ) -> Optional[DriverJoinRequest]:
        """Get a join request by ID."""
        return (
            db.query(DriverJoinRequest)
            .options(
                joinedload(DriverJoinRequest.fleet),
                joinedload(DriverJoinRequest.driver_profile),
                joinedload(DriverJoinRequest.invite_code),
            )
            .filter(DriverJoinRequest.id == request_id)
            .first()
        )

    def get_by_fleet(
        self,
        db: Session,
        *,
        fleet_id: UUID,
        status: Optional[str] = None,
    ) -> List[DriverJoinRequest]:
        """Get join requests for a fleet."""
        query = (
            db.query(DriverJoinRequest)
            .options(
                joinedload(DriverJoinRequest.driver_profile),
                joinedload(DriverJoinRequest.invite_code),
            )
            .filter(DriverJoinRequest.fleet_id == fleet_id)
        )
        
        if status:
            query = query.filter(DriverJoinRequest.status == status)
        
        return query.order_by(DriverJoinRequest.requested_at.desc()).all()

    def get_pending_by_driver(
        self, db: Session, *, driver_profile_id: UUID
    ) -> Optional[DriverJoinRequest]:
        """Get pending join request for a driver."""
        return (
            db.query(DriverJoinRequest)
            .options(joinedload(DriverJoinRequest.fleet))
            .filter(
                and_(
                    DriverJoinRequest.driver_profile_id == driver_profile_id,
                    DriverJoinRequest.status == "pending",
                )
            )
            .first()
        )

    def create(
        self,
        db: Session,
        *,
        fleet_id: UUID,
        driver_profile_id: UUID,
        invite_code_id: Optional[UUID] = None,
    ) -> DriverJoinRequest:
        """Create a new join request."""
        # Check for existing pending request
        existing = self.get_pending_by_driver(db, driver_profile_id=driver_profile_id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="You already have a pending join request",
            )
        
        request = DriverJoinRequest(
            fleet_id=fleet_id,
            driver_profile_id=driver_profile_id,
            invite_code_id=invite_code_id,
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        return request

    def approve(
        self,
        db: Session,
        *,
        request_id: UUID,
        reviewed_by: UUID,
        vehicle_group_id: Optional[UUID] = None,
    ) -> DriverJoinRequest:
        """Approve a join request."""
        request = self.get(db, request_id=request_id)
        if not request or request.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="Request not found or already processed",
            )
        
        request.status = "approved"
        request.reviewed_at = datetime.utcnow()
        request.reviewed_by = reviewed_by
        db.commit()
        db.refresh(request)
        return request

    def reject(
        self,
        db: Session,
        *,
        request_id: UUID,
        reviewed_by: UUID,
        reason: Optional[str] = None,
    ) -> DriverJoinRequest:
        """Reject a join request."""
        request = self.get(db, request_id=request_id)
        if not request or request.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="Request not found or already processed",
            )
        
        request.status = "rejected"
        request.reviewed_at = datetime.utcnow()
        request.reviewed_by = reviewed_by
        request.rejection_reason = reason
        db.commit()
        db.refresh(request)
        return request

    def cancel_by_driver(
        self, db: Session, *, driver_profile_id: UUID
    ) -> bool:
        """Cancel a driver's pending join request."""
        request = self.get_pending_by_driver(db, driver_profile_id=driver_profile_id)
        if not request:
            return False
        
        db.delete(request)
        db.commit()
        return True


class CRUDDriverFleetAssignment:
    """CRUD operations for driver fleet assignments."""

    def get(
        self, db: Session, *, assignment_id: UUID
    ) -> Optional[DriverFleetAssignment]:
        """Get a fleet assignment by ID."""
        return (
            db.query(DriverFleetAssignment)
            .filter(DriverFleetAssignment.id == assignment_id)
            .first()
        )

    def get_by_driver(
        self, db: Session, *, driver_profile_id: UUID
    ) -> Optional[DriverFleetAssignment]:
        """Get fleet assignment for a driver."""
        return (
            db.query(DriverFleetAssignment)
            .options(
                joinedload(DriverFleetAssignment.fleet),
                joinedload(DriverFleetAssignment.vehicle_group),
            )
            .filter(DriverFleetAssignment.driver_profile_id == driver_profile_id)
            .first()
        )

    def get_by_fleet(
        self,
        db: Session,
        *,
        fleet_id: UUID,
        search: Optional[str] = None,
        vehicle_group_id: Optional[UUID] = None,
        has_vehicle: Optional[bool] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> tuple[List[DriverFleetAssignment], int]:
        """Get driver assignments for a fleet with filters."""
        query = (
            db.query(DriverFleetAssignment)
            .options(
                joinedload(DriverFleetAssignment.driver_profile),
                joinedload(DriverFleetAssignment.vehicle_group),
            )
            .filter(DriverFleetAssignment.fleet_id == fleet_id)
        )
        
        if vehicle_group_id:
            query = query.filter(
                DriverFleetAssignment.vehicle_group_id == vehicle_group_id
            )
        
        if search:
            # Join with driver_profile to search by name or email
            query = query.join(DriverProfile).filter(
                or_(
                    DriverProfile.email.ilike(f"%{search}%"),
                    DriverProfile.name.ilike(f"%{search}%") if hasattr(DriverProfile, 'name') else False,
                )
            )
        
        # TODO: Add has_vehicle filter when driver_vehicle_assignment is available
        
        total = query.count()
        assignments = (
            query.order_by(DriverFleetAssignment.assigned_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return assignments, total

    def create(
        self,
        db: Session,
        *,
        fleet_id: UUID,
        driver_profile_id: UUID,
        vehicle_group_id: Optional[UUID] = None,
        assigned_by: Optional[UUID] = None,
    ) -> DriverFleetAssignment:
        """Create a new fleet assignment."""
        # Check if driver is already in a fleet
        existing = self.get_by_driver(db, driver_profile_id=driver_profile_id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Driver is already assigned to a fleet",
            )
        
        assignment = DriverFleetAssignment(
            fleet_id=fleet_id,
            driver_profile_id=driver_profile_id,
            vehicle_group_id=vehicle_group_id,
            assigned_by=assigned_by,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    def update(
        self,
        db: Session,
        *,
        assignment_id: UUID,
        vehicle_group_id: Optional[UUID] = None,
        onboarding_completed: Optional[bool] = None,
        compliance_note: Optional[str] = None,
    ) -> DriverFleetAssignment:
        """Update a fleet assignment."""
        assignment = self.get(db, assignment_id=assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        if vehicle_group_id is not None:
            assignment.vehicle_group_id = vehicle_group_id
        if onboarding_completed is not None:
            assignment.onboarding_completed = onboarding_completed
        if compliance_note is not None:
            assignment.compliance_note = compliance_note
        
        db.commit()
        db.refresh(assignment)
        return assignment

    def delete(self, db: Session, *, driver_profile_id: UUID) -> bool:
        """Remove a driver from their fleet."""
        assignment = self.get_by_driver(db, driver_profile_id=driver_profile_id)
        if not assignment:
            return False
        
        db.delete(assignment)
        db.commit()
        return True

    def get_unassigned_drivers(
        self, db: Session, *, search: Optional[str] = None
    ) -> List[DriverProfile]:
        """Get drivers not assigned to any fleet."""
        # Subquery to get all assigned driver IDs
        assigned_ids = db.query(DriverFleetAssignment.driver_profile_id).subquery()
        
        query = db.query(DriverProfile).filter(
            ~DriverProfile.driverProfileId.in_(assigned_ids)
        )
        
        if search:
            query = query.filter(
                or_(
                    DriverProfile.email.ilike(f"%{search}%"),
                    DriverProfile.name.ilike(f"%{search}%") if hasattr(DriverProfile, 'name') else False,
                )
            )
        
        return query.order_by(DriverProfile.created_at.desc()).all()


# Instantiate CRUD classes
crud_fleet_invite_code = CRUDFleetInviteCode()
crud_driver_invite = CRUDDriverInvite()
crud_driver_join_request = CRUDDriverJoinRequest()
crud_driver_fleet_assignment = CRUDDriverFleetAssignment()
