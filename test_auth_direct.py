#!/usr/bin/env python3
import sys
import hashlib
sys.path.insert(0, '/var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from safedrive.models.auth import ApiClient

DATABASE_URL = 'mysql+pymysql://dev2:ProgressIniks2018@localhost:3306/drive_safe_db'

# Test API key
test_key = "02QDlql_JlwQXjdcj-Awsw8gBPs06-6JEP-aasDKf38"
key_hash = hashlib.sha256(test_key.encode("utf-8")).hexdigest()

print(f"Testing API Key: {test_key}")
print(f"Computed Hash: {key_hash}\n")

# Query database
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

client = (
    db.query(ApiClient)
    .filter(ApiClient.api_key_hash == key_hash, ApiClient.active.is_(True))
    .first()
)

if client:
    print(f"✓ API Client Found!")
    print(f"  ID: {client.id}")
    print(f"  Name: {client.name}")
    print(f"  Role: {client.role}")
    print(f"  Active: {client.active}")
else:
    print("✗ No client found with this hash")
    
    # Check if hash exists at all
    any_client = db.query(ApiClient).filter(ApiClient.api_key_hash == key_hash).first()
    if any_client:
        print(f"  Hash found but client is inactive: {any_client.name}")
    else:
        print("  Hash not found in database at all")
        
db.close()
