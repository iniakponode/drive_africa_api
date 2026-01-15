# Vehicle Management API - Quick Start Guide

## 🚀 Quick Deploy (5 Minutes)

### Step 1: Run Database Migration
```bash
# From project root
cd c:\Users\r02it21\AndroidStudioProjects\drive_africa_api

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run migration
.venv\Scripts\alembic -c alembic.ini upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade d4e5f6a7b8c9 -> e6f7a8b9c0d1, Add vehicle management tables and trip vehicle_id.
```

### Step 2: Restart API Service
```powershell
# If running locally
# Ctrl+C to stop, then restart

# If deployed on production
ssh user@api.safedriveafrica.com "sudo systemctl restart safedriveapi-prod"
```

### Step 3: Verify Tables Created
```bash
# Local MySQL
mysql -u dev2 -pProgressIniks2018 drive_safe_db -e "SHOW TABLES LIKE '%vehicle%';"

# Expected output:
# +---------------------------------+
# | Tables_in_drive_safe_db         |
# +---------------------------------+
# | driver_vehicle_assignment       |
# | vehicle                         |
# | vehicle_group                   |
# +---------------------------------+
```

### Step 4: Test API Endpoint
```bash
curl -X GET "http://localhost:8000/api/vehicles?page=1&page_size=10" \
  -H "X-API-Key: 02QDlql_JlwQXjdcj-Awsw8gBPs06-6JEP-aasDKf38"

# Expected: {"vehicles":[],"total":0,"page":1,"page_size":10}
```

---

## 📝 Quick Test Script

Save as `test_vehicle_api.ps1`:

```powershell
$API_KEY = "02QDlql_JlwQXjdcj-Awsw8gBPs06-6JEP-aasDKf38"
$BASE_URL = "http://localhost:8000/api"

Write-Host "Testing Vehicle API..." -ForegroundColor Green

# 1. List vehicles (should be empty initially)
Write-Host "`n1. List vehicles..." -ForegroundColor Yellow
curl -X GET "$BASE_URL/vehicles" -H "X-API-Key: $API_KEY"

# 2. Create a vehicle
Write-Host "`n2. Create vehicle..." -ForegroundColor Yellow
$createResponse = curl -X POST "$BASE_URL/vehicles" `
  -H "X-API-Key: $API_KEY" `
  -H "Content-Type: application/json" `
  -d '{
    "fleet_id": "YOUR_FLEET_ID_HERE",
    "license_plate": "TEST-001",
    "make": "Toyota",
    "model": "Test Model",
    "year": 2024,
    "vehicle_type": "car"
  }'

Write-Host $createResponse

Write-Host "`nVehicle API tests complete!" -ForegroundColor Green
```

Run with:
```powershell
.\test_vehicle_api.ps1
```

---

## 🔧 Troubleshooting

### Issue: Migration fails with "column already exists"
**Solution:** Column already added in previous run. Safe to ignore or run:
```bash
.venv\Scripts\alembic -c alembic.ini downgrade -1
.venv\Scripts\alembic -c alembic.ini upgrade head
```

### Issue: "Vehicle not found" error
**Cause:** Trying to access vehicle from different fleet as fleet manager.
**Solution:** Admins can access all vehicles, fleet managers only their fleet.

### Issue: "License plate already exists"
**Cause:** Duplicate license plate in request.
**Solution:** License plates must be unique. Check existing vehicles first.

### Issue: API returns 401 Unauthorized
**Cause:** Missing or invalid API key.
**Solution:** Ensure `X-API-Key` header is set correctly.

---

## 📊 Quick API Reference

### List Vehicles
```http
GET /api/vehicles?fleet_id={uuid}&page=1&page_size=25
Headers: X-API-Key: {your-key}
```

### Create Vehicle
```http
POST /api/vehicles
Headers: 
  X-API-Key: {your-key}
  Content-Type: application/json
Body: {
  "fleet_id": "uuid",
  "license_plate": "KAA 123A",
  "make": "Toyota",
  "model": "Hilux",
  "year": 2022
}
```

### Assign Driver
```http
POST /api/vehicles/{vehicle_id}/drivers
Headers: 
  X-API-Key: {your-key}
  Content-Type: application/json
Body: {
  "driver_profile_id": "uuid",
  "is_primary": true
}
```

### Get Vehicle Stats
```http
GET /api/vehicles/{vehicle_id}/stats?period=month
Headers: X-API-Key: {your-key}
```

---

## 🎯 Integration Checklist

- [ ] Database migration completed successfully
- [ ] API service restarted
- [ ] Tables verified in database
- [ ] Test API endpoint responds correctly
- [ ] Frontend can call vehicle endpoints
- [ ] Create vehicle works
- [ ] List vehicles works
- [ ] Driver assignment works
- [ ] Vehicle stats display correctly

---

## 📞 Support

**Documentation:**
- Full API Spec: `docs/vehicle-api-specification.md`
- Implementation: `docs/vehicle-backend-implementation.md`

**Common Scenarios:**
1. **Fleet onboarding:** Use batch create endpoint for multiple vehicles
2. **Driver rotation:** Unassign old driver, assign new driver
3. **Vehicle retirement:** DELETE endpoint sets status to "retired"
4. **Trip assignment:** Mobile app should send vehicle_id when starting trip

**Need Help?**
- Check backend logs: `journalctl -u safedriveapi-prod -n 100`
- Review migration file: `alembic/versions/e6f7a8b9c0d1_add_vehicle_management_tables.py`
- Test with Postman/curl before frontend integration

---

**Ready to go! 🚀**
