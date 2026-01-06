from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, JSON, String
from sqlalchemy_utils import UUIDType

from safedrive.database.base import Base


class AdminSetting(Base):
    __tablename__ = "admin_setting"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return f"<AdminSetting(key={self.key})>"
