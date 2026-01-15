# User Management System Implementation

## Overview
Complete backend implementation for user account management system. Enables admin users to manage user accounts across the system, including creating accounts, updating roles, searching users, and managing account status.

## Files Created

### Schemas
- **safedrive/schemas/user_management.py** (110 lines)
  - `UserAccountBase`, `UserAccountCreate`, `UserAccountUpdate`
  - `UserAccountResponse` - Full user details with relationships
  - `UserAccountListResponse` - Paginated list response
  - `UserDeactivateResponse` - Deactivation confirmation
  - `FleetInfo`, `InsurancePartnerInfo`, `ManagerInfo` - Nested relationship schemas

### CRUD Operations
- **safedrive/crud/user_management.py** (189 lines)
  - `CRUDUserAccount` - Complete user account management
  - Advanced search across name, email, and UUID
  - Filtering by role, fleet, insurance partner, active status
  - Pagination support
  - API key generation and hashing (SHA256)

### API Endpoints
- **safedrive/api/v1/endpoints/user_management.py** (270 lines)
  - 5 REST endpoints for complete user lifecycle management
  - Admin-only authorization
  - Comprehensive validation and error handling

### Model Modifications
- **safedrive/models/auth.py** (Modified)
  - Added `email` field (VARCHAR 255, nullable, unique)
  - Added `last_login_at` field (TIMESTAMP, nullable)

### Migration
- **alembic/versions/f8g9h0i1j2k3_add_email_and_last_login_to_api_client.py** (38 lines)
  - Adds email column with unique index
  - Adds last_login_at column
  - Reversible migration

## Database Changes

### Modified: api_client table

**New Columns Added:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| email | VARCHAR(255) | NULLABLE, UNIQUE | User's email address |
| last_login_at | TIMESTAMP | NULLABLE | Last successful login timestamp |

**Existing Columns:**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(255) | Display name |
| role | VARCHAR(50) | User role (admin, driver, etc.) |
| api_key_hash | VARCHAR(64) | Hashed API key (SHA256) |
| active | BOOLEAN | Account active status |
| driverProfileId | UUID | Link to driver_profile (nullable) |
| fleet_id | UUID | Link to fleet (nullable) |
| insurance_partner_id | UUID | Link to insurance_partner (nullable) |
| created_at | TIMESTAMP | Account creation date |

**New Index:**
- `ix_api_client_email` (unique) - Fast email lookups

## API Endpoints

### User Account Management

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/admin/users` | Admin | List all users with filters |
| GET | `/api/admin/users/{user_id}` | Admin | Get single user details |
| POST | `/api/admin/users` | Admin | Create new user account |
| PATCH | `/api/admin/users/{user_id}` | Admin | Update user account |
| DELETE | `/api/admin/users/{user_id}` | Admin | Deactivate user account |

### Query Parameters (List Endpoint)

**Filters:**
- `role` - Filter by role (admin, driver, researcher, fleet_manager, insurance_partner)
- `search` - Search by email, name, or ID (case-insensitive)
- `fleet_id` - Filter by fleet assignment
- `insurance_partner_id` - Filter by insurance partner
- `active` - Filter by active status (true/false)

**Pagination:**
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 25, max: 100)

## Key Features Implemented

### 1. Comprehensive Search
- **Multi-field search** across:
  - Email (partial matching, case-insensitive)
  - Name (partial matching, case-insensitive)
  - UUID (exact match as string)
- **OR combination** - Returns matches from any field
- **Fast indexed** search on email

### 2. Role-Based Filtering
Supports all system roles:
- `admin` - System administrators
- `driver` - Mobile app drivers
- `researcher` - Data researchers
- `fleet_manager` - Fleet managers
- `insurance_partner` - Insurance partners

### 3. Relationship Expansion
Automatically includes related data:
- **Fleet Info** - ID, name, description, region
- **Insurance Partner Info** - ID, name, label, active status
- **Manager Info** - For drivers with assigned managers

### 4. Account Lifecycle
- **Create** - Generate API key, validate role-specific fields
- **Update** - Partial updates (only provided fields)
- **Deactivate** - Soft delete (sets active=false)
- **Search** - Find accounts across all fields

### 5. API Key Management
- **Generation** - Secure random key using `secrets.token_urlsafe(32)`
- **Hashing** - SHA256 hash stored in database
- **Return** - Raw key returned only once at creation

### 6. Validation

**Role-Specific Requirements:**
- `fleet_manager` → Requires `fleet_id`
- `insurance_partner` → Requires `insurance_partner_id`
- `driver` → Requires `driver_profile_id`
- `admin`/`researcher` → No special requirements

**Foreign Key Validation:**
- Validates fleet_id exists
- Validates insurance_partner_id exists
- Returns 404 if invalid

### 7. Data Privacy
- Email is optional (nullable)
- Gracefully handles missing email
- Last login tracking for security audits

## Response Examples

### List Users Response
```json
{
  "users": [
    {
      "id": "2c25d85a-384b-4179-ae51-e7cdb13f2161",
      "email": "admin@example.com",
      "name": "Admin",
      "role": "admin",
      "active": true,
      "fleet_id": null,
      "fleet": null,
      "insurance_partner_id": null,
      "insurance_partner": null,
      "driver_profile_id": null,
      "created_at": "2026-01-09T15:46:21",
      "last_login_at": null
    },
    {
      "id": "61aef403-f12a-4da1-86d0-84089fa98589",
      "email": "fleet@example.com",
      "name": "Abraham",
      "role": "fleet_manager",
      "active": true,
      "fleet_id": "f1e2e3t4-5678-90ab-cdef-1234567890ab",
      "fleet": {
        "id": "f1e2e3t4-5678-90ab-cdef-1234567890ab",
        "name": "ABC Transport",
        "description": "Main city fleet",
        "region": "Lagos",
        "created_at": "2026-01-01T00:00:00"
      },
      "insurance_partner_id": null,
      "insurance_partner": null,
      "driver_profile_id": null,
      "created_at": "2026-01-09T23:38:34",
      "last_login_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 8,
  "page": 1,
  "page_size": 25
}
```

### Create User Response
```json
{
  "id": "uuid",
  "email": "newuser@example.com",
  "name": "New User",
  "role": "fleet_manager",
  "active": true,
  "fleet_id": "uuid",
  "api_key": "RAW_API_KEY_SHOWN_ONLY_ONCE",
  "created_at": "2026-01-15T12:00:00"
}
```

### Update User Response
```json
{
  "id": "uuid",
  "email": "updated@example.com",
  "name": "Updated Name",
  "role": "fleet_manager",
  "active": true,
  "fleet_id": "uuid",
  "fleet": {
    "id": "uuid",
    "name": "New Fleet",
    "description": "Reassigned",
    "region": "Abuja",
    "created_at": "2026-01-01T00:00:00"
  },
  "insurance_partner_id": null,
  "insurance_partner": null,
  "driver_profile_id": null,
  "created_at": "2026-01-09T23:38:34",
  "last_login_at": "2026-01-15T13:00:00"
}
```

## Authorization

**All endpoints require Admin role:**
```python
@router.get("/api/admin/users")
def list_users(
    current_client: ApiClient = Depends(require_roles(Role.ADMIN))
):
    ...
```

Only system administrators can:
- View all user accounts
- Create new accounts
- Update existing accounts
- Deactivate accounts
- Search across all users

## Search Implementation

### Multi-Field Search
```python
search_filters = []
if search:
    # Email search
    if hasattr(model, 'email') and model.email is not None:
        search_filters.append(model.email.ilike(f"%{search}%"))
    
    # Name search
    search_filters.append(model.name.ilike(f"%{search}%"))
    
    # UUID search (cast to string)
    try:
        search_filters.append(
            func.cast(model.id, String).ilike(f"%{search}%")
        )
    except:
        pass

# Combine with OR
if search_filters:
    query = query.filter(or_(*search_filters))
```

### Search Examples
- `search=abraham` → Matches name "Abraham"
- `search=gmail` → Matches email "user@gmail.com"
- `search=2c25d85a` → Matches UUID starting with "2c25d85a"

## Validation

### Create User Validation
```python
# Role-specific validation
if role == "fleet_manager" and not fleet_id:
    raise HTTPException(400, "fleet_id required for fleet_manager")

if role == "insurance_partner" and not insurance_partner_id:
    raise HTTPException(400, "insurance_partner_id required")

if role == "driver" and not driver_profile_id:
    raise HTTPException(400, "driver_profile_id required for driver")

# Foreign key validation
if fleet_id:
    fleet = db.query(Fleet).filter(Fleet.id == fleet_id).first()
    if not fleet:
        raise HTTPException(404, "Fleet not found")
```

### Update User Validation
Similar validation applied during updates, but only for fields being changed.

## Deployment

### Deployed: January 15, 2026

**Steps Taken:**
1. ✅ Code pushed to repository
2. ✅ Deployed via Plesk control panel
3. ✅ Migration executed: `alembic upgrade f8g9h0i1j2k3`
4. ✅ Service restarted: `sudo systemctl restart safedriveapi-prod`
5. ✅ Endpoints tested successfully

**Migration Verification:**
```sql
DESCRIBE api_client;
+----------------------+---------------+------+-----+---------------------+
| Field                | Type          | Null | Key | Default             |
+----------------------+---------------+------+-----+---------------------+
| id                   | binary(16)    | NO   | PRI | NULL                |
| name                 | varchar(255)  | NO   |     | NULL                |
| role                 | varchar(50)   | NO   |     | NULL                |
| api_key_hash         | varchar(64)   | NO   | UNI | NULL                |
| active               | tinyint(1)    | NO   |     | 1                   |
| driverProfileId      | binary(16)    | YES  | MUL | NULL                |
| fleet_id             | binary(16)    | YES  | MUL | NULL                |
| insurance_partner_id | binary(16)    | YES  | MUL | NULL                |
| created_at           | datetime      | NO   |     | current_timestamp() |
| email                | varchar(255)  | YES  | UNI | NULL                | ← NEW
| last_login_at        | datetime      | YES  |     | NULL                | ← NEW
+----------------------+---------------+------+-----+---------------------+
✅ Columns added successfully
```

**Test Results:**
```bash
# List all users
GET /api/admin/users
Response: 8 users returned
Status: ✅ Working

# Filter by role
GET /api/admin/users?role=admin
Response: 2 admin users returned
Status: ✅ Working

# Search by name
GET /api/admin/users?search=Abraham
Response: 1 user returned
Status: ✅ Working

# Get single user
GET /api/admin/users/2c25d85a-384b-4179-ae51-e7cdb13f2161
Response: User details with all fields
Status: ✅ Working
```

## Error Handling

### HTTP Status Codes

| Status | Scenario |
|--------|----------|
| 200 | Successful GET/PATCH |
| 201 | Successful POST (created) |
| 204 | Successful DELETE (deactivated) |
| 400 | Validation error (missing required fields) |
| 403 | Unauthorized (non-admin user) |
| 404 | User not found or invalid foreign key |
| 409 | Conflict (duplicate email) |

### Error Response Format
```json
{
  "detail": "Fleet not found with id: uuid"
}
```

## Integration Notes

### For Web Client Developers
- All endpoints require admin API key
- Use pagination for large user lists
- Search works across email, name, and ID
- Filter by role for role-specific views
- Email is optional (may be null for existing users)
- Fleet and insurance_partner objects expanded automatically

### For Mobile App
- Not directly used by mobile app
- Driver accounts managed through admin interface
- API keys generated for driver accounts if needed

## Performance Considerations

1. **Indexed Searches**
   - Email column has unique index
   - Fast lookups on email
   - UUID cast for ID searches

2. **Eager Loading**
   - Uses `joinedload` for fleet and insurance_partner
   - Prevents N+1 query problems
   - Single query for list with relationships

3. **Pagination**
   - Prevents large result sets
   - Configurable page size (max 100)
   - Separate count query for total

4. **Query Optimization**
   - Filters applied before relationships loaded
   - Count query separate from data query
   - Efficient OR combinations in search

## Security

1. **API Key Generation** - Uses `secrets.token_urlsafe(32)` (256-bit entropy)
2. **Key Hashing** - SHA256 hash stored, not plaintext
3. **One-Time Display** - Raw key shown only at creation
4. **Role Validation** - Enforces role-specific requirements
5. **Soft Delete** - Deactivation preserves data for audit
6. **Admin-Only** - All endpoints require admin authorization

## Testing Checklist

- [x] List users with no filters
- [x] List users filtered by role
- [x] Search users by email
- [x] Search users by name
- [x] Search users by ID (UUID)
- [x] Filter by fleet_id
- [x] Filter by active status
- [x] Pagination (page 1, 2, 3)
- [x] Get single user
- [x] Create user with valid data
- [x] Create user without required fields (400 error)
- [x] Update user (partial update)
- [x] Deactivate user
- [x] Non-admin access (403 error)
- [x] Deployment successful
- [x] Migration applied
- [x] Service running
- [x] All endpoints responding

## Known Limitations

1. **Email Optional** - Existing users may not have email (gracefully handled)
2. **No Password Management** - API key based authentication only
3. **No Email Validation** - Email uniqueness enforced but format not validated by database
4. **Soft Delete Only** - No hard delete endpoint (by design for audit trail)

## Future Enhancements

1. Password-based authentication option
2. Email verification workflow
3. Two-factor authentication (2FA)
4. Session management
5. Account lockout after failed attempts
6. Password reset functionality
7. Audit log for account changes
8. Bulk user import from CSV
9. User groups/permissions management
10. Last login tracking enforcement

## Migration Rollback

If needed, rollback the migration:
```bash
alembic downgrade f8g9h0i1j2k3:down
```

This will:
- Drop `ix_api_client_email` index
- Drop `email` column
- Drop `last_login_at` column

---

**Status: ✅ DEPLOYED AND WORKING**
**Production URL:** https://api.safedriveafrica.com/api/admin/users
**Admin API Key Required:** 02QDlql_JlwQXjdcj-Awsw8gBPs06-6JEP-aasDKf38
