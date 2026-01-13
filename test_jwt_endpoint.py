"""
Quick test script to verify JWT authentication works on the production server.
Run this to test if the deployed API accepts JWT tokens.
"""

import requests
import json
from datetime import datetime

# Production API URL
BASE_URL = "https://api.safedriveafrica.com"

# Test credentials from seedings.md
TEST_EMAIL = "driver1@example.com"
TEST_PASSWORD = "password123"

print("=" * 60)
print("Testing JWT Authentication on Production Server")
print("=" * 60)

# Step 1: Try to login, if fails, try to register
print("\n1. Attempting to get JWT token...")
login_url = f"{BASE_URL}/api/auth/driver/login"
register_url = f"{BASE_URL}/api/auth/driver/register"

login_data = {
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD
}

jwt_token = None
driver_id = None

# Try login first
try:
    print("   Trying login...")
    login_response = requests.post(login_url, json=login_data)
    
    if login_response.status_code == 200:
        token_data = login_response.json()
        jwt_token = token_data["access_token"]
        driver_id = token_data["driver_profile_id"]
        print(f"   ✅ Login successful!")
        print(f"   Driver ID: {driver_id}")
        print(f"   Token: {jwt_token[:50]}...")
    elif login_response.status_code == 401:
        # Try to register instead
        print("   Login failed (401), trying registration...")
        import uuid
        register_data = {
            "driverProfileId": str(uuid.uuid4()),
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "sync": False
        }
        register_response = requests.post(register_url, json=register_data)
        
        if register_response.status_code in [200, 201]:
            token_data = register_response.json()
            jwt_token = token_data["access_token"]
            driver_id = token_data["driver_profile_id"]
            print(f"   ✅ Registration successful!")
            print(f"   Driver ID: {driver_id}")
            print(f"   Token: {jwt_token[:50]}...")
        else:
            print(f"   ❌ Registration failed ({register_response.status_code}): {register_response.text}")
            exit(1)
    else:
        print(f"   ❌ Login failed ({login_response.status_code}): {login_response.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Step 2: Test analytics endpoint with JWT only (no X-API-Key)
print("\n2. Testing /api/analytics/leaderboard with JWT only...")
analytics_url = f"{BASE_URL}/api/analytics/leaderboard"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}

try:
    analytics_response = requests.get(
        analytics_url,
        headers=headers,
        params={"period": "week", "limit": 5}
    )
    print(f"   Status: {analytics_response.status_code}")
    
    if analytics_response.status_code == 200:
        print(f"   ✅ Analytics endpoint accepts JWT!")
        data = analytics_response.json()
        print(f"   Total drivers: {data.get('total_drivers', 0)}")
    elif analytics_response.status_code == 422:
        print(f"   ❌ Still getting 422 error (X-API-Key required)")
        print(f"   Response: {analytics_response.text}")
    else:
        print(f"   ⚠️  Unexpected status: {analytics_response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 3: Test raw sensor data endpoint with JWT only
print("\n3. Testing /api/raw_sensor_data/ with JWT only...")
sensor_url = f"{BASE_URL}/api/raw_sensor_data/"

# You'll need a valid trip_id from your database
test_sensor_data = {
    "sensor_type_name": "ACCELEROMETER",
    "timestamp": int(datetime.now().timestamp() * 1000),
    "trip_id": None,  # Replace with actual trip ID if needed
    "sensor_x": 0.1,
    "sensor_y": 0.2,
    "sensor_z": 9.8
}

try:
    sensor_response = requests.post(
        sensor_url,
        headers=headers,
        json=test_sensor_data
    )
    print(f"   Status: {sensor_response.status_code}")
    
    if sensor_response.status_code in [200, 201]:
        print(f"   ✅ Raw sensor endpoint accepts JWT!")
    elif sensor_response.status_code == 422:
        error_data = sensor_response.json()
        if any("X-API-Key" in str(err) for err in error_data.get("detail", [])):
            print(f"   ❌ Still getting 422 error (X-API-Key required)")
            print(f"   Response: {sensor_response.text}")
        else:
            print(f"   ⚠️  422 for different reason: {sensor_response.text}")
    else:
        print(f"   ⚠️  Status {sensor_response.status_code}: {sensor_response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
print("\nIf you see 422 errors about X-API-Key, the server needs:")
print("1. Git pull to get latest code")
print("2. Clear Python bytecode cache (__pycache__)")
print("3. Restart the API service")
