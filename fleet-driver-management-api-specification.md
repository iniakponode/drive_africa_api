# Fleet Driver Management API Specification

This document specifies the backend API endpoints required to support the fleet driver management system. This system enables fleet managers to onboard drivers into their fleets, manage fleet memberships, and assign drivers to vehicles.

## Overview

### Driver Onboarding Flows

There are **two** ways for drivers to join a fleet:

#### Flow 1: Email-Based Invitation (RECOMMENDED)

This is the primary flow where fleet managers invite specific drivers by email.

```
1. Fleet Manager enters driver's email address
   ↓
2. System creates a DriverInvite record:
   - email: john@gmail.com
   - fleet_id: [fleet manager's fleet]
   - invite_token: ABC123XYZ
   - status: pending
   - vehicle_group_id: (optional pre-assignment)
   ↓
3. System sends email to driver:
   "You've been invited to join ABC Transport Fleet.
    Download the app and register with this email."
   ↓
4. Driver downloads mobile app
5. Driver registers with email + password
   ↓
6. Backend registration logic checks:
   "Is there a pending DriverInvite for this email?"
   - YES → Auto-link driver to fleet
   - Set invite status = "claimed"
   - Create DriverFleetAssignment record
   ↓
7. Driver is now visible in Fleet Manager's driver list
   Fleet Manager can assign vehicle group and vehicle
```

#### Flow 2: Generic Invite Code (Alternative)

For scenarios where fleet manager wants to share a code publicly or with multiple drivers.

```
1. Fleet Manager generates a generic invite code
   ↓
2. Shares code with drivers (verbally, printed, etc.)
   ↓
3. Driver registers in mobile app
4. Driver enters invite code in app
   ↓
5. DriverJoinRequest created with status "pending"
   ↓
6. Fleet Manager reviews and approves/rejects
   ↓
7. Upon approval, DriverFleetAssignment created
```

### Data Scoping Principle

- Fleet managers should **only** see drivers assigned to their fleet
- Insurance partners should **only** see drivers linked to their partner
- Admin users can see all drivers across all fleets

---

## New Database Tables

### Table: `driver_invites` (NEW - Email-based invitations)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| fleet_id | UUID | FOREIGN KEY → fleets.id, NOT NULL | Fleet inviting the driver |
| email | VARCHAR(255) | NOT NULL | Driver's email address |
| invite_token | VARCHAR(64) | UNIQUE, NOT NULL | Unique token for this invitation |
| status | ENUM | 'pending', 'claimed', 'expired', 'cancelled' | Invitation status |
| vehicle_group_id | UUID | FOREIGN KEY → vehicle_groups.id | Pre-assign driver to group |
| created_by | UUID | FOREIGN KEY → user_accounts.id | Fleet manager who created |
| created_at | TIMESTAMP | DEFAULT NOW() | When invitation was created |
| claimed_at | TIMESTAMP | | When driver registered |
| driver_profile_id | UUID | FOREIGN KEY → driver_profiles.id | Set when driver registers |
| expires_at | TIMESTAMP | | Optional expiration |

**Unique constraint:** (fleet_id, email, status='pending') - Only one pending invite per email per fleet

### Table: `fleet_invite_codes` (Generic codes)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| fleet_id | UUID | FOREIGN KEY → fleets.id, NOT NULL | Fleet this code is for |
| code | VARCHAR(32) | UNIQUE, NOT NULL | Human-readable invite code |
| expires_at | TIMESTAMP | | Optional expiration date |
| max_uses | INTEGER | | Max number of uses (null = unlimited) |
| use_count | INTEGER | DEFAULT 0 | Current number of uses |
| created_by | UUID | FOREIGN KEY → user_accounts.id | User who created the code |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| revoked_at | TIMESTAMP | | When code was revoked (null = active) |

### Table: `driver_join_requests`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| fleet_id | UUID | FOREIGN KEY → fleets.id, NOT NULL | Fleet being requested |
| driver_profile_id | UUID | FOREIGN KEY → driver_profiles.id, NOT NULL | Driver requesting |
| invite_code_id | UUID | FOREIGN KEY → fleet_invite_codes.id | Invite code used (if any) |
| status | ENUM | 'pending', 'approved', 'rejected' | Request status |
| requested_at | TIMESTAMP | DEFAULT NOW() | When request was made |
| reviewed_at | TIMESTAMP | | When request was reviewed |
| reviewed_by | UUID | FOREIGN KEY → user_accounts.id | User who reviewed |
| rejection_reason | TEXT | | Optional reason for rejection |

### Table: `driver_fleet_assignments`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| fleet_id | UUID | FOREIGN KEY → fleets.id, NOT NULL | Fleet |
| driver_profile_id | UUID | FOREIGN KEY → driver_profiles.id, NOT NULL, UNIQUE | Driver (can only be in one fleet) |
| vehicle_group_id | UUID | FOREIGN KEY → vehicle_groups.id | Optional vehicle group assignment |
| onboarding_completed | BOOLEAN | DEFAULT FALSE | Has driver completed onboarding |
| compliance_note | TEXT | | Notes about driver compliance |
| assigned_at | TIMESTAMP | DEFAULT NOW() | When driver was assigned |
| assigned_by | UUID | FOREIGN KEY → user_accounts.id | User who assigned |

---

## API Endpoints

### Fleet Invite Codes

#### GET /api/fleet/{fleet_id}/invite-codes

List all invite codes for a fleet.

**Authorization:** Fleet manager of this fleet, or admin

**Response:**
```json
{
  "invite_codes": [
    {
      "id": "uuid",
      "fleet_id": "uuid",
      "code": "FLEET-ABC123",
      "expires_at": "2024-12-31T23:59:59Z",
      "max_uses": 50,
      "use_count": 12,
      "created_at": "2024-01-15T10:30:00Z",
      "is_active": true
    }
  ]
}
```

#### POST /api/fleet/{fleet_id}/invite-codes

Create a new invite code for a fleet.

**Authorization:** Fleet manager of this fleet, or admin

**Request Body:**
```json
{
  "expires_at": "2024-12-31T23:59:59Z",
  "max_uses": 50
}
```

**Response:** Created invite code object

#### DELETE /api/fleet/{fleet_id}/invite-codes/{code_id}

Revoke an invite code.

**Authorization:** Fleet manager of this fleet, or admin

**Response:** 204 No Content

---

### Driver Email Invitations (PRIMARY METHOD)

#### GET /api/fleet/{fleet_id}/driver-invites

List driver invitations for a fleet.

**Authorization:** Fleet manager of this fleet, or admin

**Query Parameters:**
- `status`: Filter by status (pending, claimed, expired, cancelled)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 25)

**Response:**
```json
{
  "invites": [
    {
      "id": "uuid",
      "fleet_id": "uuid",
      "email": "john@gmail.com",
      "status": "pending",
      "invite_token": "ABC123XYZ",
      "vehicle_group_id": "uuid",
      "created_by": "uuid",
      "created_at": "2024-01-15T10:00:00Z",
      "claimed_at": null,
      "driver_profile_id": null,
      "expires_at": null
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 25
}
```

#### GET /api/fleet/my/driver-invites

**Scoped endpoint** - automatically filters to the authenticated fleet manager's fleet.

Same response format as above.

**Authorization:** Fleet manager (fleet_id derived from auth token)

#### POST /api/fleet/{fleet_id}/driver-invites

Invite a driver by email. This creates a pending invitation and optionally sends an email.

**Authorization:** Fleet manager of this fleet, or admin

**Request Body:**
```json
{
  "email": "john@gmail.com",
  "vehicle_group_id": "uuid",         // Optional: pre-assign to vehicle group
  "expires_at": "2024-02-15T23:59:59Z", // Optional: expiration
  "send_email": true                   // Whether to send invitation email
}
```

**Response:**
```json
{
  "id": "uuid",
  "fleet_id": "uuid",
  "email": "john@gmail.com",
  "status": "pending",
  "invite_token": "ABC123XYZ",
  "vehicle_group_id": "uuid",
  "created_at": "2024-01-15T10:00:00Z"
}
```

**Error Responses:**
- 400: Invalid email format
- 409: Active invitation already exists for this email

#### POST /api/fleet/my/driver-invites

**Scoped endpoint** - for fleet managers to invite to their own fleet.

Same request/response as above.

#### POST /api/fleet/{fleet_id}/driver-invites/{invite_id}/resend

Resend the invitation email.

**Authorization:** Fleet manager of this fleet, or admin

**Response:**
```json
{
  "message": "Invitation email resent to john@gmail.com"
}
```

#### DELETE /api/fleet/{fleet_id}/driver-invites/{invite_id}

Cancel a pending invitation.

**Authorization:** Fleet manager of this fleet, or admin

**Response:** 204 No Content

---

### Driver Join Requests (Alternative Flow)

#### GET /api/fleet/{fleet_id}/join-requests

List pending join requests for a fleet.

**Authorization:** Fleet manager of this fleet, or admin

**Query Parameters:**
- `status`: Filter by status (pending, approved, rejected)

**Response:**
```json
{
  "requests": [
    {
      "id": "uuid",
      "fleet_id": "uuid",
      "driver_profile_id": "uuid",
      "driver_email": "driver@example.com",
      "driver_name": "John Doe",
      "invite_code_used": "FLEET-ABC123",
      "status": "pending",
      "requested_at": "2024-01-20T14:00:00Z"
    }
  ]
}
```

#### POST /api/fleet/{fleet_id}/join-requests/{request_id}/approve

Approve a join request and create the fleet assignment.

**Authorization:** Fleet manager of this fleet, or admin

**Request Body:**
```json
{
  "vehicle_group_id": "uuid"
}
```

**Response:**
```json
{
  "message": "Driver approved and assigned to fleet",
  "assignment_id": "uuid"
}
```

#### POST /api/fleet/{fleet_id}/join-requests/{request_id}/reject

Reject a join request.

**Authorization:** Fleet manager of this fleet, or admin

**Request Body:**
```json
{
  "reason": "Insufficient documentation"
}
```

**Response:** 204 No Content

---

### Fleet Drivers

#### GET /api/fleet/{fleet_id}/drivers

List all drivers assigned to a fleet.

**Authorization:** Fleet manager of this fleet, or admin

**Query Parameters:**
- `search`: Search by name or email
- `vehicle_group_id`: Filter by vehicle group
- `has_vehicle`: Filter by vehicle assignment status (true/false)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 25)

**Response:**
```json
{
  "drivers": [
    {
      "driverProfileId": "uuid",
      "email": "driver@example.com",
      "name": "John Doe",
      "phone": "+1234567890",
      "assignment": {
        "id": "uuid",
        "vehicle_group_id": "uuid",
        "vehicle_group_name": "Downtown Team",
        "onboarding_completed": true,
        "assigned_at": "2024-01-15T10:00:00Z"
      },
      "vehicle": {
        "id": "uuid",
        "license_plate": "ABC-123",
        "make": "Toyota",
        "model": "Hilux"
      },
      "safety_score": 85.5,
      "total_trips": 142,
      "last_active": "2024-01-25T16:30:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 25
}
```

#### GET /api/fleet/my/drivers

**Scoped endpoint** - automatically filters to the authenticated fleet manager's fleet.

Same response format as above.

**Authorization:** Fleet manager (fleet_id derived from auth token)

#### POST /api/fleet/{fleet_id}/drivers

Manually add a driver to a fleet (admin only, or for drivers without invite code).

**Authorization:** Admin only

**Request Body:**
```json
{
  "driver_profile_id": "uuid",
  "vehicle_group_id": "uuid"
}
```

#### PUT /api/fleet/{fleet_id}/drivers/{driver_profile_id}

Update a driver's fleet assignment.

**Authorization:** Fleet manager of this fleet, or admin

**Request Body:**
```json
{
  "vehicle_group_id": "uuid",
  "onboarding_completed": true,
  "compliance_note": "All documents verified"
}
```

#### DELETE /api/fleet/{fleet_id}/drivers/{driver_profile_id}

Remove a driver from a fleet.

**Authorization:** Fleet manager of this fleet, or admin

**Response:** 204 No Content

---

### Admin Driver Search

#### GET /api/admin/drivers/unassigned

Search for drivers not assigned to any fleet.

**Authorization:** Admin only

**Query Parameters:**
- `search`: Search by email or name

**Response:**
```json
{
  "drivers": [
    {
      "driverProfileId": "uuid",
      "email": "newdriver@example.com",
      "name": "Jane Smith",
      "created_at": "2024-01-20T09:00:00Z"
    }
  ]
}
```

---

### Mobile App Endpoints

These endpoints are called from the driver mobile app.

#### POST /api/auth/register (Modified)

**IMPORTANT:** The driver registration endpoint must be modified to check for pending email invitations.

**Current Flow:**
```
1. Driver submits email + password
2. Create user account
3. Create driver profile
4. Return JWT token
```

**New Flow (with email invitation check):**
```
1. Driver submits email + password
2. Create user account
3. Create driver profile
4. CHECK: Is there a pending DriverInvite for this email?
   - YES:
     a. Update DriverInvite: status = 'claimed', claimed_at = now(), driver_profile_id = new_id
     b. Create DriverFleetAssignment record
     c. If vehicle_group_id was set on invite, assign to that group
   - NO: Continue normally (driver is not pre-assigned to a fleet)
5. Return JWT token (include fleet info if assigned)
```

**Backend Implementation:**
```python
def register_driver(email: str, password: str) -> Dict:
    # Create user and driver profile
    user = create_user(email, password, role='driver')
    driver_profile = create_driver_profile(user.id)
    
    # Check for pending email invitation
    pending_invite = db.query(DriverInvite).filter(
        DriverInvite.email == email.lower(),
        DriverInvite.status == 'pending'
    ).first()
    
    if pending_invite:
        # Claim the invitation
        pending_invite.status = 'claimed'
        pending_invite.claimed_at = datetime.utcnow()
        pending_invite.driver_profile_id = driver_profile.id
        
        # Create fleet assignment
        assignment = DriverFleetAssignment(
            fleet_id=pending_invite.fleet_id,
            driver_profile_id=driver_profile.id,
            vehicle_group_id=pending_invite.vehicle_group_id,
            assigned_by=pending_invite.created_by
        )
        db.add(assignment)
        db.commit()
    
    return generate_jwt(user, driver_profile, assignment)
```

#### POST /api/driver/join-fleet

Submit a request to join a fleet using an invite code (alternative flow).

**Authorization:** Authenticated driver (JWT)

**Request Body:**
```json
{
  "invite_code": "FLEET-ABC123"
}
```

**Response:**
```json
{
  "message": "Join request submitted",
  "request_id": "uuid",
  "fleet_name": "ABC Transport"
}
```

**Error Responses:**
- 400: Invalid or expired invite code
- 409: Already member of a fleet or pending request exists

#### GET /api/driver/fleet-status

Get the driver's current fleet membership status.

**Authorization:** Authenticated driver (JWT)

**Response (Assigned):**
```json
{
  "status": "assigned",
  "fleet": {
    "id": "uuid",
    "name": "ABC Transport"
  },
  "vehicle_group": {
    "id": "uuid",
    "name": "Downtown Team"
  },
  "vehicle": {
    "id": "uuid",
    "license_plate": "ABC-123",
    "make": "Toyota",
    "model": "Hilux"
  },
  "pending_request": null
}
```

**Response (Pending):**
```json
{
  "status": "pending",
  "fleet": null,
  "vehicle_group": null,
  "vehicle": null,
  "pending_request": {
    "id": "uuid",
    "fleet_name": "ABC Transport",
    "requested_at": "2024-01-20T14:00:00Z"
  }
}
```

**Response (Not in Fleet):**
```json
{
  "status": "none",
  "fleet": null,
  "vehicle_group": null,
  "vehicle": null,
  "pending_request": null
}
```

#### DELETE /api/driver/join-request

Cancel the driver's pending join request.

**Authorization:** Authenticated driver (JWT)

**Response:** 204 No Content

**Error Responses:**
- 404: No pending join request found

#### POST /api/auth/login (Modified)

**IMPORTANT:** The login endpoint should return fleet status alongside user info.

**Request:**
```json
{
  "email": "john@gmail.com",
  "password": "..."
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "john@gmail.com",
    "role": "driver"
  },
  "driver_profile": {
    "id": "uuid",
    "email": "john@gmail.com",
    "name": "John Doe"
  },
  "fleet_status": {
    "status": "assigned",
    "fleet": {
      "id": "uuid",
      "name": "ABC Transport"
    },
    "vehicle_group": {
      "id": "uuid",
      "name": "Downtown Team"
    },
    "vehicle": {
      "id": "uuid",
      "license_plate": "ABC-123"
    },
    "pending_request": null
  }
}
```

---

## Invite Code Generation

### Code Format

Recommended format: `{FLEET_PREFIX}-{RANDOM}`

- **FLEET_PREFIX**: 3-4 uppercase letters from fleet name
- **RANDOM**: 6 alphanumeric uppercase characters

Examples:
- `ABCT-X7K2M9` (ABC Transport)
- `CIT-A3B8C2` (City Logistics)

### Generation Algorithm

```python
import secrets
import string

def generate_invite_code(fleet_name: str) -> str:
    # Extract prefix from fleet name (first 3-4 alphabetic chars)
    prefix = ''.join(c.upper() for c in fleet_name if c.isalpha())[:4]
    if len(prefix) < 3:
        prefix = prefix.ljust(3, 'X')
    
    # Generate random suffix
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(secrets.choice(chars) for _ in range(6))
    
    return f"{prefix}-{suffix}"
```

---

## Data Scoping Rules

### Fleet Manager Scope

When a fleet manager makes API calls:

1. **Automatic filtering**: All queries should be automatically filtered to their fleet
2. **Validation**: Any create/update operations should validate the resource belongs to their fleet
3. **Forbidden resources**: Return 403 if trying to access another fleet's resources

```python
# Example middleware/decorator
def fleet_manager_scope(func):
    def wrapper(request, *args, **kwargs):
        if request.user.role == 'fleet_manager':
            kwargs['fleet_id'] = request.user.fleet_id
        return func(request, *args, **kwargs)
    return wrapper
```

### Insurance Partner Scope

Insurance partners need visibility into drivers for their linked fleets:

1. Create `insurance_partner_fleets` table linking partners to fleets
2. Query drivers through this relationship
3. Separate endpoints: `/api/insurance/my/drivers`

---

## Invite Code Generation

Suggested algorithm for generating human-readable invite codes:

```python
import secrets
import string

def generate_invite_code(fleet_name: str) -> str:
    prefix = ''.join(c.upper() for c in fleet_name[:4] if c.isalpha())
    suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"{prefix}-{suffix}"

# Example: "ABC Transport" → "ABCT-X7K2M9"
```

---

## Error Handling

### HTTP Status Codes

| Status Code | Scenario |
|-------------|----------|
| 400 | Invalid invite code, expired code, or validation error |
| 403 | Trying to access resource from another fleet |
| 404 | Resource not found |
| 409 | Driver already in a fleet, or pending request exists |

### Error Response Format

All error responses should follow this format for consistent mobile app handling:

```json
{
  "error": {
    "code": "INVALID_CODE",
    "message": "This invite code is invalid or has been revoked."
  }
}
```

### Error Codes for Mobile App

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_CODE` | 400 | Invite code does not exist or is invalid |
| `EXPIRED_CODE` | 400 | Invite code has passed its expiration date |
| `CODE_LIMIT_REACHED` | 400 | Invite code has reached max_uses limit |
| `INVALID_EMAIL` | 400 | Email format is invalid |
| `ALREADY_IN_FLEET` | 409 | Driver is already a member of a fleet |
| `PENDING_REQUEST` | 409 | Driver already has a pending join request |
| `NOT_IN_FLEET` | 404 | Driver is not a member of any fleet |
| `NO_PENDING_REQUEST` | 404 | No pending join request to cancel |
| `FLEET_NOT_FOUND` | 404 | Fleet does not exist |
| `UNAUTHORIZED_FLEET` | 403 | User cannot access this fleet's resources |

---

## Implementation Priority

1. **Phase 1**: Email invitations and auto-assignment on registration
2. **Phase 2**: Fleet invite codes and join requests (alternative flow)
3. **Phase 3**: Fleet drivers list with scoping
4. **Phase 4**: Driver vehicle assignments
5. **Phase 5**: Push notifications for status changes

---

## Questions for Backend Team

1. Should a driver be able to belong to multiple fleets, or is it strictly one fleet per driver?
2. What happens to trip data when a driver leaves a fleet?
3. Should invite codes be case-sensitive?
4. Is there a need for bulk driver import from CSV?
5. Should there be an "invited" status before the driver creates their profile?
