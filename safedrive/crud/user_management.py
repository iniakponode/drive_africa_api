from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from fastapi import HTTPException
import logging
import hashlib
import secrets

from safedrive.models.auth import ApiClient
from safedrive.schemas.user_management import UserAccountCreate, UserAccountUpdate

logger = logging.getLogger(__name__)


class CRUDUserAccount:
    """CRUD operations for user account management."""

    def __init__(self, model):
        self.model = model

    def get(self, db: Session, user_id: UUID) -> Optional[ApiClient]:
        """Get a user by ID with related data."""
        try:
            return (
                db.query(self.model)
                .options(
                    joinedload(self.model.insurance_partner)
                )
                .filter(self.model.id == user_id.bytes)
                .first()
            )
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            raise

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 25,
        role: Optional[str] = None,
        search: Optional[str] = None,
        fleet_id: Optional[UUID] = None,
        insurance_partner_id: Optional[UUID] = None,
        active: Optional[bool] = None
    ) -> Tuple[List[ApiClient], int]:
        """
        Get multiple users with filters and pagination.
        Returns (users, total_count).
        """
        try:
            query = db.query(self.model)

            # Apply filters
            filters = []
            
            if role:
                filters.append(self.model.role == role)
            
            if fleet_id:
                filters.append(self.model.fleet_id == fleet_id.bytes)
            
            if insurance_partner_id:
                filters.append(self.model.insurance_partner_id == insurance_partner_id.bytes)
            
            if active is not None:
                filters.append(self.model.active == active)
            
            # Search functionality (case-insensitive)
            if search:
                search_term = f"%{search}%"
                search_filters = []
                
                # Search in name (if exists)
                search_filters.append(self.model.name.ilike(search_term))
                
                # Search in email (if the column exists, otherwise skip)
                if hasattr(self.model, 'email'):
                    search_filters.append(self.model.email.ilike(search_term))
                
                # Search by ID (convert UUID to string for searching)
                try:
                    # If search term looks like a UUID, search by ID
                    if len(search) >= 8:  # Minimum UUID prefix length
                        search_filters.append(
                            func.lower(func.cast(self.model.id, String)).like(f"{search.lower()}%")
                        )
                except:
                    pass
                
                filters.append(or_(*search_filters))

            if filters:
                query = query.filter(and_(*filters))

            # Get total count before pagination
            total = query.count()

            # Apply pagination and eager load relationships
            users = (
                query
                .options(joinedload(self.model.insurance_partner))
                .order_by(self.model.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )

            return users, total

        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            raise

    def create(self, db: Session, obj_in: UserAccountCreate) -> ApiClient:
        """Create a new user account."""
        try:
            # Generate API key hash if password is provided
            api_key = secrets.token_urlsafe(32)
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Prepare user data
            user_data = {
                "name": obj_in.name or obj_in.email.split('@')[0],
                "role": obj_in.role,
                "active": obj_in.active,
                "api_key_hash": api_key_hash,
                "fleet_id": obj_in.fleet_id,
                "insurance_partner_id": obj_in.insurance_partner_id,
                "driverProfileId": obj_in.driver_profile_id,
            }

            # Add email if the column exists
            if hasattr(self.model, 'email'):
                user_data["email"] = obj_in.email

            db_obj = self.model(**user_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            
            logger.info(f"Created user {db_obj.id} with role {db_obj.role}")
            logger.info(f"Generated API key for user: {api_key}")
            
            return db_obj

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

    def update(self, db: Session, db_obj: ApiClient, obj_in: UserAccountUpdate) -> ApiClient:
        """Update a user account."""
        try:
            obj_data = obj_in.model_dump(exclude_unset=True)

            for field, value in obj_data.items():
                # Map schema field names to model field names
                if field == "driver_profile_id":
                    setattr(db_obj, "driverProfileId", value)
                else:
                    setattr(db_obj, field, value)

            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated user {db_obj.id}")
            return db_obj

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

    def deactivate(self, db: Session, user_id: UUID) -> ApiClient:
        """Soft delete a user by setting active = False."""
        try:
            db_obj = self.get(db, user_id)
            if not db_obj:
                raise HTTPException(status_code=404, detail="User not found")

            db_obj.active = False
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Deactivated user {user_id}")
            return db_obj

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error deactivating user: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error deactivating user: {str(e)}")

    def update_last_login(self, db: Session, user_id: UUID) -> None:
        """Update the last login timestamp for a user."""
        try:
            if hasattr(self.model, 'last_login_at'):
                db.query(self.model).filter(
                    self.model.id == user_id.bytes
                ).update({"last_login_at": datetime.utcnow()})
                db.commit()
        except Exception as e:
            logger.warning(f"Failed to update last login for user {user_id}: {str(e)}")
            # Don't raise exception - this is not critical


# Import to avoid circular dependency
from sqlalchemy import String

# Create singleton instance
crud_user_account = CRUDUserAccount(ApiClient)
