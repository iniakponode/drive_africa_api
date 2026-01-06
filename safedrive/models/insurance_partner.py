from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from safedrive.database.base import Base


class InsurancePartner(Base):
    __tablename__ = "insurance_partner"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    label = Column(String(100), nullable=False, unique=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    drivers = relationship(
        "InsurancePartnerDriver",
        back_populates="partner",
        cascade="all, delete-orphan",
    )
    api_clients = relationship("ApiClient", back_populates="insurance_partner")

    def __repr__(self) -> str:
        return f"<InsurancePartner(id={self.id}, label={self.label})>"


class InsurancePartnerDriver(Base):
    __tablename__ = "insurance_partner_driver"
    __table_args__ = (
        UniqueConstraint("partner_id", "driverProfileId", name="uq_partner_driver"),
    )

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    partner_id = Column(
        UUIDType(binary=True),
        ForeignKey("insurance_partner.id", ondelete="CASCADE"),
        nullable=False,
    )
    driverProfileId = Column(
        UUIDType(binary=True),
        ForeignKey("driver_profile.driverProfileId"),
        nullable=False,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    partner = relationship("InsurancePartner", back_populates="drivers")

    def __repr__(self) -> str:
        return (
            f"<InsurancePartnerDriver(partner_id={self.partner_id}, "
            f"driverProfileId={self.driverProfileId})>"
        )
