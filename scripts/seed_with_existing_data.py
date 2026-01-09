#!/usr/bin/env python3
"""
Advanced seeding script for Safe Drive Africa API
Seeds API clients with relationships to existing fleets, drivers, and insurers.

This script queries existing data in the database and creates appropriate API clients.

Usage:
    python scripts/seed_with_existing_data.py
"""
import os
import sys
import secrets
from uuid import uuid4, UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from safedrive.core.security import hash_api_key
from safedrive.models.auth import ApiClient


def get_db_session():
    """Create database session from environment variable."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_client_if_not_exists(db, name: str, role: str, **kwargs):
    """Create API client if it doesn't exist."""
    existing = db.query(ApiClient).filter(ApiClient.name == name).first()
    if existing:
        return None
    
    raw_key = secrets.token_urlsafe(32)
    client = ApiClient(
        id=uuid4(),
        name=name,
        role=role,
        active=True,
        api_key_hash=hash_api_key(raw_key),
        **kwargs
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


def main():
    print("🌱 Seeding API Keys with Existing Data...")
    print("=" * 70)
    
    db = get_db_session()
    created_clients = []
    
    try:
        # 1. Create admin client
        print("\n1️⃣  Creating Admin client...")
        admin = create_client_if_not_exists(db, "Admin", "admin")
        if admin:
            created_clients.append(admin)
            print("   ✅ Created")
        else:
            print("   ⚠️  Already exists")
        
        # 2. Create researcher client
        print("\n2️⃣  Creating Researcher client...")
        researcher = create_client_if_not_exists(db, "Researcher", "researcher")
        if researcher:
            created_clients.append(researcher)
            print("   ✅ Created")
        else:
            print("   ⚠️  Already exists")
        
        # 3. Get existing fleets and create fleet manager clients
        print("\n3️⃣  Checking for existing fleets...")
        fleets = db.execute(text("SELECT id, name FROM fleet LIMIT 5")).fetchall()
        
        if fleets:
            print(f"   Found {len(fleets)} fleet(s)")
            for fleet in fleets:
                fleet_id = fleet[0] if isinstance(fleet[0], str) else str(UUID(bytes=fleet[0]))
                fleet_name = fleet[1]
                
                client = create_client_if_not_exists(
                    db,
                    f"Fleet Manager - {fleet_name}",
                    "fleet_manager",
                    fleet_id=UUID(fleet_id)
                )
                if client:
                    created_clients.append(client)
                    print(f"   ✅ Created fleet manager for: {fleet_name}")
        else:
            print("   ℹ️  No fleets found")
        
        # 4. Get existing insurance partners
        print("\n4️⃣  Checking for existing insurance partners...")
        insurers = db.execute(text("SELECT id, name FROM insurance_partner WHERE active = 1 LIMIT 5")).fetchall()
        
        if insurers:
            print(f"   Found {len(insurers)} insurance partner(s)")
            for insurer in insurers:
                insurer_id = insurer[0] if isinstance(insurer[0], str) else str(UUID(bytes=insurer[0]))
                insurer_name = insurer[1]
                
                client = create_client_if_not_exists(
                    db,
                    f"Insurance - {insurer_name}",
                    "insurance_partner",
                    insurance_partner_id=UUID(insurer_id)
                )
                if client:
                    created_clients.append(client)
                    print(f"   ✅ Created insurance partner client for: {insurer_name}")
        else:
            print("   ℹ️  No insurance partners found")
        
        # 5. Get a few driver profiles for testing
        print("\n5️⃣  Checking for existing driver profiles...")
        try:
            # Try different column name variations
            try:
                drivers = db.execute(text("""
                    SELECT driverProfileId, firstName, lastName 
                    FROM driver_profile 
                    LIMIT 3
                """)).fetchall()
            except Exception:
                # Try with different column names if camelCase doesn't work
                try:
                    drivers = db.execute(text("""
                        SELECT driverProfileId, first_name, last_name 
                        FROM driver_profile 
                        LIMIT 3
                    """)).fetchall()
                except Exception:
                    # If both fail, just get driverProfileId
                    drivers = db.execute(text("""
                        SELECT driverProfileId 
                        FROM driver_profile 
                        LIMIT 3
                    """)).fetchall()
            
            if drivers:
                print(f"   Found {len(drivers)} driver(s)")
                for idx, driver in enumerate(drivers):
                    driver_id = driver[0] if isinstance(driver[0], str) else str(UUID(bytes=driver[0]))
                    
                    # Try to get name if columns exist
                    if len(driver) >= 3:
                        first_name = driver[1] or "Driver"
                        last_name = driver[2] or ""
                        driver_name = f"{first_name} {last_name}".strip()
                    else:
                        driver_name = f"Driver {idx + 1}"
                    
                    client = create_client_if_not_exists(
                        db,
                        f"Driver - {driver_name}",
                        "driver",
                        driverProfileId=UUID(driver_id)
                    )
                    if client:
                        created_clients.append(client)
                        print(f"   ✅ Created driver client for: {driver_name}")
            else:
                print("   ℹ️  No driver profiles found")
        except Exception as e:
            print(f"   ⚠️  Could not retrieve driver profiles: {str(e)}")
            print("   Skipping driver client creation...")
        
        print("\n" + "=" * 70)
        print("✅ Seeding complete!")
        print("=" * 70)
        
        if created_clients:
            print("\n🔑 API KEYS - SAVE THESE SECURELY!")
            print("=" * 70)
            
            for client in created_clients:
                print(f"\n📋 {client['name']}")
                print(f"   Role: {client['role']}")
                print(f"   ID: {client['id']}")
                print(f"   🔑 API Key: {client['api_key']}")
                
                if client.get('driverProfileId'):
                    print(f"   👤 Driver Profile: {client['driverProfileId']}")
                if client.get('fleet_id'):
                    print(f"   🚗 Fleet: {client['fleet_id']}")
                if client.get('insurance_partner_id'):
                    print(f"   🏢 Insurance Partner: {client['insurance_partner_id']}")
            
            print("\n" + "=" * 70)
            print("⚠️  COPY THESE KEYS NOW - They won't be shown again!")
            print("=" * 70)
            
            # Save to file for reference
            output_file = "api_keys_GENERATED.txt"
            with open(output_file, "w") as f:
                f.write("Safe Drive Africa API - Generated Keys\n")
                f.write("=" * 70 + "\n")
                f.write("Generated: " + str(__import__('datetime').datetime.now()) + "\n")
                f.write("⚠️  DELETE THIS FILE AFTER COPYING KEYS\n")
                f.write("=" * 70 + "\n\n")
                
                for client in created_clients:
                    f.write(f"Name: {client['name']}\n")
                    f.write(f"Role: {client['role']}\n")
                    f.write(f"API Key: {client['api_key']}\n")
                    if client.get('driverProfileId'):
                        f.write(f"Driver Profile: {client['driverProfileId']}\n")
                    if client.get('fleet_id'):
                        f.write(f"Fleet: {client['fleet_id']}\n")
                    if client.get('insurance_partner_id'):
                        f.write(f"Insurance Partner: {client['insurance_partner_id']}\n")
                    f.write("\n")
            
            print(f"\n💾 Keys also saved to: {output_file}")
            print("   ⚠️  Remember to DELETE this file after copying the keys!\n")
            
            # Test command
            admin_key = next((c['api_key'] for c in created_clients if c['role'] == 'admin'), None)
            if admin_key:
                print("\n📝 Test the admin key:")
                print(f'   curl -H "X-API-Key: {admin_key}" \\')
                print('        https://api.safedriveafrica.com/api/auth/me')
                print()
        else:
            print("\nℹ️  No new clients created (all already exist)")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
