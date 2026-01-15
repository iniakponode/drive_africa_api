# User Management API Specification

**Version:** 1.0  
**Date:** January 15, 2026  
**Status:** Draft - For Backend Implementation

---

## Overview

This specification defines the API endpoints required to support the new Admin User Management system in the Drive Africa Data Hub frontend. The system enables administrators to:

- Browse and search users across all roles
- Filter users by role, fleet, or insurance partner
- Click through to view associated data for any user
- See fleet manager assignments on fleets

---

## Table of Contents

1. [Data Models](#data-models)
2. [API Endpoints](#api-endpoints)
3. [Database Schema](#database-schema)
4. [Authentication & Authorization](#authentication--authorization)
5. [Error Handling](#error-handling)
6. [Migration Strategy](#migration-strategy)

---

## Data Models

### UserAccount

Represents a user account in the system (any role).

```typescript
interface UserAccount {
  id: string                          // UUID - Primary key
  email: string                       // User's email address
  name?: string | null                // Optional display name
  role: Role                          // User's role in the system
  active: boolean                     // Whether the account is active
  
  // Role-specific associations (nullable based on role)
  fleet_id?: string | null            // For fleet_manager: their assigned fleet
  fleet?: Fleet | null                // Expanded fleet object (optional)
  insurance_partner_id?: string | null // For insurance_partner: their partner org
  insurance_partner?: InsurancePartner | null // Expanded partner object (optional)
  driver_profile_id?: string | null   // For driver: their driver profile ID
  
  created_at: string                  // ISO 8601 timestamp
  last_login_at?: string | null       // ISO 8601 timestamp of last login
}
```

### Role Enum

```typescript
type Role = 
  | 'admin'
  | 'driver'
  | 'researcher'
  | 'fleet_manager'
  | 'insurance_partner'
```

### UserAccountListResponse

Paginated response for user listings.

```typescript
interface UserAccountListResponse {
  users: UserAccount[]
  total: number                       // Total count matching filters
  page: number                        // Current page (1-indexed)
  page_size: number                   // Items per page
}
```

---

## API Endpoints

### 1. List Users

Retrieves a paginated, filterable list of user accounts.

**Endpoint:** `GET /api/admin/users`

**Authentication:** Required (Admin API key or JWT)

**Authorization:** `admin` role only

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 25, max: 100) |
| `role` | string | No | Filter by role (e.g., `fleet_manager`, `driver`) |
| `search` | string | No | Search term for email, name, or ID (case-insensitive) |
| `fleet_id` | string | No | Filter by associated fleet (UUID) |
| `insurance_partner_id` | string | No | Filter by associated insurance partner (UUID) |
| `active` | boolean | No | Filter by active status |

**Example Request:**
```http
GET /api/admin/users?role=fleet_manager&search=john&page=1&page_size=25
X-API-Key: <admin_api_key>
```

**Example Response (200 OK):**
```json
{
  "users": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "email": "john.manager@fleet.com",
      "name": "John Manager",
      "role": "fleet_manager",
      "active": true,
      "fleet_id": "f1234567-89ab-cdef-0123-456789abcdef",
      "fleet": {
        "id": "f1234567-89ab-cdef-0123-456789abcdef",
        "name": "Nairobi Fleet",
        "description": "Central Nairobi operations",
        "region": "Nairobi",
        "created_at": "2025-06-15T10:30:00Z"
      },
      "insurance_partner_id": null,
      "insurance_partner": null,
      "driver_profile_id": null,
      "created_at": "2025-06-15T10:30:00Z",
      "last_login_at": "2026-01-14T08:45:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 25
}
```

**Search Behavior:**

The `search` parameter should perform a case-insensitive search across:
- `email` (partial match)
- `name` (partial match)
- `id` (exact or prefix match)

Recommended implementation using PostgreSQL:
```sql
WHERE (
  email ILIKE '%' || :search || '%'
  OR name ILIKE '%' || :search || '%'
  OR id::text ILIKE :search || '%'
)
```

---

### 2. Get Single User

Retrieves a single user account by ID.

**Endpoint:** `GET /api/admin/users/{user_id}`

**Authentication:** Required (Admin API key or JWT)

**Authorization:** `admin` role only

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string (UUID) | Yes | The user's ID |

**Example Request:**
```http
GET /api/admin/users/a1b2c3d4-e5f6-7890-abcd-ef1234567890
X-API-Key: <admin_api_key>
```

**Example Response (200 OK):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "john.manager@fleet.com",
  "name": "John Manager",
  "role": "fleet_manager",
  "active": true,
  "fleet_id": "f1234567-89ab-cdef-0123-456789abcdef",
  "fleet": {
    "id": "f1234567-89ab-cdef-0123-456789abcdef",
    "name": "Nairobi Fleet",
    "description": "Central Nairobi operations",
    "region": "Nairobi",
    "created_at": "2025-06-15T10:30:00Z"
  },
  "insurance_partner_id": null,
  "insurance_partner": null,
  "driver_profile_id": null,
  "created_at": "2025-06-15T10:30:00Z",
  "last_login_at": "2026-01-14T08:45:00Z"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | User not found |

---

### 3. Create User (Optional Enhancement)

Creates a new user account.

**Endpoint:** `POST /api/admin/users`

**Authentication:** Required (Admin API key or JWT)

**Authorization:** `admin` role only

**Request Body:**
```json
{
  "email": "new.user@example.com",
  "name": "New User",
  "role": "fleet_manager",
  "active": true,
  "fleet_id": "f1234567-89ab-cdef-0123-456789abcdef",
  "password": "initial_password_or_null_for_invite"
}
```

**Response (201 Created):**
```json
{
  "id": "new-uuid-here",
  "email": "new.user@example.com",
  "name": "New User",
  "role": "fleet_manager",
  "active": true,
  "fleet_id": "f1234567-89ab-cdef-0123-456789abcdef",
  "fleet": { ... },
  "created_at": "2026-01-15T12:00:00Z",
  "last_login_at": null
}
```

---

### 4. Update User (Optional Enhancement)

Updates an existing user account.

**Endpoint:** `PATCH /api/admin/users/{user_id}`

**Authentication:** Required (Admin API key or JWT)

**Authorization:** `admin` role only

**Request Body (all fields optional):**
```json
{
  "name": "Updated Name",
  "role": "fleet_manager",
  "active": false,
  "fleet_id": "new-fleet-id",
  "insurance_partner_id": null
}
```

**Response (200 OK):** Returns the updated UserAccount object.

---

### 5. Deactivate User (Optional Enhancement)

Soft-deletes a user by setting `active = false`.

**Endpoint:** `DELETE /api/admin/users/{user_id}`

**Authentication:** Required (Admin API key or JWT)

**Authorization:** `admin` role only

**Response (200 OK):**
```json
{
  "message": "User deactivated successfully",
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## Database Schema

### Users Table

If you don't already have a unified users table, create one:

```sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'driver', 'researcher', 'fleet_manager', 'insurance_partner')),
    active BOOLEAN NOT NULL DEFAULT true,
    
    -- Role-specific foreign keys (nullable)
    fleet_id UUID REFERENCES fleets(id) ON DELETE SET NULL,
    insurance_partner_id UUID REFERENCES insurance_partners(id) ON DELETE SET NULL,
    driver_profile_id VARCHAR(255), -- References driver_profiles.driverProfileId
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes for common queries
    CONSTRAINT valid_role_association CHECK (
        (role = 'fleet_manager' AND fleet_id IS NOT NULL) OR
        (role = 'insurance_partner' AND insurance_partner_id IS NOT NULL) OR
        (role = 'driver' AND driver_profile_id IS NOT NULL) OR
        (role IN ('admin', 'researcher'))
    )
);

-- Indexes for performance
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_fleet_id ON users(fleet_id);
CREATE INDEX idx_users_insurance_partner_id ON users(insurance_partner_id);
CREATE INDEX idx_users_active ON users(active);
CREATE INDEX idx_users_search ON users USING gin(to_tsvector('english', email || ' ' || COALESCE(name, '')));
```

### Relationship to Existing Tables

Ensure proper foreign key relationships exist:

```sql
-- If api_clients table exists and is being used for authentication
-- Consider migrating to a unified users table or maintaining both

-- Fleet managers should reference fleets
ALTER TABLE users 
ADD CONSTRAINT fk_users_fleet 
FOREIGN KEY (fleet_id) REFERENCES fleets(id);

-- Insurance partner users should reference insurance_partners
ALTER TABLE users 
ADD CONSTRAINT fk_users_insurance_partner 
FOREIGN KEY (insurance_partner_id) REFERENCES insurance_partners(id);
```

---

## Authentication & Authorization

### Required Headers

All endpoints require one of:

```http
X-API-Key: <admin_api_key>
```
or
```http
Authorization: Bearer <jwt_token>
```

### Authorization Rules

| Endpoint | Allowed Roles |
|----------|---------------|
| `GET /api/admin/users` | `admin` |
| `GET /api/admin/users/{id}` | `admin` |
| `POST /api/admin/users` | `admin` |
| `PATCH /api/admin/users/{id}` | `admin` |
| `DELETE /api/admin/users/{id}` | `admin` |

### Implementation Notes

```python
# Example Python/FastAPI authorization check
@router.get("/api/admin/users")
async def list_users(
    current_user: User = Depends(get_current_user),
    # ... other params
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    # ... implementation
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### Error Codes

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | `INVALID_REQUEST` | Malformed request or invalid parameters |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Email already exists |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 500 | `INTERNAL_ERROR` | Server error |

### Validation Rules

| Field | Rule |
|-------|------|
| `email` | Valid email format, unique |
| `role` | Must be one of allowed values |
| `page` | Integer >= 1 |
| `page_size` | Integer 1-100 |
| `fleet_id` | Valid UUID, must exist if provided |
| `insurance_partner_id` | Valid UUID, must exist if provided |

---

## Migration Strategy

### If Using api_clients Table for Users

If the current system uses `api_clients` as the user table, you have two options:

#### Option A: Add fields to api_clients

```sql
-- Add missing fields to existing table
ALTER TABLE api_clients ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE api_clients ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;

-- Create view for unified access
CREATE VIEW users_view AS
SELECT 
    id,
    COALESCE(email, name || '@generated.local') as email,
    name,
    role,
    active,
    fleet_id,
    insurance_partner_id,
    "driverProfileId" as driver_profile_id,
    created_at,
    NULL::timestamp as last_login_at
FROM api_clients;
```

#### Option B: Create separate users table

```sql
-- Create new users table
CREATE TABLE users ( ... ); -- As defined above

-- Migrate existing data
INSERT INTO users (id, email, name, role, active, fleet_id, insurance_partner_id, driver_profile_id, created_at)
SELECT 
    id,
    COALESCE(email, name || '@migrated.local'),
    name,
    role,
    active,
    fleet_id,
    insurance_partner_id,
    "driverProfileId",
    created_at
FROM api_clients
WHERE role IN ('admin', 'fleet_manager', 'insurance_partner', 'researcher');
```

---

## Integration with Existing Endpoints

### Fleet Managers in Fleet List

The frontend now expects fleet manager information when listing fleets. Update the `/api/fleet/` endpoint response or create a separate endpoint.

**Option 1: Enhance existing endpoint**

Update `GET /api/fleet/` to optionally include managers:

```http
GET /api/fleet/?include_managers=true
```

**Response:**
```json
[
  {
    "id": "f1234567-89ab-cdef-0123-456789abcdef",
    "name": "Nairobi Fleet",
    "description": "Central operations",
    "region": "Nairobi",
    "created_at": "2025-06-15T10:30:00Z",
    "managers": [
      {
        "id": "user-uuid",
        "email": "manager@fleet.com",
        "name": "Fleet Manager"
      }
    ]
  }
]
```

**Option 2: Frontend fetches separately (current implementation)**

The frontend currently fetches fleet managers via `GET /api/admin/users?role=fleet_manager` and maps them to fleets client-side. This works but requires an extra API call.

---

## Testing Checklist

### Unit Tests

- [ ] List users with no filters returns all users
- [ ] List users with role filter returns correct subset
- [ ] List users with search returns matching users
- [ ] List users with fleet_id filter returns correct users
- [ ] List users with insurance_partner_id filter returns correct users
- [ ] List users with combined filters works correctly
- [ ] Pagination works correctly (page, page_size, total)
- [ ] Get single user returns correct data
- [ ] Get non-existent user returns 404
- [ ] Non-admin users receive 403

### Integration Tests

- [ ] Search by partial email matches
- [ ] Search by partial name matches
- [ ] Search by ID prefix matches
- [ ] Fleet and InsurancePartner objects are properly expanded
- [ ] Large result sets are paginated correctly

### Performance Tests

- [ ] List users with 10,000+ records completes < 500ms
- [ ] Search with 10,000+ records completes < 500ms
- [ ] Concurrent requests handled properly

---

## Appendix: Frontend API Usage

### TypeScript API Functions (for reference)

```typescript
// src/lib/api.ts

export type UserListParams = {
  role?: Role
  search?: string
  fleet_id?: string
  insurance_partner_id?: string
  active?: boolean
  page?: number
  page_size?: number
}

export function getUsers(
  apiKey: string,
  params: UserListParams = {},
): Promise<UserAccountListResponse> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<UserAccountListResponse>(`/api/admin/users${suffix}`, apiKey)
}

export function getUser(apiKey: string, userId: string): Promise<UserAccount> {
  return apiFetch<UserAccount>(`/api/admin/users/${userId}`, apiKey)
}

export function getUsersByRole(
  apiKey: string,
  role: Role,
  params: Omit<UserListParams, 'role'> = {},
): Promise<UserAccountListResponse> {
  return getUsers(apiKey, { ...params, role })
}

export function getFleetManagers(
  apiKey: string,
  params: Omit<UserListParams, 'role'> = {},
): Promise<UserAccountListResponse> {
  return getUsersByRole(apiKey, 'fleet_manager', params)
}

export function searchUsers(
  apiKey: string,
  searchTerm: string,
  params: Omit<UserListParams, 'search'> = {},
): Promise<UserAccountListResponse> {
  return getUsers(apiKey, { ...params, search: searchTerm })
}
```

---

## Contact

For questions about this specification, contact the frontend team or refer to:
- Frontend source: `src/pages/admin/AdminUsers.tsx`
- API client: `src/lib/api.ts`
- Types: `src/lib/types.ts`
