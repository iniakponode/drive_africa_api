#!/usr/bin/env python3
"""
Seed script for Safe Drive Africa API - Production Database
Creates default API clients with keys for testing and initial setup.

Usage:
    python scripts/seed_api_keys.py

Output:
    Prints API keys to console - SAVE THESE KEYS SECURELY!
"""
import os
import sys
import secrets
from uuid import uuid4

# Add parent directory to path to import safedrive modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from safedrive.core.security import hash_api_key
from safedrive.models.auth import ApiClient
from safedrive.models.admin_setting import AdminSetting
import json


def get_db_session():
    """Create database session from environment variable."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_api_client_with_key(db, name: str, role: str, driver_profile_id=None, 
                                 fleet_id=None, insurance_partner_id=None):
    """Create an API client and return the raw key."""
    # Check if client already exists
    existing = db.query(ApiClient).filter(ApiClient.name == name).first()
    if existing:
        print(f"⚠️  Client '{name}' already exists. Skipping...")
        return None
    
    # Generate secure API key
    raw_key = secrets.token_urlsafe(32)
    
    client = ApiClient(
        id=uuid4(),
        name=name,
        role=role,
        active=True,
        driverProfileId=driver_profile_id,
        fleet_id=fleet_id,
        insurance_partner_id=insurance_partner_id,
        api_key_hash=hash_api_key(raw_key),
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    return {
        "id": str(client.id),
        "name": client.name,
        "role": client.role,
        "api_key": raw_key,
        "driverProfileId": str(client.driverProfileId) if client.driverProfileId else None,
        "fleet_id": str(client.fleet_id) if client.fleet_id else None,
        "insurance_partner_id": str(client.insurance_partner_id) if client.insurance_partner_id else None,
    }


def seed_default_dataset_access(db):
    """Seed default dataset access configuration if not exists."""
    existing = db.query(AdminSetting).filter(
        AdminSetting.key == "dataset_access"
    ).first()
    
    if existing:
        print("ℹ️  Dataset access configuration already exists")
        return
    
    default_config = {
        "datasets": {
            "researcher_unsafe_behaviours": ["admin", "researcher"],
            "researcher_raw_sensor_data": ["admin", "researcher"],
            "researcher_alcohol_trip_bundle": ["admin", "researcher"],
            "researcher_nlg_reports": ["admin", "researcher"],
            "researcher_raw_sensor_export": ["admin", "researcher"],
            "researcher_trips_export": ["admin", "researcher"],
            "researcher_aggregate_snapshot": ["admin", "researcher"],
            "researcher_ingestion_status": ["admin", "researcher"],
            "behaviour_metrics": ["admin", "researcher", "fleet_manager", "insurance_partner"],
            "fleet_monitoring": ["admin", "fleet_manager"],
            "fleet_assignments": ["admin", "fleet_manager"],
            "fleet_events": ["admin", "fleet_manager"],
            "fleet_trip_context": ["admin", "fleet_manager"],
            "fleet_reports": ["admin", "fleet_manager"],
            "insurance_telematics": ["admin", "insurance_partner"],
            "insurance_reports": ["admin", "insurance_partner"],
            "insurance_raw_sensor_export": ["admin", "insurance_partner"],
            "insurance_alerts": ["admin", "insurance_partner"],
            "insurance_aggregate_reports": ["admin", "insurance_partner"]
        }
    }
    
    setting = AdminSetting(
        key="dataset_access",
        value=json.dumps(default_config),
        description="Dataset access control configuration"
    )
    
    db.add(setting)
    db.commit()
    print("✅ Created default dataset access configuration")


def main():
    print("🌱 Seeding Safe Drive Africa API...")
    print("=" * 60)
    
    db = get_db_session()
    created_clients = []
    
    try:
        # Seed dataset access configuration first
        seed_default_dataset_access(db)
        print()
        
        # Create default API clients
        print("Creating API clients...")
        print("-" * 60)
        
        # 1. Admin client
        admin = create_api_client_with_key(
            db, 
            name="Production Admin", 
            role="admin"
        )
        if admin:
            created_clients.append(admin)
        
        # 2. Researcher client
        researcher = create_api_client_with_key(
            db,
            name="Production Researcher",
            role="researcher"
        )
        if researcher:
            created_clients.append(researcher)
        
        # You can add more default clients here if needed
        # For fleet_manager, driver, insurance_partner - these should be created
        # through the admin API once fleets/drivers/insurers exist
        
        print()
        print("=" * 60)
        print("✅ Seeding complete!")
        print("=" * 60)
        print()
        
        if created_clients:
            print("🔑 API KEYS - SAVE THESE SECURELY!")
            print("=" * 60)
            for client in created_clients:
                print(f"\n📋 {client['name']}")
                print(f"   Role: {client['role']}")
                print(f"   ID: {client['id']}")
                print(f"   API Key: {client['api_key']}")
                if client.get('driverProfileId'):
                    print(f"   Driver Profile ID: {client['driverProfileId']}")
                if client.get('fleet_id'):
                    print(f"   Fleet ID: {client['fleet_id']}")
                if client.get('insurance_partner_id'):
                    print(f"   Insurance Partner ID: {client['insurance_partner_id']}")
            
            print("\n" + "=" * 60)
            print("⚠️  IMPORTANT: Copy these keys now!")
            print("   They will NOT be shown again.")
            print("=" * 60)
            print()
            print("📝 Test the admin key:")
            print(f'   curl -H "X-API-Key: {created_clients[0]["api_key"]}" \\')
            print('        https://api.safedriveafrica.com/api/auth/me')
            print()
        else:
            print("\nℹ️  No new clients created (all already exist)")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
