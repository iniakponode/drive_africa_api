from sqlalchemy import Column, String, DateTime, Boolean, BINARY, ForeignKey
from uuid import uuid4, UUID
from sqlalchemy.orm import relationship
from safedrive.database.base import Base
import logging

logger = logging.getLogger(__name__)

def generate_uuid_binary():
    return uuid4().bytes

class NLGReport(Base):
    """
    NLGReport model represents a generated report with metadata and associations.

    Attributes:
    - **id**: Primary key, UUID in binary format.
    - **user_id**: Foreign key, UUID in binary format, references the user who generated the report.
    - **report_text**: Text content of the generated report.
    - **generated_at**: Timestamp of report generation.
    - **synced**: Boolean indicating if the report is synced with a remote server.
    """
    __tablename__ = "nlg_report"

    id = Column(BINARY(16), primary_key=True, default=generate_uuid_binary)
    driver_profile_id = Column(BINARY(16), ForeignKey('driver_profile.driver_profile_id'), nullable=False)
    report_text = Column(String(500), nullable=False)
    generated_at = Column(DateTime, nullable=False)
    synced = Column(Boolean, nullable=False, default=False)
    
    driver_profile=relationship("DriverProfile", back_populates="nlg_reports")

    def __repr__(self):
        return f"<NLGReport(id={self.id.hex()}, driver_profile_id={self.driver_profile_id.hex()}, synced={self.synced})>"

    @property
    def id_uuid(self):
        return UUID(bytes=self.id)

    @property
    def user_id_uuid(self):
        return UUID(bytes=self.driver_profile_id)