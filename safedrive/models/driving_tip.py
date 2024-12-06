from uuid import uuid4, UUID
from sqlalchemy import Column, String, Boolean, BINARY, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from safedrive.database.base import Base
import logging

# Logger setup
logger = logging.getLogger(__name__)

def generate_uuid_binary():
    """Generate a binary UUID."""
    return uuid4().bytes

class DrivingTip(Base):
    """
    DrivingTip model representing driving advice and regulations.

    Attributes:
    - **tip_id**: Unique identifier for each driving tip.
    - **title**: Title or summary of the tip.
    - **meaning**: Explanation of the driving tip's meaning.
    - **penalty**: Any penalties associated with not following the tip.
    - **fine**: The amount of fine, if applicable.
    - **law**: Relevant law associated with the tip.
    - **hostility**: Describes hostility levels associated with the behavior.
    - **summary_tip**: A concise summary of the tip.
    - **sync**: Flag indicating if the data has been synced.
    - **date**: The date the tip was recorded.
    - **profile_id**: Foreign key linking to the driver profile associated with this tip.
    - **llm**: Specifies the large language model used for generating the tip.

    Relationships:
    - **profile**: Many-to-One relationship with DriverProfile.
    """
    __tablename__ = "driving_tips"

    tip_id = Column(BINARY(16), primary_key=True, unique=True, default=generate_uuid_binary)
    title = Column(String(255), nullable=False)
    meaning = Column(String(255), nullable=True)
    penalty = Column(String(255), nullable=True)
    fine = Column(String(255), nullable=True)
    law = Column(String(255), nullable=True)
    hostility = Column(String(255), nullable=True)
    summary_tip = Column(String(255), nullable=True)
    sync = Column(Boolean, nullable=False)
    date = Column(DateTime, nullable=False)
    profile_id = Column(BINARY(16), ForeignKey('driver_profile.driver_profile_id'), nullable=False)
    llm = Column(String(255), nullable=True)

    # Relationships
    profile = relationship("DriverProfile", back_populates="driving_tips")

    def __repr__(self):
        return f"<DrivingTip(tip_id={self.tip_id.hex()}, title={self.title})>"

    @property
    def id_uuid(self) -> UUID:
        """Convert binary UUID to string format for JSON responses and logs retrieval."""
        uuid_value = UUID(bytes=self.tip_id)
        logger.debug(f"Retrieved UUID for DrivingTip: {uuid_value}")
        return uuid_value