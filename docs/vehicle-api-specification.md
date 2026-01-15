# Vehicle Management API Specification

**Document Version:** 1.0  
**Date:** January 15, 2026  
**Status:** Proposed  
**Author:** Development Team  
**Target Audience:** Backend Developers

---

## Table of Contents

1. [Overview](#overview)
2. [Business Requirements](#business-requirements)
3. [Data Models](#data-models)
4. [API Endpoints](#api-endpoints)
5. [Database Schema](#database-schema)
6. [Migration Strategy](#migration-strategy)
7. [Frontend Integration](#frontend-integration)

---

## Overview

### Problem Statement

The current Safe Drive Africa platform tracks **drivers** and their **trips**, but lacks the ability to track **individual vehicles**. This creates gaps for:

- **Fleet Managers**: Cannot track which vehicles are in their fleet, who drives them, or vehicle-specific metrics
- **Insurance Partners**: Cannot tie insurance policies to specific vehicles or assess vehicle-level risk
- **Compliance**: Cannot track vehicle maintenance, registration status, or roadworthiness

### Proposed Solution

Add a **Vehicle** entity to the data model with:
- Vehicle details (license plate, make, model, VIN, year)
- Fleet and vehicle group associations
- Driver-vehicle assignments
- Trip-vehicle linkage

---

## Business Requirements

### Must Have (P0)

1. **CRUD operations for Vehicles**
   - Create, read, update, delete vehicles
   - Associate vehicles with fleets and vehicle groups

2. **Driver-Vehicle Assignment**
   - Assign a driver to a primary vehicle
   - Support multiple drivers per vehicle (shift work)
   - Track assignment history

3. **Trip-Vehicle Association**
   - Link each trip to the vehicle used
   - Query trips by vehicle

### Should Have (P1)

4. **Vehicle Status Tracking**
   - Active, maintenance, retired status
   - Last trip date, total distance

5. **Bulk Operations**
   - CSV import for fleet onboarding
   - Batch update vehicle assignments

### Nice to Have (P2)

6. **Insurance Integration**
   - Policy number per vehicle
   - Insurance partner ID linkage

7. **Vehicle Documents**
   - Registration expiry date
   - Insurance expiry date
   - Inspection due date

---

## Data Models

### Vehicle

```python
class Vehicle(Base):
    __tablename__ = "vehicle"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    fleet_id: UUID = Column(UUID, ForeignKey("fleet.id"), nullable=False, index=True)
    vehicle_group_id: UUID = Column(UUID, ForeignKey("vehicle_group.id"), nullable=True)
    
    # Vehicle identification
    license_plate: str = Column(String(20), nullable=False, unique=True, index=True)
    vin: str = Column(String(17), nullable=True, unique=True)  # Vehicle Identification Number
    
    # Vehicle details
    make: str = Column(String(50), nullable=True)  # e.g., "Toyota"
    model: str = Column(String(50), nullable=True)  # e.g., "Hilux"
    year: int = Column(Integer, nullable=True)
    color: str = Column(String(30), nullable=True)
    vehicle_type: str = Column(String(30), nullable=True)  # car, motorcycle, truck, van
    
    # Status
    status: str = Column(String(20), default="active")  # active, maintenance, retired
    
    # Insurance (optional)
    insurance_policy_number: str = Column(String(50), nullable=True)
    insurance_partner_id: UUID = Column(UUID, ForeignKey("insurance_partner.id"), nullable=True)
    insurance_expiry_date: Date = Column(Date, nullable=True)
    
    # Registration
    registration_expiry_date: Date = Column(Date, nullable=True)
    
    # Metadata
    notes: str = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fleet = relationship("Fleet", back_populates="vehicles")
    vehicle_group = relationship("VehicleGroup", back_populates="vehicles")
    driver_assignments = relationship("DriverVehicleAssignment", back_populates="vehicle")
    trips = relationship("Trip", back_populates="vehicle")
```

### DriverVehicleAssignment

```python
class DriverVehicleAssignment(Base):
    __tablename__ = "driver_vehicle_assignment"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    driver_profile_id: UUID = Column(UUID, ForeignKey("driver_profile.id"), nullable=False, index=True)
    vehicle_id: UUID = Column(UUID, ForeignKey("vehicle.id"), nullable=False, index=True)
    
    is_primary: bool = Column(Boolean, default=False)  # Driver's default vehicle
    
    assigned_at: datetime = Column(DateTime, default=datetime.utcnow)
    unassigned_at: datetime = Column(DateTime, nullable=True)  # Null = still assigned
    
    # Relationships
    driver_profile = relationship("DriverProfile", back_populates="vehicle_assignments")
    vehicle = relationship("Vehicle", back_populates="driver_assignments")
```

### Trip (Modified)

```python
class Trip(Base):
    # ... existing fields ...
    
    # NEW FIELD
    vehicle_id: UUID = Column(UUID, ForeignKey("vehicle.id"), nullable=True, index=True)
    
    # Relationship
    vehicle = relationship("Vehicle", back_populates="trips")
```

---

## API Endpoints

### Vehicle CRUD

#### List Vehicles

```http
GET /api/vehicles
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| fleet_id | UUID | No | Filter by fleet |
| vehicle_group_id | UUID | No | Filter by vehicle group |
| status | string | No | Filter by status (active, maintenance, retired) |
| page | int | No | Page number (default: 1) |
| page_size | int | No | Items per page (default: 25, max: 100) |

**Response:**
```json
{
  "vehicles": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "fleet_id": "123e4567-e89b-12d3-a456-426614174000",
      "vehicle_group_id": "789e0123-e89b-12d3-a456-426614174000",
      "license_plate": "KAA 123A",
      "vin": "1HGBH41JXMN109186",
      "make": "Toyota",
      "model": "Hilux",
      "year": 2022,
      "color": "White",
      "vehicle_type": "truck",
      "status": "active",
      "insurance_policy_number": "INS-2024-001",
      "insurance_expiry_date": "2025-06-30",
      "registration_expiry_date": "2025-12-31",
      "created_at": "2024-01-15T10:30:00Z",
      "fleet": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Nairobi Fleet"
      },
      "vehicle_group": {
        "id": "789e0123-e89b-12d3-a456-426614174000",
        "name": "Delivery Trucks"
      },
      "primary_driver": {
        "driver_profile_id": "abc12345-e89b-12d3-a456-426614174000",
        "email": "driver@example.com"
      }
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 25
}
```

#### Get Single Vehicle

```http
GET /api/vehicles/{vehicle_id}
```

**Response:** Same as single item in list response, plus:
```json
{
  "...": "...",
  "assigned_drivers": [
    {
      "driver_profile_id": "abc12345-e89b-12d3-a456-426614174000",
      "email": "driver@example.com",
      "is_primary": true,
      "assigned_at": "2024-01-10T08:00:00Z"
    }
  ],
  "recent_trips": [
    {
      "id": "trip-uuid",
      "start_time": "2024-01-14T09:00:00Z",
      "end_time": "2024-01-14T10:30:00Z",
      "distance_km": 45.2,
      "unsafe_count": 2
    }
  ],
  "stats": {
    "total_trips": 234,
    "total_distance_km": 12500.5,
    "total_unsafe_behaviours": 45,
    "ubpk": 0.0036
  }
}
```

#### Create Vehicle

```http
POST /api/vehicles
```

**Request Body:**
```json
{
  "fleet_id": "123e4567-e89b-12d3-a456-426614174000",
  "vehicle_group_id": "789e0123-e89b-12d3-a456-426614174000",
  "license_plate": "KAA 123A",
  "vin": "1HGBH41JXMN109186",
  "make": "Toyota",
  "model": "Hilux",
  "year": 2022,
  "color": "White",
  "vehicle_type": "truck",
  "insurance_policy_number": "INS-2024-001",
  "insurance_partner_id": "ins-partner-uuid",
  "insurance_expiry_date": "2025-06-30",
  "registration_expiry_date": "2025-12-31",
  "notes": "Company vehicle, GPS tracker installed"
}
```

**Response:** Created vehicle object (201 Created)

#### Update Vehicle

```http
PATCH /api/vehicles/{vehicle_id}
```

**Request Body:** Partial vehicle object (only fields to update)

**Response:** Updated vehicle object (200 OK)

#### Delete Vehicle

```http
DELETE /api/vehicles/{vehicle_id}
```

**Response:** 204 No Content

**Note:** Should soft-delete (set status to "retired") rather than hard delete to preserve trip history.

---

### Batch Operations

#### Batch Create Vehicles

```http
POST /api/vehicles/batch
```

**Request Body:**
```json
{
  "vehicles": [
    {
      "fleet_id": "...",
      "license_plate": "KAA 123A",
      "make": "Toyota",
      "model": "Hilux",
      "year": 2022
    },
    {
      "fleet_id": "...",
      "license_plate": "KAB 456B",
      "make": "Honda",
      "model": "CR-V",
      "year": 2023
    }
  ]
}
```

**Response:**
```json
{
  "created": 2,
  "updated": 0,
  "skipped": 0,
  "errors": []
}
```

---

### Driver-Vehicle Assignments

#### Assign Driver to Vehicle

```http
POST /api/vehicles/{vehicle_id}/drivers
```

**Request Body:**
```json
{
  "driver_profile_id": "abc12345-e89b-12d3-a456-426614174000",
  "is_primary": true
}
```

**Response:** Assignment object (201 Created)

#### List Drivers for Vehicle

```http
GET /api/vehicles/{vehicle_id}/drivers
```

**Response:**
```json
{
  "drivers": [
    {
      "assignment_id": "...",
      "driver_profile_id": "...",
      "email": "driver@example.com",
      "is_primary": true,
      "assigned_at": "2024-01-10T08:00:00Z"
    }
  ]
}
```

#### Remove Driver from Vehicle

```http
DELETE /api/vehicles/{vehicle_id}/drivers/{driver_profile_id}
```

**Response:** 204 No Content

#### Get Vehicles for Driver

```http
GET /api/drivers/{driver_profile_id}/vehicles
```

**Response:**
```json
{
  "vehicles": [
    {
      "id": "...",
      "license_plate": "KAA 123A",
      "make": "Toyota",
      "model": "Hilux",
      "is_primary": true,
      "assigned_at": "2024-01-10T08:00:00Z"
    }
  ]
}
```

---

### Vehicle-Trip Queries

#### Get Trips for Vehicle

```http
GET /api/vehicles/{vehicle_id}/trips
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | date | Filter trips after this date |
| end_date | date | Filter trips before this date |
| page | int | Page number |
| page_size | int | Items per page |

**Response:**
```json
{
  "trips": [
    {
      "id": "trip-uuid",
      "driver_profile_id": "...",
      "start_time": "2024-01-14T09:00:00Z",
      "end_time": "2024-01-14T10:30:00Z",
      "distance_km": 45.2,
      "unsafe_count": 2,
      "ubpk": 0.044
    }
  ],
  "total": 234,
  "page": 1,
  "page_size": 25
}
```

#### Get Vehicle Statistics

```http
GET /api/vehicles/{vehicle_id}/stats
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| period | string | day, week, month, all (default: all) |

**Response:**
```json
{
  "vehicle_id": "...",
  "period": "month",
  "total_trips": 45,
  "total_distance_km": 2340.5,
  "total_duration_hours": 78.5,
  "total_unsafe_behaviours": 12,
  "ubpk": 0.0051,
  "unique_drivers": 3,
  "busiest_driver": {
    "driver_profile_id": "...",
    "email": "...",
    "trip_count": 30
  }
}
```

---

## Database Schema

### New Tables

```sql
-- Vehicle table
CREATE TABLE vehicle (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fleet_id UUID NOT NULL REFERENCES fleet(id),
    vehicle_group_id UUID REFERENCES vehicle_group(id),
    
    license_plate VARCHAR(20) NOT NULL UNIQUE,
    vin VARCHAR(17) UNIQUE,
    
    make VARCHAR(50),
    model VARCHAR(50),
    year INTEGER,
    color VARCHAR(30),
    vehicle_type VARCHAR(30),
    
    status VARCHAR(20) DEFAULT 'active',
    
    insurance_policy_number VARCHAR(50),
    insurance_partner_id UUID REFERENCES insurance_partner(id),
    insurance_expiry_date DATE,
    registration_expiry_date DATE,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_vehicle_fleet_id ON vehicle(fleet_id);
CREATE INDEX idx_vehicle_license_plate ON vehicle(license_plate);
CREATE INDEX idx_vehicle_status ON vehicle(status);

-- Driver-Vehicle Assignment table
CREATE TABLE driver_vehicle_assignment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_profile_id UUID NOT NULL REFERENCES driver_profile(id),
    vehicle_id UUID NOT NULL REFERENCES vehicle(id),
    
    is_primary BOOLEAN DEFAULT FALSE,
    
    assigned_at TIMESTAMP DEFAULT NOW(),
    unassigned_at TIMESTAMP,
    
    UNIQUE(driver_profile_id, vehicle_id, unassigned_at)
);

CREATE INDEX idx_dva_driver ON driver_vehicle_assignment(driver_profile_id);
CREATE INDEX idx_dva_vehicle ON driver_vehicle_assignment(vehicle_id);
CREATE INDEX idx_dva_active ON driver_vehicle_assignment(vehicle_id) WHERE unassigned_at IS NULL;
```

### Modified Tables

```sql
-- Add vehicle_id to trip table
ALTER TABLE trip ADD COLUMN vehicle_id UUID REFERENCES vehicle(id);
CREATE INDEX idx_trip_vehicle_id ON trip(vehicle_id);
```

---

## Migration Strategy

### Phase 1: Schema Migration (Backend)

1. Create `vehicle` table
2. Create `driver_vehicle_assignment` table
3. Add `vehicle_id` column to `trip` table (nullable initially)

### Phase 2: API Development (Backend)

1. Implement Vehicle CRUD endpoints
2. Implement Driver-Vehicle assignment endpoints
3. Add vehicle info to trip responses

### Phase 3: Data Migration (If needed)

1. If existing data has vehicle info embedded elsewhere, migrate it
2. Work with fleet managers to populate initial vehicle data

### Phase 4: Frontend Integration

1. Add AdminVehicles page (already prepared)
2. Update Fleet pages to show vehicle info
3. Update Trip views to show vehicle info
4. Update Insurance reports to include vehicle data

### Phase 5: Mobile App Integration

1. Update mobile app to capture vehicle_id when starting trip
2. Allow driver to select which vehicle they're driving

---

## Frontend Integration

### Types (Already Added)

```typescript
interface Vehicle {
  id: string
  fleet_id: string
  vehicle_group_id?: string | null
  license_plate: string
  vin?: string | null
  make?: string | null
  model?: string | null
  year?: number | null
  color?: string | null
  vehicle_type?: string | null
  status: 'active' | 'maintenance' | 'retired'
  insurance_policy_number?: string | null
  insurance_partner_id?: string | null
  insurance_expiry_date?: string | null
  registration_expiry_date?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
  fleet?: Fleet | null
  vehicle_group?: VehicleGroup | null
  primary_driver?: { driver_profile_id: string; email: string } | null
}

interface DriverVehicleAssignment {
  id: string
  driver_profile_id: string
  vehicle_id: string
  is_primary: boolean
  assigned_at: string
  unassigned_at?: string | null
  vehicle?: Vehicle | null
}
```

### API Functions (Already Added)

- `getVehicles(apiKey, params)` - List vehicles with filters
- `getVehicle(apiKey, vehicleId)` - Get single vehicle
- `createVehicle(apiKey, payload)` - Create vehicle
- `updateVehicle(apiKey, vehicleId, payload)` - Update vehicle
- `deleteVehicle(apiKey, vehicleId)` - Delete/retire vehicle
- `batchCreateVehicles(apiKey, vehicles)` - Bulk create
- `assignDriverToVehicle(apiKey, vehicleId, driverProfileId, isPrimary)` - Assign driver
- `removeDriverFromVehicle(apiKey, vehicleId, driverProfileId)` - Remove assignment
- `getVehicleDrivers(apiKey, vehicleId)` - List drivers for vehicle
- `getDriverVehicles(apiKey, driverProfileId)` - List vehicles for driver

### UI Pages (Already Added)

- `/admin/vehicles` - AdminVehicles page for managing vehicles

---

## Authorization

### Role Permissions

| Role | Permissions |
|------|-------------|
| admin | Full CRUD on all vehicles |
| fleet_manager | CRUD on vehicles in their fleet only |
| insurance_partner | Read vehicles linked to their policies |
| driver | Read their assigned vehicles only |
| researcher | Read-only access to anonymized vehicle data |

---

## Open Questions

1. **Should vehicle_id on Trip be required?**
   - Pros: Complete data, accurate vehicle tracking
   - Cons: Breaking change for existing mobile apps
   - Recommendation: Optional initially, required after mobile app update

2. **How to handle shared vehicles?**
   - Multiple drivers can be assigned to same vehicle
   - Only one can be "primary"
   - Trip captures actual driver, regardless of assignment

3. **Vehicle document storage?**
   - Should we store registration/insurance documents?
   - Would need file upload infrastructure
   - Recommendation: Phase 2 feature

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Schema Migration | 2 days | None |
| API Development | 5 days | Schema |
| Frontend Integration | 3 days | API |
| Testing | 2 days | All above |
| Mobile App Update | 5 days | API |
| **Total** | **~3 weeks** | |

---

**Document Status:** Ready for Review  
**Next Steps:** Backend team to review and provide feedback
