from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, or_
from fastapi import HTTPException
import logging

from safedrive.models.vehicle import Vehicle, DriverVehicleAssignment
from safedrive.models.driver_profile import DriverProfile
from safedrive.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleBulkCreateItem

logger = logging.getLogger(__name__)


class CRUDVehicle:
    """CRUD operations for the Vehicle model."""

    def __init__(self, model):
        self.model = model

    def get(self, db: Session, vehicle_id: UUID) -> Optional[Vehicle]:
        """Get a vehicle by ID."""
        try:
            return db.query(self.model).filter(self.model.id == vehicle_id.bytes).first()
        except Exception as e:
            logger.error(f"Error getting vehicle {vehicle_id}: {str(e)}")
            raise

    def get_multi(
        self,
        db: Session,
        *,
        fleet_id: Optional[UUID] = None,
        vehicle_group_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 25
    ) -> tuple[List[Vehicle], int]:
        """
        Get multiple vehicles with filters and pagination.
        Returns (vehicles, total_count).
        """
        try:
            query = db.query(self.model)

            # Apply filters
            if fleet_id:
                query = query.filter(self.model.fleet_id == fleet_id.bytes)
            if vehicle_group_id:
                query = query.filter(self.model.vehicle_group_id == vehicle_group_id.bytes)
            if status:
                query = query.filter(self.model.status == status)

            # Get total count before pagination
            total = query.count()

            # Apply pagination and eager load relationships
            vehicles = (
                query
                .options(
                    joinedload(self.model.fleet),
                    joinedload(self.model.vehicle_group),
                    joinedload(self.model.driver_assignments).joinedload(DriverVehicleAssignment.driver_profile)
                )
                .order_by(self.model.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )

            return vehicles, total

        except Exception as e:
            logger.error(f"Error getting vehicles: {str(e)}")
            raise

    def create(self, db: Session, obj_in: VehicleCreate) -> Vehicle:
        """Create a new vehicle."""
        try:
            # Check for duplicate license plate
            existing = db.query(self.model).filter(self.model.license_plate == obj_in.license_plate).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"Vehicle with license plate {obj_in.license_plate} already exists")

            # Check for duplicate VIN if provided
            if obj_in.vin:
                existing_vin = db.query(self.model).filter(self.model.vin == obj_in.vin).first()
                if existing_vin:
                    raise HTTPException(status_code=400, detail=f"Vehicle with VIN {obj_in.vin} already exists")

            obj_data = obj_in.model_dump()
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created vehicle {db_obj.id_uuid} with license plate {db_obj.license_plate}")
            return db_obj

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating vehicle: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating vehicle: {str(e)}")

    def update(self, db: Session, db_obj: Vehicle, obj_in: VehicleUpdate) -> Vehicle:
        """Update a vehicle."""
        try:
            obj_data = obj_in.model_dump(exclude_unset=True)

            # Check for duplicate license plate if being updated
            if "license_plate" in obj_data:
                existing = (
                    db.query(self.model)
                    .filter(
                        and_(
                            self.model.license_plate == obj_data["license_plate"],
                            self.model.id != db_obj.id
                        )
                    )
                    .first()
                )
                if existing:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Vehicle with license plate {obj_data['license_plate']} already exists"
                    )

            # Check for duplicate VIN if being updated
            if "vin" in obj_data and obj_data["vin"]:
                existing_vin = (
                    db.query(self.model)
                    .filter(
                        and_(
                            self.model.vin == obj_data["vin"],
                            self.model.id != db_obj.id
                        )
                    )
                    .first()
                )
                if existing_vin:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Vehicle with VIN {obj_data['vin']} already exists"
                    )

            for field, value in obj_data.items():
                setattr(db_obj, field, value)

            db_obj.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated vehicle {db_obj.id_uuid}")
            return db_obj

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating vehicle: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error updating vehicle: {str(e)}")

    def delete(self, db: Session, vehicle_id: UUID) -> Vehicle:
        """
        Soft delete a vehicle by setting status to 'retired'.
        This preserves trip history.
        """
        try:
            db_obj = self.get(db, vehicle_id)
            if not db_obj:
                raise HTTPException(status_code=404, detail="Vehicle not found")

            db_obj.status = "retired"
            db_obj.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Soft deleted vehicle {vehicle_id} (set to retired)")
            return db_obj

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting vehicle: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error deleting vehicle: {str(e)}")

    def batch_create(self, db: Session, objs_in: List[VehicleBulkCreateItem]) -> dict:
        """
        Bulk create vehicles.
        Returns dict with counts: {created, updated, skipped, errors}
        """
        created = 0
        updated = 0
        skipped = 0
        errors = []

        for idx, obj_in in enumerate(objs_in):
            try:
                # Check if vehicle exists by license plate
                existing = db.query(self.model).filter(
                    self.model.license_plate == obj_in.license_plate
                ).first()

                if existing:
                    # Update existing vehicle
                    obj_data = obj_in.model_dump(exclude_unset=True, exclude={"license_plate"})
                    for field, value in obj_data.items():
                        if value is not None:  # Only update non-None values
                            setattr(existing, field, value)
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                    logger.debug(f"Updated existing vehicle: {obj_in.license_plate}")
                else:
                    # Create new vehicle
                    obj_data = obj_in.model_dump()
                    db_obj = self.model(**obj_data)
                    db.add(db_obj)
                    created += 1
                    logger.debug(f"Created new vehicle: {obj_in.license_plate}")

                # Commit after each vehicle to avoid rolling back all on error
                db.commit()

            except Exception as e:
                db.rollback()
                error_msg = f"Row {idx + 1} (license_plate={obj_in.license_plate}): {str(e)}"
                errors.append(error_msg)
                skipped += 1
                logger.warning(f"Skipped vehicle creation: {error_msg}")

        return {
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "errors": errors
        }


class CRUDDriverVehicleAssignment:
    """CRUD operations for the DriverVehicleAssignment model."""

    def __init__(self, model):
        self.model = model

    def get_active_assignment(
        self,
        db: Session,
        driver_id: UUID,
        vehicle_id: UUID
    ) -> Optional[DriverVehicleAssignment]:
        """Get active assignment between driver and vehicle."""
        try:
            return (
                db.query(self.model)
                .filter(
                    and_(
                        self.model.driver_profile_id == driver_id.bytes,
                        self.model.vehicle_id == vehicle_id.bytes,
                        self.model.unassigned_at.is_(None)
                    )
                )
                .first()
            )
        except Exception as e:
            logger.error(f"Error getting assignment: {str(e)}")
            raise

    def get_vehicle_drivers(
        self,
        db: Session,
        vehicle_id: UUID,
        active_only: bool = True
    ) -> List[DriverVehicleAssignment]:
        """Get all drivers assigned to a vehicle."""
        try:
            query = (
                db.query(self.model)
                .filter(self.model.vehicle_id == vehicle_id.bytes)
                .options(joinedload(self.model.driver_profile))
            )

            if active_only:
                query = query.filter(self.model.unassigned_at.is_(None))

            return query.order_by(self.model.is_primary.desc(), self.model.assigned_at.desc()).all()

        except Exception as e:
            logger.error(f"Error getting vehicle drivers: {str(e)}")
            raise

    def get_driver_vehicles(
        self,
        db: Session,
        driver_id: UUID,
        active_only: bool = True
    ) -> List[DriverVehicleAssignment]:
        """Get all vehicles assigned to a driver."""
        try:
            query = (
                db.query(self.model)
                .filter(self.model.driver_profile_id == driver_id.bytes)
                .options(joinedload(self.model.vehicle))
            )

            if active_only:
                query = query.filter(self.model.unassigned_at.is_(None))

            return query.order_by(self.model.is_primary.desc(), self.model.assigned_at.desc()).all()

        except Exception as e:
            logger.error(f"Error getting driver vehicles: {str(e)}")
            raise

    def assign_driver(
        self,
        db: Session,
        driver_id: UUID,
        vehicle_id: UUID,
        is_primary: bool = False
    ) -> DriverVehicleAssignment:
        """Assign a driver to a vehicle."""
        try:
            # Check if assignment already exists
            existing = self.get_active_assignment(db, driver_id, vehicle_id)
            if existing:
                # Update is_primary if different
                if existing.is_primary != is_primary:
                    existing.is_primary = is_primary
                    db.commit()
                    db.refresh(existing)
                    logger.info(f"Updated assignment: driver {driver_id} to vehicle {vehicle_id}")
                return existing

            # If setting as primary, unset other primary assignments for this driver
            if is_primary:
                other_primaries = (
                    db.query(self.model)
                    .filter(
                        and_(
                            self.model.driver_profile_id == driver_id.bytes,
                            self.model.is_primary.is_(True),
                            self.model.unassigned_at.is_(None)
                        )
                    )
                    .all()
                )
                for assignment in other_primaries:
                    assignment.is_primary = False
                    logger.debug(f"Removed primary flag from assignment {assignment.id_uuid}")

            # Create new assignment
            assignment = self.model(
                driver_profile_id=driver_id,
                vehicle_id=vehicle_id,
                is_primary=is_primary
            )
            db.add(assignment)
            db.commit()
            db.refresh(assignment)
            logger.info(f"Created assignment: driver {driver_id} to vehicle {vehicle_id}")
            return assignment

        except Exception as e:
            db.rollback()
            logger.error(f"Error assigning driver: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error assigning driver: {str(e)}")

    def unassign_driver(
        self,
        db: Session,
        driver_id: UUID,
        vehicle_id: UUID
    ) -> bool:
        """Unassign a driver from a vehicle."""
        try:
            assignment = self.get_active_assignment(db, driver_id, vehicle_id)
            if not assignment:
                return False

            assignment.unassigned_at = datetime.utcnow()
            db.commit()
            logger.info(f"Unassigned driver {driver_id} from vehicle {vehicle_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error unassigning driver: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error unassigning driver: {str(e)}")


# Create singleton instances
crud_vehicle = CRUDVehicle(Vehicle)
crud_driver_vehicle_assignment = CRUDDriverVehicleAssignment(DriverVehicleAssignment)
