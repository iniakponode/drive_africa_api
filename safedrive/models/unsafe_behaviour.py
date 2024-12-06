from typing import Optional
from sqlalchemy import Column, Float, String, DateTime, Boolean, ForeignKey, BINARY, Integer
from sqlalchemy.orm import relationship
from safedrive.database.base import Base
from uuid import uuid4, UUID

def generate_uuid_binary():
    return uuid4().bytes

class UnsafeBehaviour(Base):
    """
    Represents the unsafe_behaviour table in the database.

    Attributes:
    - **id**: Unique identifier for the unsafe behaviour.
    - **trip_id**: Foreign key to Trip model representing the trip associated with the unsafe behaviour.
    - **location_id**: Foreign key to Location model representing the location associated with the behaviour.
    - **behaviour_type**: Type of the unsafe behaviour detected.
    - **severity**: Severity level of the unsafe behaviour.
    - **timestamp**: The Unix timestamp representing the time when the behaviour was detected.
    - **date**: The date when the behaviour occurred.
    - **updated_at**: The timestamp when the record was last updated.
    - **updated**: Flag indicating if the behaviour record was updated.
    - **synced**: Flag indicating if the record has been synced with external storage.
    - **alcohol_influence**: Flag indicating if the behaviour was influenced by alcohol.

    Relationships:
    - **trip**: Relationship with the Trip model.
    - **location**: Relationship with the Location model.
    """

    __tablename__ = "unsafe_behaviour"

    id = Column(BINARY(16), primary_key=True, default=generate_uuid_binary)
    trip_id = Column(BINARY(16), ForeignKey('trip.id'), nullable=False)
    driver_profile_id = Column(BINARY(16), ForeignKey('driver_profile.driver_profile_id'), nullable=False)
    location_id = Column(BINARY(16), ForeignKey('location.id'), nullable=True)
    behaviour_type = Column(String(255), nullable=False)
    severity = Column(Float, nullable=False)
    timestamp = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    updated = Column(Boolean, default=False)
    synced = Column(Boolean, default=False)
    alcohol_influence = Column(Boolean, default=False)

    # Relationships
    location = relationship("Location", back_populates="unsafe_behaviours")
    trip = relationship("Trip", back_populates="unsafe_behaviours")
    causes = relationship("Cause", back_populates="unsafe_behaviour", cascade="all, delete-orphan")
    driver_profile=relationship("DriverProfile", back_populates="unsafe_behaviours")

    def __repr__(self):
        return f"<UnsafeBehaviour(id={self.id.hex()}, behaviour_type='{self.behaviour_type}', severity='{self.severity}')>"

    @property
    def id_uuid(self) -> UUID:
        """Return the UUID representation of the binary ID."""
        return UUID(bytes=self.id)

    @property
    def trip_id_uuid(self) -> UUID:
        """Return the UUID representation of the binary trip_id."""
        return UUID(bytes=self.trip_id)

    @property
    def location_id_uuid(self) -> Optional[UUID]:
        """Return the UUID representation of the binary location_id."""
        return UUID(bytes=self.location_id) if self.location_id else None
    
    @property
    def driver_profile_id_uuid(self) -> UUID:
        """Return the UUID representation of the binary driver_profile_id."""
        return UUID(bytes=self.driver_profile_id)