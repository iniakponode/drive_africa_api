# Fleet Driver Management - Web Client Integration Fixes

**Date:** January 15, 2026
**Status:** URGENT - Production Issues

## Issues Identified

### 1. Route Ordering Problem
**Error:** `/api/fleet/my/driver-invites` returns UUID parsing error on "my"

**Root Cause:** FastAPI matches routes in definition order. The parameterized route `/fleet/{fleet_id}/driver-invites` is defined BEFORE the specific route `/fleet/my/driver-invites`, so it catches the request first and tries to parse "my" as a UUID.

**Solution:** Move ALL `/fleet/my/...` routes to the TOP of the file, before any `/fleet/{fleet_id}/...` routes.

**Affected Routes:**
- `GET /fleet/my/driver-invites` (line 163)
- `POST /fleet/my/driver-invites` (line 244)
- `GET /fleet/my/drivers` (line 577)

### 2. Missing Scoped Endpoints
The web client expects these scoped endpoints that don't exist yet:

#### Missing: GET /api/fleet/my/invite-codes
**Current:** Only `/api/fleet/{fleet_id}/invite-codes` exists
**Needed:** Scoped version for fleet managers

#### Missing: POST /api/fleet/my/invite-codes
**Current:** Only `/api/fleet/{fleet_id}/invite-codes` exists
**Needed:** Scoped version for fleet managers

### 3. Page Size Validation Issue
**Error:** `/api/vehicles?page_size=200` returns "Input should be less than or equal to 100"

**Status:** This is working as designed (max 100), but web client is requesting 200.

**Solution:** Web client needs to be updated to request `page_size=100` maximum, or make multiple requests.

## Required Changes

### File: safedrive/api/v1/endpoints/fleet_driver.py

#### Step 1: Add Missing Scoped Endpoints (at the TOP, before line 22)

```python
# --- Scoped Endpoints for Fleet Managers (MUST BE FIRST) ---

@router.get(
    "/fleet/my/invite-codes",
    response_model=schemas.FleetInviteCodeListResponse,
    summary="List my fleet's invite codes",
)
def list_my_fleet_invite_codes(
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.FLEET_MANAGER)),
):
    """
    List all invite codes for the authenticated fleet manager's fleet.
    
    **Authorization:** Fleet manager only
    """
    if not current_client.fleet_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fleet manager must be assigned to a fleet",
        )
    
    invite_codes = crud.crud_fleet_invite_code.get_by_fleet(db, fleet_id=current_client.fleet_id)
    return {"invite_codes": invite_codes}


@router.post(
    "/fleet/my/invite-codes",
    response_model=schemas.FleetInviteCodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invite code for my fleet",
)
def create_my_fleet_invite_code(
    payload: schemas.FleetInviteCodeCreate,
    db: Session = Depends(get_db),
    current_client: ApiClient = Depends(require_roles(Role.FLEET_MANAGER)),
):
    """
    Create an invite code for the authenticated fleet manager's fleet.
    
    **Authorization:** Fleet manager only
    """
    if not current_client.fleet_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fleet manager must be assigned to a fleet",
        )
    
    # Check if fleet exists
    fleet = db.query(Fleet).filter(Fleet.id == current_client.fleet_id).first()
    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")
    
    # Create invite code using fleet manager's fleet_id
    invite_code = crud.crud_fleet_invite_code.create(
        db,
        fleet_id=current_client.fleet_id,
        created_by=current_client.id,
        expires_at=payload.expires_at,
        max_uses=payload.max_uses,
    )
    
    return invite_code
```

#### Step 2: Move Existing "/fleet/my/" Routes to Top

Move these three endpoint functions to appear RIGHT AFTER the two new endpoints above:

1. `GET /fleet/my/driver-invites` (currently line 163)
2. `POST /fleet/my/driver-invites` (currently line 244)
3. `GET /fleet/my/drivers` (currently line 577)

#### Step 3: Verify Route Order

After reorganization, the file should have this structure:

```
Line ~20:  GET  /fleet/my/invite-codes        [NEW]
Line ~50:  POST /fleet/my/invite-codes        [NEW]
Line ~100: GET  /fleet/my/driver-invites      [MOVED]
Line ~150: POST /fleet/my/driver-invites      [MOVED]
Line ~200: GET  /fleet/my/drivers             [MOVED]
Line ~250: GET  /fleet/{fleet_id}/invite-codes     [EXISTING]
Line ~280: POST /fleet/{fleet_id}/invite-codes     [EXISTING]
Line ~310: DELETE /fleet/{fleet_id}/invite-codes/{code_id} [EXISTING]
Line ~350: GET  /fleet/{fleet_id}/driver-invites   [EXISTING]
...rest of parameterized routes...
```

## Testing After Fix

### Test 1: Fleet Manager Invite Codes
```powershell
# Get fleet manager's API key
$fleetManagerKey = "61aef403-f12a-4da1-86d0-84089fa98589_API_KEY"

# List my invite codes
Invoke-RestMethod -Uri "https://api.safedriveafrica.com/api/fleet/my/invite-codes" `
  -Headers @{"X-API-Key"=$fleetManagerKey} `
  -Method Get

# Create my invite code
Invoke-RestMethod -Uri "https://api.safedriveafrica.com/api/fleet/my/invite-codes" `
  -Headers @{"X-API-Key"=$fleetManagerKey} `
  -Method Post `
  -Body (@{max_uses=10} | ConvertTo-Json) `
  -ContentType "application/json"
```

### Test 2: Fleet Manager Driver Invites
```powershell
# List my driver invites
Invoke-RestMethod -Uri "https://api.safedriveafrica.com/api/fleet/my/driver-invites" `
  -Headers @{"X-API-Key"=$fleetManagerKey} `
  -Method Get

# Create driver invite
Invoke-RestMethod -Uri "https://api.safedriveafrica.com/api/fleet/my/driver-invites" `
  -Headers @{"X-API-Key"=$fleetManagerKey} `
  -Method Post `
  -Body (@{email="driver@example.com"} | ConvertTo-Json) `
  -ContentType "application/json"
```

### Test 3: Fleet Manager Drivers
```powershell
# List my fleet drivers
Invoke-RestMethod -Uri "https://api.safedriveafrica.com/api/fleet/my/drivers?page=1&page_size=25" `
  -Headers @{"X-API-Key"=$fleetManagerKey} `
  -Method Get
```

## Web Client Updates Needed

### 1. Update Vehicle API page_size
**File:** Web client vehicle fetching code
**Change:** `page_size=200` → `page_size=100`

```javascript
// BEFORE
const response = await fetch(`/api/vehicles?fleet_id=${fleetId}&status=active&page=1&page_size=200`)

// AFTER
const response = await fetch(`/api/vehicles?fleet_id=${fleetId}&status=active&page=1&page_size=100`)
```

### 2. Verify Endpoint URLs
All fleet manager endpoints should use `/fleet/my/...` pattern:

| Endpoint | Status |
|----------|--------|
| `GET /api/fleet/my/invite-codes` | ✅ Will work after fix |
| `POST /api/fleet/my/invite-codes` | ✅ Will work after fix |
| `GET /api/fleet/my/driver-invites` | ✅ Will work after fix |
| `POST /api/fleet/my/driver-invites` | ✅ Will work after fix |
| `GET /api/fleet/my/drivers` | ✅ Will work after fix |

## Deployment Steps

1. **Backup current code**
   ```bash
   git add safedrive/api/v1/endpoints/fleet_driver.py
   git commit -m "Backup: Before fleet driver route reordering"
   ```

2. **Make changes**
   - Add two new scoped endpoints at top
   - Move three existing "my" routes to top
   - Verify order

3. **Test locally**
   ```bash
   # Start local server
   uvicorn main:app --reload
   
   # Test endpoints
   curl http://localhost:8000/api/fleet/my/invite-codes -H "X-API-Key: test_key"
   ```

4. **Deploy to production**
   ```bash
   git add safedrive/api/v1/endpoints/fleet_driver.py
   git commit -m "Fix: Reorder fleet driver routes and add missing scoped endpoints"
   git push origin main
   ```
   
   - Pull in Plesk
   - Restart service: `sudo systemctl restart safedriveapi-prod`

5. **Verify production**
   - Test all `/api/fleet/my/...` endpoints
   - Verify no UUID parsing errors
   - Check web client loads correctly

## Priority

**CRITICAL** - Web client is currently broken for fleet managers. This needs immediate deployment.

## Estimated Time

- Code changes: 30 minutes
- Testing: 15 minutes  
- Deployment: 10 minutes
- **Total: ~1 hour**
