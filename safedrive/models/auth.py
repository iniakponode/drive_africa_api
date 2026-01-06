from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from safedrive.database.base import Base


class ApiClient(Base):
    __tablename__ = "api_client"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    api_key_hash = Column(String(64), nullable=False, unique=True)
    active = Column(Boolean, nullable=False, default=True)
    driverProfileId = Column(
        UUIDType(binary=True),
        ForeignKey("driver_profile.driverProfileId"),
        nullable=True,
    )
    fleet_id = Column(UUIDType(binary=True), ForeignKey("fleet.id"), nullable=True)
    insurance_partner_id = Column(
        UUIDType(binary=True),
        ForeignKey("insurance_partner.id"),
        nullable=True,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    insurance_partner = relationship("InsurancePartner", back_populates="api_clients")

    def __repr__(self) -> str:
        return f"<ApiClient(id={self.id}, name={self.name}, role={self.role})>"
