# JWT Authentication Implementation Summary

## Overview
Successfully implemented **Option 2**: Allow either API key or JWT in dependencies (make X-API-Key optional and accept JWT when present).

## Changes Made

### 1. Core Security Module (`safedrive/core/security.py`)
- ✅ Added `get_current_client_or_driver()` function that accepts **either** API Key **or** JWT token
- ✅ Added `require_roles_or_jwt()` dependency factory for endpoints that support both auth methods
- ✅ JWT token extracts driver info and creates `ApiClientContext` with driver role

### 2. Router Configuration (`safedrive/api/v1/api_router.py`)
Updated router-level dependencies to accept JWT for all driver-accessible routers:

| Router | Old Dependency | New Dependency | Status |
|--------|---------------|----------------|--------|
| **trips** | `require_roles_or_jwt` | `require_roles_or_jwt` | ✅ Already updated |
| **raw_sensor_data** | `require_roles_or_jwt` | `require_roles_or_jwt` | ✅ Already updated |
| **unsafe_behaviour** | `require_roles_or_jwt` | `require_roles_or_jwt` | ✅ Already updated |
| **driver_profile** | `require_roles_or_jwt` | `require_roles_or_jwt` | ✅ Already updated |
| **driver_sync** | `require_roles_or_jwt` | `require_roles_or_jwt` | ✅ Already updated |
| **driving_tips** | `require_roles_or_jwt` | `require_roles_or_jwt` | ✅ Already updated |
| **nlg_report** | `require_roles_or_jwt` | `require_roles_or_jwt` | ✅ Already updated |
| **report_statistics** | `require_roles_or_jwt` | `require_roles_or_jwt` | ✅ Already updated |
| **ai_model_inputs** | `require_roles_or_jwt` | `require_roles_or_jwt` | ✅ Already updated |
| **location** | `require_roles_or_jwt` | `require_roles_or_jwt` | ✅ Already updated |
| **alcohol_questionnaire** | `require_roles_or_jwt` | `require_roles_or_jwt` | ✅ Already updated |
| **analytics** | `require_roles` (API only) | `require_roles_or_jwt` | ✅ **FIXED** |
| **config** | `require_roles` (API only) | `require_roles_or_jwt` | ✅ **FIXED** |
| **auth** | `get_current_client` (API only) | No dependency | ✅ **FIXED** |
| **index** | `get_current_client` (API only) | No dependency | ✅ **FIXED** |

### 3. Individual Endpoints Updated

#### Analytics Endpoints (`safedrive/api/v1/endpoints/analytics.py`)
All four analytics endpoints now accept JWT:
- ✅ `GET /api/analytics/leaderboard`
- ✅ `GET /api/analytics/driver-ubpk`
- ✅ `GET /api/analytics/bad-days`
- ✅ `GET /api/analytics/driver-kpis`

#### Auth Endpoint (`safedrive/api/v1/endpoints/auth.py`)
- ✅ `GET /api/auth/me` - Now accepts JWT or API key via `get_current_client_or_driver`

### 4. Authentication Flow

#### Mobile App (JWT) Flow
```
1. Driver registers/logs in → Receives JWT token
2. Mobile app includes: Authorization: Bearer <token>
3. Backend accepts JWT, extracts driver ID
4. Returns driver-scoped data
```

#### Admin/Research Tools (API Key) Flow
```
1. Admin/researcher has API key
2. Tools include: X-API-Key: <key>
3. Backend accepts API key
4. Returns role-scoped data
```

#### Both Work Simultaneously
```
Mobile drivers: JWT only (no X-API-Key required)
Admin users: API key (X-API-Key header)
Backward compatible: Both methods work on same endpoints
```

## Authentication Architecture

### Security Function Hierarchy

```
get_current_client()              → Requires X-API-Key header (API key only)
    ↓
get_current_client_or_driver()    → Accepts X-API-Key OR Authorization: Bearer
    ↓
require_roles(*roles)             → Wraps get_current_client() + role check
    ↓
require_roles_or_jwt(*roles)      → Wraps get_current_client_or_driver() + role check
```

### When to Use Each

| Function | Use Case | Auth Methods |
|----------|----------|-------------|
| `get_current_client()` | Admin-only endpoints | API Key only |
| `get_current_client_or_driver()` | Driver + admin endpoints | JWT or API Key |
| `require_roles()` | Admin-only with specific roles | API Key only |
| `require_roles_or_jwt()` | Driver + admin with specific roles | JWT or API Key |

## Testing

All 22 tests pass:
```bash
DATABASE_URL=sqlite:///:memory: python -m pytest -v
======================== 22 passed, 159 warnings in 7.33s =========================
```

## Deployment Steps

1. **Pull latest code:**
   ```bash
   cd /path/to/drive_africa_api
   git pull origin main
   ```

2. **Clear Python bytecode cache:**
   ```bash
   find . -type d -name __pycache__ -exec rm -rf {} +
   find . -type f -name "*.pyc" -delete
   ```

3. **Restart service:**
   ```bash
   sudo systemctl restart safedrive-api
   # or
   sudo systemctl restart gunicorn
   ```

4. **Verify in Swagger:**
   - Visit `https://api.safedriveafrica.com/docs`
   - Check `/api/analytics/leaderboard` endpoint
   - Should show **both** auth options:
     - `X-API-Key` (security, optional)
     - `HTTPBearer` (Authorization header, optional)

## Mobile App Required Changes

### ✅ Already Implemented (No Changes Needed)
If your mobile app already includes `Authorization: Bearer <token>` header, **no changes required**!

### ❌ If Still Sending X-API-Key
Remove these lines:
```kotlin
// REMOVE THIS
.addHeader("X-API-Key", apiKey)
```

Keep only:
```kotlin
// KEEP THIS
.addHeader("Authorization", "Bearer $jwtToken")
```

## Expected Behavior After Deployment

### Before Fix
```http
POST /api/raw_sensor_data/batch_create
Authorization: Bearer eyJ...

Response: 422 Unprocessable Entity
{
  "detail": [{
    "type": "missing",
    "loc": ["header", "X-API-Key"],
    "msg": "Field required"
  }]
}
```

### After Fix
```http
POST /api/raw_sensor_data/batch_create
Authorization: Bearer eyJ...

Response: 201 Created
{
  "message": "5 RawSensorData records created."
}
```

## Verification Checklist

After deploying, verify these endpoints accept JWT-only requests:

- [ ] `POST /api/trips/`
- [ ] `POST /api/raw_sensor_data/batch_create`
- [ ] `POST /api/unsafe_behaviours/batch_create`
- [ ] `GET /api/analytics/leaderboard`
- [ ] `GET /api/analytics/driver-ubpk`
- [ ] `GET /api/auth/me`
- [ ] `GET /api/config/cloud-endpoints`

## Rollback Plan

If issues arise, revert to requiring API keys:
```bash
git revert HEAD~3
sudo systemctl restart safedrive-api
```

## Benefits of This Approach

✅ **Backward Compatible**: Existing API key users (admin, researchers) unaffected
✅ **Mobile-Friendly**: Drivers use JWT tokens (no API key management)
✅ **Secure**: Both methods validated, JWT includes expiration
✅ **Flexible**: Can add more auth methods in future without breaking changes
✅ **Tested**: All 22 existing tests still pass

## Alternative Approach (Not Chosen)

### Option 1: Split Routers
- ❌ More complex routing
- ❌ Duplicate endpoint code
- ❌ Harder to maintain
- ❌ Less flexible for future changes

### Why Option 2 is Better
- ✅ Single endpoint serves both auth methods
- ✅ Less code duplication
- ✅ Easier to add new auth methods
- ✅ Cleaner FastAPI dependency structure
