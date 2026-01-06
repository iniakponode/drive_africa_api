from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient

from safedrive.database.base import Base
from safedrive.database.db import get_db
from safedrive.main import app
from safedrive.core.security import hash_api_key
from safedrive.models.admin_setting import AdminSetting
from safedrive.models.auth import ApiClient
from safedrive.models.insurance_partner import InsurancePartner, InsurancePartnerDriver
from uuid import uuid4

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def create_tables():
    Base.metadata.create_all(bind=engine)


def drop_tables():
    Base.metadata.drop_all(bind=engine)


def create_api_client(
    db,
    role: str,
    driver_profile_id=None,
    fleet_id=None,
    insurance_partner_id=None,
    active: bool = True,
):
    raw_key = f"test-{role}-{uuid4()}"
    client = ApiClient(
        name=f"{role}-test-client",
        role=role,
        active=active,
        driverProfileId=driver_profile_id,
        fleet_id=fleet_id,
        insurance_partner_id=insurance_partner_id,
        api_key_hash=hash_api_key(raw_key),
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return raw_key
