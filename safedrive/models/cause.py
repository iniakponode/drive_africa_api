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

class Cause(Base):
    """
    Cause model representing possible causes linked to unsafe behaviors.

    Attributes:
    - **id**: Unique identifier for each cause.
    - **unsafe_behaviour_id**: Foreign key linking to the unsafe behavior associated with this cause.
    - **name**: Description or name of the cause.
    - **influence**: Boolean indicating if the cause has significant influence.
    - **created_at**: Timestamp when the cause was recorded.
    - **updated_at**: Timestamp when the cause was last updated.

    Relationships:
    - **unsafe_behaviour**: Many-to-One relationship with UnsafeBehaviour.
    """
    __tablename__ = "causes"

    id = Column(BINARY(16), primary_key=True, unique=True, default=generate_uuid_binary)
    unsafe_behaviour_id = Column(BINARY(16), ForeignKey('unsafe_behaviour.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    influence = Column(Boolean, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    synced=Column(Boolean, nullable=False, default=False)

    # Relationships
    unsafe_behaviour = relationship("UnsafeBehaviour", back_populates="causes")

    def __repr__(self):
        return f"<Cause(id={self.id.hex()}, name={self.name})>"

    @property
    def id_uuid(self) -> UUID:
        """Convert binary UUID to string format for JSON responses and logs retrieval."""
        uuid_value = UUID(bytes=self.id)
        logger.debug(f"Retrieved UUID for Cause: {uuid_value}")
        return uuid_value