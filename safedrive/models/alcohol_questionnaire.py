from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
from safedrive.database.base import Base
from uuid import uuid4

class AlcoholQuestionnaire(Base):
    __tablename__ = "alcohol_questionnaire"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid4)
    driverProfileId = Column(UUIDType(binary=True), ForeignKey("driver_profile.driverProfileId"), nullable=False)
    drankAlcohol = Column(Boolean, nullable=False)
    selectedAlcoholTypes = Column(Text, nullable=False)
    beerQuantity = Column(String(255), nullable=False)
    wineQuantity = Column(String(255), nullable=False)
    spiritsQuantity = Column(String(255), nullable=False)
    firstDrinkTime = Column(String(255), nullable=False)
    lastDrinkTime = Column(String(255), nullable=False)
    emptyStomach = Column(Boolean, nullable=False)
    caffeinatedDrink = Column(Boolean, nullable=False)
    impairmentLevel = Column(Integer, nullable=False)
    date = Column(DateTime)
    plansToDrive = Column(Boolean, nullable=False)
    sync=Column(Boolean, nullable=False)

    driver_profile = relationship("DriverProfile", back_populates="alcohol_questionnaires")
