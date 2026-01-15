# Fleet Driver Management - Client Integration Guide

**Date:** January 15, 2026  
**Version:** 1.0  
**Target Audience:** Web Client & Mobile App Developers

## Overview

This document provides integration details for the Fleet Driver Management system, including new endpoints for invite codes, driver invitations, and fleet driver management. These features enable fleet managers to invite and manage drivers through both web and mobile applications.

---

## Base URL

**Production:** `https://api.safedriveafrica.com/api`

---

## Authentication

All endpoints require authentication via API Key or JWT token:

### Web Client (Fleet Manager Dashboard)
```http
X-API-Key: <fleet_manager_api_key>
```

### Mobile App (Driver)
```http
Authorization: Bearer <jwt_token>
```

---

## Important Route Changes

### FastAPI Route Ordering Fix

**Issue Resolved:** Previously, `/fleet/my/*` endpoints returned 422 errors because FastAPI was matching the parameterized route `/fleet/{fleet_id}/*` first, trying to parse "my" as a UUID.

**Solution:** All `/fleet/my/*` routes now appear before parameterized routes in the code, ensuring correct route matching.

**Impact:** 
- ✅ `/fleet/my/invite-codes` - Now works correctly
- ✅ `/fleet/my/driver-invites` - Now works correctly
- ✅ `/fleet/my/drivers` - Now works correctly

---

## Fleet Invite Codes

Fleet invite codes allow drivers to self-register and join a fleet without direct email invitation. These codes can be shared via SMS, posters, or other channels.

### 1. List My Fleet Invite Codes

**Endpoint:** `GET /fleet/my/invite-codes`  
**Authorization:** Fleet Manager  
**Use Case:** Web client - Display list of active invite codes

**Request:**
```http
GET /api/fleet/my/invite-codes
X-API-Key: your_fleet_manager_key
```

**Response:**
```json
{
  "invite_codes": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "code": "BAYE-7EOBSF",
      "fleet_id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
      "created_by": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "created_at": "2026-01-15T10:00:00Z",
      "expires_at": "2026-02-15T10:00:00Z",
      "max_uses": 100,
      "current_uses": 23,
      "is_active": true
    }
  ]
}
```

**Web Client Implementation:**
```typescript
async function fetchMyInviteCodes() {
  const response = await fetch(`${API_BASE}/fleet/my/invite-codes`, {
    headers: {
      'X-API-Key': userApiKey,
    },
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch invite codes');
  }
  
  return await response.json();
}
```

---

### 2. Create Fleet Invite Code

**Endpoint:** `POST /fleet/my/invite-codes`  
**Authorization:** Fleet Manager  
**Use Case:** Web client - Generate new invite code for driver recruitment

**Request:**
```http
POST /api/fleet/my/invite-codes
X-API-Key: your_fleet_manager_key
Content-Type: application/json

{
  "expires_at": "2026-03-15T23:59:59Z",
  "max_uses": 50
}
```

**Response:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "code": "BAYE-ABC123",
  "fleet_id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
  "created_by": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-01-15T10:00:00Z",
  "expires_at": "2026-03-15T23:59:59Z",
  "max_uses": 50,
  "current_uses": 0,
  "is_active": true
}
```

**Web Client Implementation:**
```typescript
async function createInviteCode(data: { expires_at: string; max_uses: number }) {
  const response = await fetch(`${API_BASE}/fleet/my/invite-codes`, {
    method: 'POST',
    headers: {
      'X-API-Key': userApiKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    throw new Error('Failed to create invite code');
  }
  
  return await response.json();
}
```

---

### 3. Validate Invite Code (Mobile App)

**Endpoint:** `POST /driver-join/validate-code`  
**Authorization:** None (Public endpoint)  
**Use Case:** Mobile app - Validate code before driver registration

**Request:**
```http
POST /api/driver-join/validate-code
Content-Type: application/json

{
  "code": "BAYE-7EOBSF"
}
```

**Response:**
```json
{
  "valid": true,
  "fleet_id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
  "fleet_name": "Bayelsa State Transport Company",
  "message": "Code is valid"
}
```

**Mobile App Implementation (React Native):**
```typescript
async function validateInviteCode(code: string) {
  const response = await fetch(`${API_BASE}/driver-join/validate-code`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ code }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Invalid code');
  }
  
  return await response.json();
}
```

---

### 4. Join Fleet with Code (Mobile App)

**Endpoint:** `POST /driver-join/join-with-code`  
**Authorization:** Driver JWT  
**Use Case:** Mobile app - Driver joins fleet using invite code

**Request:**
```http
POST /api/driver-join/join-with-code
Authorization: Bearer <driver_jwt_token>
Content-Type: application/json

{
  "code": "BAYE-7EOBSF"
}
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "fleet_id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
  "driver_profile_id": "d1e2f3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6a",
  "vehicle_group_id": null,
  "assigned_at": "2026-01-15T12:30:00Z",
  "assigned_by": null,
  "onboarding_completed": false
}
```

**Mobile App Implementation (React Native):**
```typescript
async function joinFleetWithCode(code: string, authToken: string) {
  const response = await fetch(`${API_BASE}/driver-join/join-with-code`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ code }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to join fleet');
  }
  
  return await response.json();
}
```

---

## Driver Invitations (Email-Based)

Email invitations allow fleet managers to directly invite specific drivers by email address.

### 5. List My Driver Invitations

**Endpoint:** `GET /fleet/my/driver-invites`  
**Authorization:** Fleet Manager  
**Use Case:** Web client - Display pending/accepted driver invitations

**Request:**
```http
GET /api/fleet/my/driver-invites?status=pending&page=1&page_size=25
X-API-Key: your_fleet_manager_key
```

**Query Parameters:**
- `status` (optional): Filter by status (`pending`, `accepted`, `expired`)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (max: 100, default: 25)

**Response:**
```json
{
  "invites": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "fleet_id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
      "email": "driver@example.com",
      "token": "inv_abc123xyz789",
      "status": "pending",
      "created_by": "f1g2h3i4-j5k6-7l8m-9n0o-p1q2r3s4t5u6",
      "created_at": "2026-01-15T10:00:00Z",
      "expires_at": "2026-02-15T10:00:00Z",
      "accepted_at": null,
      "vehicle_group_id": "v1w2x3y4-z5a6-7b8c-9d0e-f1g2h3i4j5k6"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 25
}
```

**Web Client Implementation:**
```typescript
async function fetchMyDriverInvites(status?: string, page = 1, pageSize = 25) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  
  if (status) {
    params.append('status', status);
  }
  
  const response = await fetch(`${API_BASE}/fleet/my/driver-invites?${params}`, {
    headers: {
      'X-API-Key': userApiKey,
    },
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch driver invites');
  }
  
  return await response.json();
}
```

---

### 6. Create Driver Invitation

**Endpoint:** `POST /fleet/my/driver-invites`  
**Authorization:** Fleet Manager  
**Use Case:** Web client - Send email invitation to specific driver

**Request:**
```http
POST /api/fleet/my/driver-invites
X-API-Key: your_fleet_manager_key
Content-Type: application/json

{
  "email": "newdriver@example.com",
  "vehicle_group_id": "v1w2x3y4-z5a6-7b8c-9d0e-f1g2h3i4j5k6",
  "expires_at": "2026-02-15T23:59:59Z",
  "send_email": true
}
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "fleet_id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
  "email": "newdriver@example.com",
  "token": "inv_def456uvw012",
  "status": "pending",
  "created_by": "f1g2h3i4-j5k6-7l8m-9n0o-p1q2r3s4t5u6",
  "created_at": "2026-01-15T12:00:00Z",
  "expires_at": "2026-02-15T23:59:59Z",
  "accepted_at": null,
  "vehicle_group_id": "v1w2x3y4-z5a6-7b8c-9d0e-f1g2h3i4j5k6"
}
```

**Web Client Implementation:**
```typescript
interface CreateInviteData {
  email: string;
  vehicle_group_id?: string;
  expires_at?: string;
  send_email?: boolean;
}

async function createDriverInvite(data: CreateInviteData) {
  const response = await fetch(`${API_BASE}/fleet/my/driver-invites`, {
    method: 'POST',
    headers: {
      'X-API-Key': userApiKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    throw new Error('Failed to create driver invite');
  }
  
  return await response.json();
}
```

---

### 7. Accept Driver Invitation (Mobile App)

**Endpoint:** `POST /driver-join/accept-invite`  
**Authorization:** Driver JWT  
**Use Case:** Mobile app - Driver accepts email invitation

**Request:**
```http
POST /api/driver-join/accept-invite
Authorization: Bearer <driver_jwt_token>
Content-Type: application/json

{
  "token": "inv_abc123xyz789"
}
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "fleet_id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
  "driver_profile_id": "d1e2f3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6a",
  "vehicle_group_id": "v1w2x3y4-z5a6-7b8c-9d0e-f1g2h3i4j5k6",
  "assigned_at": "2026-01-15T14:00:00Z",
  "assigned_by": "f1g2h3i4-j5k6-7l8m-9n0o-p1q2r3s4t5u6",
  "onboarding_completed": false
}
```

**Mobile App Implementation (React Native):**
```typescript
async function acceptDriverInvite(token: string, authToken: string) {
  const response = await fetch(`${API_BASE}/driver-join/accept-invite`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ token }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to accept invite');
  }
  
  return await response.json();
}
```

---

## Fleet Driver Management

### 8. List My Fleet Drivers

**Endpoint:** `GET /fleet/my/drivers`  
**Authorization:** Fleet Manager  
**Use Case:** Web client - Display all drivers in the fleet manager's fleet

**Request:**
```http
GET /api/fleet/my/drivers?search=john&page=1&page_size=25
X-API-Key: your_fleet_manager_key
```

**Query Parameters:**
- `search` (optional): Search by driver name or email
- `vehicle_group_id` (optional): Filter by vehicle group UUID
- `has_vehicle` (optional): Filter by vehicle assignment status (true/false)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (max: 100, default: 25)

**Response:**
```json
{
  "drivers": [
    {
      "driverProfileId": "d1e2f3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6a",
      "email": "driver@example.com",
      "name": "John Doe",
      "phone": "+2348012345678",
      "assignment": {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "vehicle_group_id": "v1w2x3y4-z5a6-7b8c-9d0e-f1g2h3i4j5k6",
        "vehicle_group_name": "Sedan Fleet",
        "onboarding_completed": true,
        "assigned_at": "2026-01-10T10:00:00Z"
      },
      "vehicle": null,
      "safety_score": 85.5,
      "total_trips": 245,
      "last_active": "2026-01-15T08:30:00Z"
    }
  ],
  "total": 48,
  "page": 1,
  "page_size": 25
}
```

**Web Client Implementation:**
```typescript
interface DriverFilters {
  search?: string;
  vehicle_group_id?: string;
  has_vehicle?: boolean;
  page?: number;
  page_size?: number;
}

async function fetchMyFleetDrivers(filters: DriverFilters = {}) {
  const params = new URLSearchParams({
    page: (filters.page || 1).toString(),
    page_size: (filters.page_size || 25).toString(),
  });
  
  if (filters.search) params.append('search', filters.search);
  if (filters.vehicle_group_id) params.append('vehicle_group_id', filters.vehicle_group_id);
  if (filters.has_vehicle !== undefined) params.append('has_vehicle', filters.has_vehicle.toString());
  
  const response = await fetch(`${API_BASE}/fleet/my/drivers?${params}`, {
    headers: {
      'X-API-Key': userApiKey,
    },
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch fleet drivers');
  }
  
  return await response.json();
}
```

---

## Mobile App Integration Flow

### Driver Registration with Fleet Code

**Step 1:** Driver enters invite code on registration screen
```typescript
const code = await showInviteCodeInput();
const validation = await validateInviteCode(code);

if (validation.valid) {
  // Show fleet name to confirm
  showFleetInfo(validation.fleet_name);
}
```

**Step 2:** Driver completes registration
```typescript
const registrationData = {
  email: driverEmail,
  password: driverPassword,
  name: driverName,
  phone: driverPhone,
};

const authResponse = await registerDriver(registrationData);
const jwt = authResponse.token;
```

**Step 3:** Automatically join fleet with code
```typescript
try {
  const assignment = await joinFleetWithCode(code, jwt);
  
  // Store fleet assignment
  await AsyncStorage.setItem('fleet_id', assignment.fleet_id);
  await AsyncStorage.setItem('assignment_id', assignment.id);
  
  // Navigate to onboarding or main app
  navigation.navigate('Onboarding');
} catch (error) {
  showError('Failed to join fleet. Please contact support.');
}
```

---

### Driver Registration with Email Invite

**Step 1:** Driver receives email with invite link
```
https://app.safedriveafrica.com/join?token=inv_abc123xyz789
```

**Step 2:** Mobile app deep links to accept invite screen
```typescript
// In App.tsx or deep link handler
Linking.addEventListener('url', handleDeepLink);

function handleDeepLink(event: { url: string }) {
  const url = new URL(event.url);
  const token = url.searchParams.get('token');
  
  if (token && token.startsWith('inv_')) {
    navigation.navigate('AcceptInvite', { token });
  }
}
```

**Step 3:** Driver logs in or registers, then accepts invite
```typescript
// After authentication
const jwt = await login(email, password);

try {
  const assignment = await acceptDriverInvite(token, jwt);
  
  await AsyncStorage.setItem('fleet_id', assignment.fleet_id);
  await AsyncStorage.setItem('assignment_id', assignment.id);
  
  navigation.navigate('Onboarding');
} catch (error) {
  showError('Invalid or expired invitation.');
}
```

---

## Web Client Integration Flow

### Fleet Manager Dashboard - Invite Codes Tab

**Display Active Codes:**
```typescript
useEffect(() => {
  async function loadInviteCodes() {
    try {
      const data = await fetchMyInviteCodes();
      setInviteCodes(data.invite_codes);
    } catch (error) {
      showNotification('Error loading invite codes', 'error');
    }
  }
  
  loadInviteCodes();
}, []);
```

**Create New Invite Code:**
```typescript
async function handleCreateCode() {
  const expiresAt = new Date();
  expiresAt.setMonth(expiresAt.getMonth() + 1); // 1 month expiry
  
  try {
    const newCode = await createInviteCode({
      expires_at: expiresAt.toISOString(),
      max_uses: 50,
    });
    
    // Display code for sharing
    showCodeModal(newCode.code);
    
    // Refresh list
    const data = await fetchMyInviteCodes();
    setInviteCodes(data.invite_codes);
  } catch (error) {
    showNotification('Failed to create invite code', 'error');
  }
}
```

---

### Fleet Manager Dashboard - Driver Invitations Tab

**Display Pending Invitations:**
```typescript
const [statusFilter, setStatusFilter] = useState('pending');

useEffect(() => {
  async function loadInvites() {
    try {
      const data = await fetchMyDriverInvites(statusFilter, page, pageSize);
      setInvites(data.invites);
      setTotal(data.total);
    } catch (error) {
      showNotification('Error loading invitations', 'error');
    }
  }
  
  loadInvites();
}, [statusFilter, page, pageSize]);
```

**Send New Invitation:**
```typescript
async function handleInviteDriver(email: string, vehicleGroupId?: string) {
  const expiresAt = new Date();
  expiresAt.setDate(expiresAt.getDate() + 7); // 7 days expiry
  
  try {
    const invite = await createDriverInvite({
      email,
      vehicle_group_id: vehicleGroupId,
      expires_at: expiresAt.toISOString(),
      send_email: true,
    });
    
    showNotification(`Invitation sent to ${email}`, 'success');
    
    // Refresh list
    const data = await fetchMyDriverInvites(statusFilter, page, pageSize);
    setInvites(data.invites);
  } catch (error) {
    showNotification('Failed to send invitation', 'error');
  }
}
```

---

### Fleet Manager Dashboard - Drivers List

**Display All Drivers with Filters:**
```typescript
const [filters, setFilters] = useState<DriverFilters>({
  page: 1,
  page_size: 25,
});

useEffect(() => {
  async function loadDrivers() {
    try {
      const data = await fetchMyFleetDrivers(filters);
      setDrivers(data.drivers);
      setTotal(data.total);
    } catch (error) {
      showNotification('Error loading drivers', 'error');
    }
  }
  
  loadDrivers();
}, [filters]);
```

**Search and Filter:**
```typescript
function handleSearch(searchTerm: string) {
  setFilters(prev => ({
    ...prev,
    search: searchTerm,
    page: 1, // Reset to first page
  }));
}

function handleVehicleGroupFilter(vehicleGroupId: string) {
  setFilters(prev => ({
    ...prev,
    vehicle_group_id: vehicleGroupId,
    page: 1,
  }));
}
```

---

## Error Handling

### Common Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Invalid API key"
}
```
- **Action:** Redirect to login, refresh API key

**403 Forbidden:**
```json
{
  "detail": "Fleet manager must be assigned to a fleet"
}
```
- **Action:** Contact administrator to assign fleet

**404 Not Found:**
```json
{
  "detail": "Fleet not found"
}
```
- **Action:** Verify fleet_id is correct

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```
- **Action:** Display validation errors to user

**400 Bad Request:**
```json
{
  "detail": "Invite code has expired"
}
```
- **Action:** Display error message, request new code

---

## Testing

### Test Data (Production)

**Fleet Manager API Key:**
```
Test Fleet: Bayelsa State Transport Company
API Key: fleet_manager_bayelsa_prod_key_2024
Fleet ID: c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f
```

**Active Invite Code:**
```
Code: BAYE-7EOBSF
Fleet: Bayelsa State Transport Company
Status: Active
Max Uses: 100
Current Uses: 0
Expires: 2026-02-15
```

### Test Scenarios

**Web Client:**
1. ✅ Login as fleet manager
2. ✅ Navigate to invite codes tab
3. ✅ Verify `BAYE-7EOBSF` appears in list
4. ✅ Create new invite code
5. ✅ Navigate to invitations tab
6. ✅ Send invitation to test email
7. ✅ Verify invitation appears as "pending"
8. ✅ Navigate to drivers tab
9. ✅ Search for driver by name
10. ✅ Filter by vehicle group

**Mobile App:**
1. ✅ Enter invite code `BAYE-7EOBSF` on registration
2. ✅ Validate code shows "Bayelsa State Transport Company"
3. ✅ Complete driver registration
4. ✅ Verify fleet assignment successful
5. ✅ Test email invite flow with deep link
6. ✅ Accept invitation after login
7. ✅ Verify fleet assignment appears in profile

---

## Rate Limits

- **Default:** 100 requests per minute per API key
- **Burst:** 20 requests per second

If rate limit exceeded:
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

---

## Support

**Backend API Issues:**
- Repository: https://github.com/iniakponode/drive_africa_api
- Documentation: `/docs/` (see project root)

**Questions:**
- Contact backend team for endpoint clarification
- Check `AGENTS.md` for project overview
- Review `docs/seedings.md` for test data

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-15 | Initial release with route fixes and new endpoints |

---

## Next Steps

### Web Client Team
1. Update API client to use `/fleet/my/*` endpoints
2. Implement invite codes management UI
3. Implement driver invitations management UI
4. Update drivers list with new filters
5. Test all endpoints with production API key

### Mobile App Team
1. Add invite code input to registration flow
2. Implement code validation before registration
3. Add deep link handler for email invites
4. Update driver onboarding to handle fleet assignment
5. Test with production invite code `BAYE-7EOBSF`

---

**Document Status:** ✅ Ready for Implementation  
**Last Updated:** January 15, 2026
