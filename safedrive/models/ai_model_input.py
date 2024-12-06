from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, BINARY
from sqlalchemy.orm import relationship
from safedrive.database.base import Base
from uuid import uuid4, UUID

def generate_uuid_binary():
    return uuid4().bytes

class AIModelInput(Base):
    """
    SQLAlchemy model for AI Model Input.

    Attributes:
    - **id**: Primary key, stored as BINARY(16).
    - **trip_id**: Foreign key referencing Trip.id, stored as BINARY(16).
    - **timestamp**: Timestamp of the AI model input.
    - **date**: Date of the AI model input.
    - **hour_of_day_mean**: Mean hour of the day.
    - **day_of_week_mean**: Mean day of the week.
    - **speed_std**: Standard deviation of speed.
    - **course_std**: Standard deviation of course.
    - **acceleration_y_original_mean**: Mean of original Y-axis acceleration.
    """
    __tablename__ = 'ai_model_inputs'
    
    id = Column(BINARY(16), primary_key=True, default=generate_uuid_binary)
    trip_id = Column(BINARY(16), ForeignKey('trip.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    date = Column(DateTime, nullable=False)
    hour_of_day_mean = Column(Float, nullable=False)
    day_of_week_mean = Column(Float, nullable=False)
    speed_std = Column(Float, nullable=False)
    course_std = Column(Float, nullable=False)
    acceleration_y_original_mean = Column(Float, nullable=False)
    synced=Column(Boolean, nullable=False, default=False)

    # Relationships
    trip = relationship('Trip', back_populates='ai_model_inputs')

    def __repr__(self):
        return f"<AIModelInput(id={self.id.hex()}, trip_id={self.trip_id.hex()})>"

    @property
    def id_uuid(self) -> UUID:
        """Return the UUID representation of the binary ID."""
        return UUID(bytes=self.id)

    @property
    def trip_id_uuid(self) -> UUID:
        """Return the UUID representation of the binary trip_id."""
        return UUID(bytes=self.trip_id)