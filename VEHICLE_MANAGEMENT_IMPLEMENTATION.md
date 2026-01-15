# Vehicle Management System Implementation

## Overview
Complete backend implementation for vehicle management system supporting the web client's vehicle management interface. Includes vehicle CRUD operations, vehicle groups, driver-vehicle assignments, and comprehensive filtering/search capabilities.

## Files Created

### Models
- **safedrive/models/vehicle.py** (154 lines)
  - `Vehicle` - Main vehicle entity
  - `VehicleGroup` - Groups for organizing vehicles
  - `DriverVehicleAssignment` - Driver-to-vehicle assignments

### Schemas
- **safedrive/schemas/vehicle.py** (221 lines)
  - `VehicleBase`, `VehicleCreate`, `VehicleUpdate`, `VehicleResponse`
  - `VehicleGroupCreate`, `VehicleGroupUpdate`, `VehicleGroupResponse`
  - `DriverVehicleAssignmentCreate`, `AssignmentResponse`
  - Pagination and list response schemas

### CRUD Operations
- **safedrive/crud/vehicle.py** (389 lines)
  - `CRUDVehicle` - Vehicle management with search and filtering
  - `CRUDVehicleGroup` - Vehicle group management
  - `CRUDDriverVehicleAssignment` - Assignment management
  - Advanced search across license_plate, make, model, VIN

### API Endpoints
- **safedrive/api/v1/endpoints/vehicles.py** (489 lines)
  - 17 REST endpoints for complete vehicle lifecycle management

### Migration
- **alembic/versions/e6f7a8b9c0d1_add_vehicle_management_tables.py** (147 lines)
  - Creates 3 tables with proper foreign keys and indexes
  - Adds vehicle_id to trip table for trip-vehicle association

## Database Tables Created

### 1. vehicle
Main vehicle registry.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| license_plate | VARCHAR(50) | License plate number (unique, indexed) |
| make | VARCHAR(100) | Vehicle manufacturer |
| model | VARCHAR(100) | Vehicle model |
| year | INTEGER | Manufacturing year |
| color | VARCHAR(50) | Vehicle color |
| vin | VARCHAR(100) | Vehicle Identification Number (unique, indexed) |
| status | ENUM | active/maintenance/retired |
| fleet_id | UUID | Fleet ownership (FK → fleet.id) |
| vehicle_group_id | UUID | Optional group assignment (FK → vehicle_group.id) |
| insurance_policy_number | VARCHAR(100) | Insurance policy number |
| insurance_expiry | DATE | Insurance expiration date |
| registration_expiry | DATE | Registration expiration date |
| last_service_date | DATE | Last maintenance date |
| next_service_due | DATE | Next scheduled maintenance |
| odometer_reading | INTEGER | Current odometer reading (km) |
| fuel_type | VARCHAR(50) | Fuel type (petrol, diesel, electric, hybrid) |
| notes | TEXT | Additional notes |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

**Status Values:** active, maintenance, retired

### 2. vehicle_group
Groups for organizing vehicles (e.g., by region, type).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Group name (not null) |
| description | TEXT | Group description |
| fleet_id | UUID | Fleet ownership (FK → fleet.id) |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 3. driver_vehicle_assignment
Assigns drivers to specific vehicles.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| driver_profile_id | UUID | Driver (FK → driver_profile.driverProfileId) |
| vehicle_id | UUID | Vehicle (FK → vehicle.id) |
| assigned_at | TIMESTAMP | Assignment start date |
| assigned_by | UUID | User who made assignment (FK → api_client.id) |
| unassigned_at | TIMESTAMP | Assignment end date (null = active) |

**Constraint:** One driver can only be assigned to one active vehicle at a time

### 4. trip table modification
Added vehicle_id column to existing trip table.

| Column | Type | Description |
|--------|------|-------------|
| vehicle_id | UUID | Vehicle used for trip (FK → vehicle.id, nullable) |

## API Endpoints

### Vehicle Management

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/vehicles` | Fleet Manager/Admin | List all vehicles with filters |
| GET | `/api/fleet/my/vehicles` | Fleet Manager | List my fleet's vehicles |
| GET | `/api/vehicles/{vehicle_id}` | Fleet Manager/Admin | Get single vehicle details |
| POST | `/api/vehicles` | Fleet Manager/Admin | Create new vehicle |
| PUT | `/api/vehicles/{vehicle_id}` | Fleet Manager/Admin | Update vehicle |
| DELETE | `/api/vehicles/{vehicle_id}` | Fleet Manager/Admin | Delete vehicle |

**Query Parameters for List:**
- `search` - Search by license plate, make, model, or VIN
- `status` - Filter by status (active/maintenance/retired)
- `vehicle_group_id` - Filter by vehicle group
- `fleet_id` - Filter by fleet (admin only)
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 10, max: 100)

### Vehicle Groups

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/vehicle-groups` | Fleet Manager/Admin | List vehicle groups |
| GET | `/api/fleet/my/vehicle-groups` | Fleet Manager | List my fleet's groups |
| GET | `/api/vehicle-groups/{group_id}` | Fleet Manager/Admin | Get single group |
| POST | `/api/vehicle-groups` | Fleet Manager/Admin | Create vehicle group |
| PUT | `/api/vehicle-groups/{group_id}` | Fleet Manager/Admin | Update vehicle group |
| DELETE | `/api/vehicle-groups/{group_id}` | Fleet Manager/Admin | Delete vehicle group |

### Driver-Vehicle Assignments

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/vehicles/{vehicle_id}/assign-driver` | Fleet Manager/Admin | Assign driver to vehicle |
| POST | `/api/vehicles/{vehicle_id}/unassign-driver` | Fleet Manager/Admin | Unassign driver from vehicle |
| GET | `/api/vehicles/{vehicle_id}/assignments` | Fleet Manager/Admin | Get assignment history |
| GET | `/api/drivers/{driver_id}/vehicle-assignment` | Fleet Manager/Admin | Get driver's current vehicle |
| GET | `/api/vehicles/{vehicle_id}/current-driver` | Fleet Manager/Admin | Get vehicle's current driver |

## Key Features Implemented

### 1. Fleet Scoping
- Fleet managers automatically scoped to their fleet
- `/fleet/my/` endpoints for convenience
- Validation prevents cross-fleet access
- Admin users can access all fleets

### 2. Advanced Search
- Search across multiple fields: license_plate, make, model, VIN
- Case-insensitive partial matching (ILIKE)
- OR combination of search terms
- Fast indexed searches

### 3. Status Management
- Three status values: active, maintenance, retired
- Status filtering in list endpoints
- Status transitions tracked

### 4. Vehicle Groups
- Organize vehicles by region, type, or custom criteria
- Optional group assignment
- Can filter vehicles by group
- Can reassign vehicles between groups

### 5. Driver Assignment
- One driver = one active vehicle (enforced)
- Assignment history tracking
- Automatic unassignment when reassigning
- Assignment metadata (who, when)

### 6. Maintenance Tracking
- Insurance expiry date
- Registration expiry date
- Last service date
- Next service due date
- Odometer readings

### 7. Data Validation
- Unique constraints on license_plate and VIN
- Required field validation via Pydantic
- Status enum validation
- Foreign key validation

### 8. Pagination
- All list endpoints support pagination
- Configurable page size (max 100)
- Total count in response

## Response Examples

### Vehicle List Response
```json
{
  "vehicles": [
    {
      "id": "uuid",
      "license_plate": "ABC-123",
      "make": "Toyota",
      "model": "Hilux",
      "year": 2023,
      "color": "White",
      "vin": "1HGBH41JXMN109186",
      "status": "active",
      "fleet_id": "uuid",
      "vehicle_group_id": "uuid",
      "vehicle_group_name": "Downtown Fleet",
      "current_driver": {
        "driverProfileId": "uuid",
        "email": "john@example.com",
        "name": "John Doe"
      },
      "insurance_policy_number": "INS-12345",
      "insurance_expiry": "2024-12-31",
      "registration_expiry": "2024-12-31",
      "last_service_date": "2024-01-01",
      "next_service_due": "2024-04-01",
      "odometer_reading": 45000,
      "fuel_type": "diesel",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T00:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 10
}
```

### Assignment Response
```json
{
  "id": "uuid",
  "driver_profile_id": "uuid",
  "driver_email": "john@example.com",
  "driver_name": "John Doe",
  "vehicle_id": "uuid",
  "vehicle_license_plate": "ABC-123",
  "assigned_at": "2024-01-15T10:00:00Z",
  "assigned_by": "uuid",
  "assigned_by_name": "Fleet Manager"
}
```

## Authorization Rules

### Fleet Manager
- Can ONLY manage vehicles in their fleet
- Cannot access other fleets' vehicles
- Returns 403 if attempting cross-fleet access

### Admin
- Can manage vehicles across all fleets
- Can filter by fleet_id
- Full access to all operations

## Indexes Created

Performance-optimized with these indexes:
- `ix_vehicle_license_plate` (unique)
- `ix_vehicle_vin` (unique)
- `ix_vehicle_fleet_id`
- `ix_vehicle_vehicle_group_id`
- `ix_vehicle_status`
- `ix_vehicle_group_fleet_id`
- `ix_driver_vehicle_assignment_driver_profile_id`
- `ix_driver_vehicle_assignment_vehicle_id`

## Deployment

### Deployed: January 15, 2026

**Steps Taken:**
1. ✅ Code pushed to repository
2. ✅ Deployed via Plesk control panel
3. ✅ Migration executed: `alembic upgrade e6f7a8b9c0d1`
4. ✅ Service restarted: `sudo systemctl restart safedriveapi-prod`
5. ✅ Endpoints tested successfully

**Test Results:**
```bash
GET /api/vehicles?page=1&page_size=10
Response: {"vehicles":[],"total":0,"page":1,"page_size":10}
Status: ✅ Working
```

**Database Verification:**
```sql
SHOW TABLES LIKE 'vehicle%';
+----------------------------------+
| vehicle                          |
| vehicle_group                    |
| driver_vehicle_assignment        |
+----------------------------------+
✅ All tables created successfully
```

## Integration Notes

### For Web Client Developers
- Use `/api/fleet/my/vehicles` for fleet manager's vehicle list
- Use search parameter for filtering by license plate, make, model, or VIN
- Vehicle groups can be used for organizing vehicles in UI
- Status values: "active", "maintenance", "retired"
- Pagination required for large fleets

### For Trip Recording
- Trip table now has optional `vehicle_id` field
- Can associate trips with specific vehicles
- Useful for vehicle-specific analytics

## Testing Checklist

- [x] Create vehicle
- [x] List vehicles with pagination
- [x] Search vehicles by license plate
- [x] Filter by status
- [x] Filter by vehicle group
- [x] Update vehicle
- [x] Delete vehicle
- [x] Create vehicle group
- [x] Assign driver to vehicle
- [x] Unassign driver from vehicle
- [x] Get current driver for vehicle
- [x] Get current vehicle for driver
- [x] Fleet manager scoping (403 on cross-fleet access)
- [x] Admin can access all fleets
- [x] Deployment successful
- [x] Service running
- [x] Endpoints responding

## Performance Considerations

1. **Indexed Searches** - Fast lookups on license_plate, VIN, fleet_id
2. **Eager Loading** - Uses joinedload to prevent N+1 queries
3. **Pagination** - Prevents large result sets
4. **Efficient Counting** - Separate count query before data fetch

## Future Enhancements

1. Vehicle photo uploads
2. Maintenance schedule automation
3. Fuel consumption tracking
4. Vehicle utilization reports
5. Automatic expiry notifications (insurance, registration)
6. Vehicle performance analytics
7. Integration with telematics devices

---

**Status: ✅ DEPLOYED AND WORKING**
**Production URL:** https://api.safedriveafrica.com/api/vehicles
