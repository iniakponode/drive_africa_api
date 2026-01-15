# Database Performance Optimization Guide
## A Beginner's Journey from 165 Seconds to 79 Milliseconds

**Author:** Safe Drive Africa Development Team  
**Date:** January 15, 2026  
**Difficulty Level:** Beginner-Friendly with Advanced Concepts Explained

---

## Table of Contents

1. [Introduction](#introduction)
2. [Understanding the Problem](#understanding-the-problem)
3. [Learning the Basics](#learning-the-basics)
4. [Solution Architecture](#solution-architecture)
5. [Implementation Journey](#implementation-journey)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Results and Verification](#results-and-verification)
8. [Maintenance and Best Practices](#maintenance-and-best-practices)

---

## Introduction

### What This Guide Covers

This guide documents the complete journey of optimizing a slow analytics API endpoint that was timing out after 60+ seconds. By the end of this optimization:
- **Original response time:** 165 seconds (2 minutes 45 seconds)
- **Final response time:** 79 milliseconds (0.079 seconds)
- **Total improvement:** 2,088x faster

### Who Should Read This?

- Backend developers new to performance optimization
- Students learning about database query optimization
- Developers working with large datasets in FastAPI/SQLAlchemy
- Anyone experiencing slow API responses with sensor data

### Technologies Used

- **Backend Framework:** FastAPI (Python)
- **Database ORM:** SQLAlchemy
- **Database:** MySQL
- **Cache:** Redis
- **Web Server:** Nginx + Gunicorn
- **Server OS:** Ubuntu Linux

---

## Understanding the Problem

### The Scenario

We had an analytics endpoint `/api/analytics/bad-days` that:
- Analyzes driver behavior over time
- Processes data from three large tables:
  - **trips:** 646 records
  - **locations:** 22,558 records  
  - **raw_sensor_data:** ~8.5 million records
- Returns a paginated list of drivers with "bad day" counts

### The Symptoms

1. **CORS Errors in Web Client**
   - Browser console showed: `Access to fetch blocked by CORS policy`
   - Users couldn't access the dashboard

2. **504 Gateway Timeout**
   - Requests took 60+ seconds
   - Nginx timeout killed the request
   - Error: "504 Gateway Timeout"

3. **Server Load**
   - Database CPU spiking to 100%
   - Memory usage climbing during queries
   - Other API endpoints slowing down

### Why Was It So Slow?

The original query had a fundamental flaw:

```python
# BAD APPROACH - Loading everything into Python memory
all_trips = db.query(Trip).filter(...).all()  # Gets 646 trips

for trip in all_trips:
    # For EACH trip, query raw_sensor_data
    sensor_data = db.query(RawSensorData).filter(
        RawSensorData.trip_id == trip.id
    ).all()  # This runs 646 times!
    
    # Calculate distance in Python
    total_distance = sum([s.location.distance for s in sensor_data])
```

**Why this is bad:**
- Makes 646 separate database queries
- Loads millions of rows into Python memory
- Does aggregation (summing) in Python instead of database
- No indexes to speed up lookups

---

## Learning the Basics

### Concept 1: Database Indexes

**What is an index?**  
Think of it like an index in a textbook. Instead of reading every page to find "Redis", you look at the index which tells you "Redis is on page 45."

**In databases:**
```sql
-- Without index: Database scans ALL 8.5M rows
SELECT * FROM raw_sensor_data WHERE trip_id = 'abc123';

-- With index: Database jumps directly to matching rows
CREATE INDEX idx_trip_id ON raw_sensor_data(trip_id);
```

**When to use indexes:**
- Columns frequently used in `WHERE` clauses
- Foreign key columns
- Columns used in `JOIN` operations
- Columns used in `ORDER BY`

**Cost of indexes:**
- Takes up disk space
- Slows down `INSERT` and `UPDATE` operations
- MySQL automatically maintains them

### Concept 2: Query Aggregation

**Bad: Aggregating in Python**
```python
# Fetches 1,000,000 rows to Python
rows = db.query(RawSensorData).all()
total = sum([row.value for row in rows])  # Python does math
```

**Good: Aggregating in Database**
```sql
-- Database does the math, returns ONE row
SELECT SUM(value) as total FROM raw_sensor_data;
```

**Why database aggregation is faster:**
- Database engines are optimized for this
- Data never leaves the database server
- Uses indexes efficiently
- Returns only the result, not all rows

### Concept 3: Query Planning (Explain)

Before optimizing, understand what the database is doing:

```sql
EXPLAIN SELECT * FROM trips WHERE start_time > 1234567890;
```

Output shows:
- Which indexes are used (or not used)
- How many rows are scanned
- Join strategies
- Estimated cost

### Concept 4: Caching

**What is caching?**  
Storing the result of an expensive operation so you don't have to do it again.

**Example:**
```python
# First request: Calculate for 10 seconds, store result
result = expensive_calculation()
cache.set("result_key", result, expire=300)  # Store for 5 minutes

# Second request: Retrieve in 0.001 seconds
result = cache.get("result_key")  # Instant!
```

**Cache Strategies:**
- **Time-based expiration:** Data expires after X seconds
- **LRU (Least Recently Used):** Remove oldest unused items when full
- **Write-through:** Update cache when database updates
- **Cache invalidation:** Delete cache when data changes

### Concept 5: N+1 Query Problem

**The Problem:**
```python
# 1 query to get all trips
trips = db.query(Trip).all()

# N queries (one per trip) - BAD!
for trip in trips:
    locations = db.query(Location).filter(
        Location.trip_id == trip.id
    ).all()
```

If you have 100 trips, this makes **101 queries** (1 + 100).

**The Solution: JOINs**
```python
# 1 query total - GOOD!
results = db.query(Trip, Location).join(
    Location, Location.trip_id == Trip.id
).all()
```

---

## Solution Architecture

### Three-Phase Approach

We implemented a **three-phase optimization strategy**:

#### Phase 1: Database Optimization + Caching (IMPLEMENTED)
- **Target:** Queries < 10 seconds, cached < 100ms
- **For:** Current dataset (646 trips, 8.5M sensor records)
- **Techniques:**
  - Database indexes on frequently queried columns
  - Query restructuring (pre-aggregation)
  - Redis caching with 5-minute TTL
  - Page size reduction (50 → 25)

#### Phase 2: Pre-aggregated Summary Tables (PREPARED, NOT ACTIVE)
- **Target:** Queries < 2 seconds even uncached
- **Trigger:** When trips exceed 2,000
- **Techniques:**
  - New `trip_summary` table with pre-computed metrics
  - Database triggers to auto-update on INSERT/UPDATE
  - Aggregation happens at write-time, not read-time

#### Phase 3: Background Job Pre-computation (PREPARED, NOT ACTIVE)
- **Target:** Queries < 500ms always
- **Trigger:** When drivers exceed 10,000
- **Techniques:**
  - Celery background workers
  - Scheduled jobs every 15 minutes
  - Pre-compute all driver statistics
  - API reads from pre-computed cache

### Architecture Diagram

```
┌─────────────┐
│  Web Client │ (Admin Dashboard)
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────┐
│    Nginx    │ (Reverse Proxy, CORS, SSL)
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│  Gunicorn   │ (WSGI Server, 4 workers)
└──────┬──────┘
       │
       ▼
┌─────────────┐         ┌─────────────┐
│   FastAPI   │────────▶│    Redis    │ (L1 Cache, 5min TTL)
│  (Python)   │         └─────────────┘
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    MySQL    │ (Database with Indexes)
│   8.5M rows │
└─────────────┘
```

### Data Flow

**First Request (Cache Miss):**
```
Client → Nginx → Gunicorn → FastAPI
                              ↓
                         Check Redis (miss)
                              ↓
                         Query MySQL (10s)
                              ↓
                         Store in Redis
                              ↓
                         Return JSON → Client
```

**Subsequent Requests (Cache Hit):**
```
Client → Nginx → Gunicorn → FastAPI
                              ↓
                         Check Redis (HIT!)
                              ↓
                         Return JSON (13ms) → Client
```

---

## Implementation Journey

### Step 1: Fix CORS Errors

**Problem:** Web client couldn't access API due to CORS policy.

**What is CORS?**  
Cross-Origin Resource Sharing - a security feature that blocks JavaScript from accessing APIs on different domains.

**Solution:**

```python
# safedrive/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://datahub.safedriveafrica.com",  # Admin dashboard
        "https://api.safedriveafrica.com",
        "http://localhost:3000",  # Development
    ],
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # X-API-Key, Authorization, etc.
)
```

**Nginx Configuration:**
```nginx
# /etc/nginx/sites-available/api.safedriveafrica.com
location /api/ {
    # CORS headers
    add_header 'Access-Control-Allow-Origin' 'https://datahub.safedriveafrica.com' always;
    add_header 'Access-Control-Allow-Credentials' 'true' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Origin, X-API-Key, Authorization, Content-Type' always;
    
    # Handle preflight requests
    if ($request_method = 'OPTIONS') {
        return 204;
    }
    
    # Increase timeout for slow queries
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    
    proxy_pass http://127.0.0.1:8000;
}
```

**Testing:**
```bash
# Test CORS headers are present
curl -I -H "Origin: https://datahub.safedriveafrica.com" \
  https://api.safedriveafrica.com/api/analytics/bad-days

# Should include:
# Access-Control-Allow-Origin: https://datahub.safedriveafrica.com
# Access-Control-Allow-Credentials: true
```

### Step 2: Increase Timeouts (Temporary Fix)

While we optimize, prevent requests from timing out:

**Nginx:**
```nginx
proxy_read_timeout 300s;  # Wait up to 5 minutes
```

**Gunicorn:**
```bash
# gunicorn.conf.py or command line
gunicorn --timeout 120 main:app
```

**Why this is NOT a permanent solution:**
- Users won't wait 2+ minutes
- Server resources are tied up
- Other requests may be blocked

### Step 3: Add Database Indexes

**Analyze the Query:**
```sql
EXPLAIN SELECT * FROM trip 
WHERE start_time >= 1234567890 
ORDER BY start_time DESC;
```

Output showed:
- **Type:** ALL (table scan - BAD!)
- **Rows:** 646 (scanning every row)
- **Extra:** Using filesort (sorting in memory - BAD!)

**Create Indexes:**

```sql
-- scripts/add_analytics_indexes.sql

-- 1. Speed up time-based filtering
CREATE INDEX idx_trip_start_time ON trip(start_time);

-- 2. Speed up driver + time queries
CREATE INDEX idx_trip_driver_time ON trip(driverProfileId, start_time);

-- 3. Speed up trip aggregations
CREATE INDEX idx_raw_sensor_trip ON raw_sensor_data(trip_id);

-- 4. Speed up location lookups
CREATE INDEX idx_raw_sensor_location ON raw_sensor_data(location_id);

-- 5. Speed up unsafe behavior counts
CREATE INDEX idx_unsafe_trip ON unsafe_behaviour(trip_id);

-- 6. Composite index for common query pattern
CREATE INDEX idx_trip_composite ON trip(start_time, driverProfileId, id);
```

**Applying Indexes:**
```bash
# Connect to database
mysql -u dev2 -pProgressIniks2018 drive_safe_db < scripts/add_analytics_indexes.sql
```

**Verifying Indexes:**
```sql
-- Check if index exists
SHOW INDEXES FROM trip;

-- Test query again
EXPLAIN SELECT * FROM trip WHERE start_time >= 1234567890;
-- Should now show: type: range, key: idx_trip_start_time
```

**Result:** Queries improved from 165s to ~10s, but still too slow.

### Step 4: Restructure Query (Pre-Aggregation)

**The Problem: Join Order Matters**

**Bad Approach:**
```sql
-- Join 8.5M sensor records THEN aggregate
SELECT trip.id, SUM(location.distance)
FROM trip
JOIN raw_sensor_data ON raw_sensor_data.trip_id = trip.id
JOIN location ON location.id = raw_sensor_data.location_id
GROUP BY trip.id;

-- This creates a MASSIVE intermediate result set before summing!
```

**Good Approach:**
```sql
-- Aggregate FIRST, then join results
SELECT trip.id, subq.total_distance
FROM trip
LEFT JOIN (
    -- This subquery runs FIRST and reduces 8.5M rows to 646 rows
    SELECT trip_id, SUM(location.distance) as total_distance
    FROM raw_sensor_data
    LEFT JOIN location ON location.id = raw_sensor_data.location_id
    GROUP BY trip_id
) AS subq ON subq.trip_id = trip.id;

-- Much smaller intermediate result set!
```

**Implementation in SQLAlchemy:**

```python
# safedrive/api/v1/endpoints/analytics.py

# Pre-aggregate distances per trip
distance_subq = (
    db.query(
        RawSensorData.trip_id,
        func.coalesce(func.sum(Location.distance), 0).label("total_distance"),
    )
    .outerjoin(Location, Location.id == RawSensorData.location_id)
    .group_by(RawSensorData.trip_id)
    .subquery()
)

# Now join the aggregated results to trips
trip_data = (
    db.query(
        Trip.driverProfileId,
        Trip.id.label("trip_id"),
        Trip.start_time,
        Trip.start_date,
        func.coalesce(distance_subq.c.total_distance, 0).label("distance_m"),
    )
    .outerjoin(distance_subq, distance_subq.c.trip_id == Trip.id)
    .filter(Trip.start_time >= cutoff_timestamp_ms)
    .order_by(Trip.start_time.desc())
    .all()
)
```

**Key Concepts:**
- **Subquery:** A query inside another query
- **GROUP BY:** Aggregates rows with same value into one row
- **LEFT JOIN:** Keeps all trips even if they have no sensor data
- **func.coalesce():** Returns first non-NULL value (handles missing data)

**Result:** Queries improved from 188s to **10.3 seconds**!

### Step 5: Reduce Page Size

**Simple but Effective:**
```python
# Before
page_size: int = Query(50, ge=10, le=100)  # Default 50 drivers

# After
page_size: int = Query(25, ge=10, le=100)  # Default 25 drivers
```

**Why this helps:**
- Fewer drivers = less data to process
- User experience: pagination is better than huge lists
- Faster initial page load

### Step 6: Install and Configure Redis

**What is Redis?**  
An in-memory data store used as a cache. Think of it as ultra-fast RAM storage for frequently accessed data.

**Installation on Ubuntu:**
```bash
# Update package list
sudo apt update

# Install Redis
sudo apt install redis-server -y

# Verify installation
redis-cli --version
# Output: redis-cli 6.0.16
```

**Configuration:**
```bash
# Edit configuration
sudo nano /etc/redis/redis.conf

# Key settings:
maxmemory 256mb                  # Use 256MB for cache
maxmemory-policy allkeys-lru     # Remove least recently used items
supervised systemd               # Run as systemd service
bind 127.0.0.1 ::1              # Only accept local connections
```

**Common Configuration Mistakes:**
```bash
# ❌ WRONG - Redis won't understand "mb"
maxmemory 256mb

# ✅ CORRECT - Must be in bytes
maxmemory 268435456

# ❌ WRONG - Typo
supervised supervised systemd

# ✅ CORRECT
supervised systemd
```

**Start Redis:**
```bash
# Enable on boot
sudo systemctl enable redis-server

# Start service
sudo systemctl start redis-server

# Check status
sudo systemctl status redis-server

# Test connection
redis-cli ping
# Output: PONG
```

**Install Python Redis Client:**
```bash
# Add to requirements.txt
echo "redis==5.0.1" >> requirements.txt

# Install in virtual environment
source venv/bin/activate
pip install redis==5.0.1
```

### Step 7: Implement Caching Module

**Create Cache Module:**

```python
# safedrive/core/cache.py
import json
import hashlib
import logging
from typing import Any, Optional
import redis

logger = logging.getLogger(__name__)

# Cache TTL (Time To Live) in seconds
CACHE_TTL_SHORT = 300    # 5 minutes
CACHE_TTL_MEDIUM = 600   # 10 minutes  
CACHE_TTL_LONG = 1800    # 30 minutes

# Singleton Redis client
_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> Optional[redis.Redis]:
    """
    Get or create Redis client.
    Returns None if Redis is unavailable (graceful degradation).
    """
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        _redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        # Test connection
        _redis_client.ping()
        logger.info("Redis connection established")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        return None

def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate a consistent cache key from arguments.
    
    Example:
        generate_cache_key("bad_days", cohort=[1,2,3], page=1)
        # Returns: "bad_days:a3f2b1c4d5e6"
    """
    # Combine all arguments
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    
    # Create hash of arguments for consistency
    key_string = "|".join(key_parts)
    hash_suffix = hashlib.md5(key_string.encode()).hexdigest()[:12]
    
    # Format: prefix:hash
    prefix = args[0] if args else "cache"
    return f"{prefix}:{hash_suffix}"

def cache_get(key: str) -> Optional[Any]:
    """
    Get value from cache.
    Returns None if key doesn't exist or Redis is unavailable.
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.warning(f"Cache get error for {key}: {e}")
        return None

def cache_set(key: str, value: Any, ttl: int = CACHE_TTL_SHORT) -> bool:
    """
    Set value in cache with expiration time.
    Returns True if successful, False otherwise.
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        json_value = json.dumps(value)
        client.setex(key, ttl, json_value)
        logger.info(f"Cached {key} for {ttl}s")
        return True
    except Exception as e:
        logger.warning(f"Cache set error for {key}: {e}")
        return False

def cache_invalidate_pattern(pattern: str) -> int:
    """
    Delete all keys matching pattern.
    
    Example:
        cache_invalidate_pattern("bad_days:*")  # Delete all bad_days caches
    """
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            deleted = client.delete(*keys)
            logger.info(f"Invalidated {deleted} keys matching {pattern}")
            return deleted
        return 0
    except Exception as e:
        logger.warning(f"Cache invalidation error for {pattern}: {e}")
        return 0
```

**Key Features:**
- **Graceful Degradation:** If Redis is down, API still works (just slower)
- **Connection Pooling:** Reuses single Redis connection
- **Error Handling:** Logs errors but doesn't crash
- **JSON Serialization:** Automatically converts Python objects to JSON

### Step 8: Update Analytics Endpoint

**Add Caching Logic:**

```python
# safedrive/api/v1/endpoints/analytics.py

@router.get("/analytics/bad-days", response_model=BadDaysResponse)
def bad_days(
    fleet_id: Optional[UUID] = Query(None, alias="fleetId"),
    insurance_partner_id: Optional[UUID] = Query(None, alias="insurancePartnerId"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(25, ge=10, le=100, description="Drivers per page"),
    db: Session = Depends(get_db),
    current_client: ApiClientContext = Depends(
        require_roles_or_jwt(
            Role.ADMIN,
            Role.RESEARCHER,
            Role.FLEET_MANAGER,
            Role.INSURANCE_PARTNER,
            Role.DRIVER,
        )
    ),
) -> BadDaysResponse:
    """
    Get drivers with "bad days" - days where UBPK increased significantly.
    Results are cached for 5 minutes.
    """
    # Resolve which drivers to analyze
    cohort_ids, _ = _resolve_cohort(
        db, current_client, fleet_id, insurance_partner_id, require_scope=False
    )
    
    # ✅ TRY CACHE FIRST
    from safedrive.core.cache import cache_get, cache_set, generate_cache_key, CACHE_TTL_SHORT
    
    cache_key = generate_cache_key(
        "bad_days",
        cohort=sorted(cohort_ids) if cohort_ids else None,
        page=page,
        page_size=page_size
    )
    
    cached_result = cache_get(cache_key)
    if cached_result is not None:
        logger.info(f"Cache HIT for {cache_key}")
        return BadDaysResponse(**cached_result)
    
    logger.info(f"Cache MISS for {cache_key} - computing...")
    
    # ... expensive database query here ...
    
    response = BadDaysResponse(
        thresholds=BadDaysThresholds(
            day=day_threshold,
            week=week_threshold,
            month=month_threshold,
        ),
        drivers=drivers,
    )
    
    # ✅ CACHE THE RESULT
    # Use model_dump(mode='json') to serialize UUIDs properly
    cache_set(cache_key, response.model_dump(mode='json'), CACHE_TTL_SHORT)
    
    return response
```

**Important Note: UUID Serialization**

First attempt failed with:
```
Cache set error: Object of type UUID is not JSON serializable
```

**Problem:** Python's UUID objects can't be directly converted to JSON.

**Wrong Fix:**
```python
cache_set(cache_key, response.dict(), CACHE_TTL_SHORT)  # ❌ Fails with UUIDs
```

**Correct Fix:**
```python
cache_set(cache_key, response.model_dump(mode='json'), CACHE_TTL_SHORT)  # ✅ Works!
```

The `mode='json'` parameter tells Pydantic to convert all non-JSON-serializable types (like UUID, datetime) to strings.

### Step 9: Deploy and Test

**Commit Changes:**
```bash
git add safedrive/core/cache.py
git add safedrive/api/v1/endpoints/analytics.py
git add requirements.txt
git commit -m "Add Redis caching with UUID serialization fix"
git push origin main
```

**Deploy on Server:**
```bash
# SSH to server
ssh root@serv.ungozuhost.com

# Navigate to application directory
cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com

# Pull latest code (via Plesk or git)
# User pulls via Plesk Git interface

# Install new dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart safedriveapi-prod

# Verify service is running
sudo systemctl status safedriveapi-prod
```

**Test Uncached Request:**
```bash
time curl -s -H 'X-API-Key: 02QDlql_JlwQXjdcj-Awsw8gBPs06-6JEP-aasDKf38' \
  'http://localhost:8000/api/analytics/bad-days?page=2&pageSize=25' > /dev/null

# Output:
# real    0m10.378s  <- First request computes
```

**Test Cached Request:**
```bash
time curl -s -H 'X-API-Key: 02QDlql_JlwQXjdcj-Awsw8gBPs06-6JEP-aasDKf38' \
  'http://localhost:8000/api/analytics/bad-days?page=2&pageSize=25' > /dev/null

# Output:
# real    0m0.013s  <- Second request from cache!
```

**Verify Cache Keys:**
```bash
# Connect to Redis
redis-cli

# List all bad_days cache keys
KEYS "bad_days:*"
# Output:
# 1) "bad_days:3d051f1cdda3"
# 2) "bad_days:d473e14ec6f6"

# Check TTL (time remaining)
TTL bad_days:3d051f1cdda3
# Output: 245 (seconds remaining out of 300)

# View cached data (first 100 chars)
GET bad_days:3d051f1cdda3 | head -c 100
```

---

## Troubleshooting Guide

### Issue 1: CORS Errors

**Symptoms:**
```
Access to fetch at 'https://api.safedriveafrica.com/api/analytics/bad-days' 
from origin 'https://datahub.safedriveafrica.com' has been blocked by CORS policy
```

**Diagnosis:**
```bash
# Check if CORS headers are present
curl -I -H "Origin: https://datahub.safedriveafrica.com" \
  https://api.safedriveafrica.com/api/analytics/bad-days
```

**Look for:**
- `Access-Control-Allow-Origin` header
- `Access-Control-Allow-Credentials` header

**Fixes:**

1. **Add CORS middleware in FastAPI:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://datahub.safedriveafrica.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **Configure Nginx:**
```nginx
add_header 'Access-Control-Allow-Origin' 'https://datahub.safedriveafrica.com' always;
add_header 'Access-Control-Allow-Credentials' 'true' always;
```

3. **Restart services:**
```bash
sudo systemctl restart nginx
sudo systemctl restart safedriveapi-prod
```

### Issue 2: 504 Gateway Timeout

**Symptoms:**
- Request takes >60 seconds
- Browser shows "504 Gateway Timeout"
- Nginx error log shows: `upstream timed out`

**Diagnosis:**
```bash
# Check Nginx timeout settings
grep timeout /etc/nginx/sites-available/api.safedriveafrica.com

# Check Gunicorn timeout
ps aux | grep gunicorn | grep timeout
```

**Immediate Fix (Temporary):**
```nginx
# Increase Nginx timeouts
proxy_read_timeout 300s;
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
```

```bash
# Increase Gunicorn timeout
gunicorn --timeout 120 main:app
```

**Permanent Fix:**
Optimize queries (see implementation steps)

### Issue 3: Authentication Not Working

**Symptoms:**
```json
{"detail":"Authentication required. Provide either X-API-Key or Authorization: Bearer token."}
```

**Diagnosis Steps:**

1. **Verify API key exists in database:**
```sql
SELECT name, role, active 
FROM api_client 
WHERE api_key_hash = SHA2('YOUR_API_KEY_HERE', 256);
```

2. **Check if header is being sent:**
```bash
# Verbose curl shows headers
curl -v -H 'X-API-Key: YOUR_KEY' http://localhost:8000/api/auth/me
```

3. **Test hash computation:**
```python
import hashlib
key = "02QDlql_JlwQXjdcj-Awsw8gBPs06-6JEP-aasDKf38"
print(hashlib.sha256(key.encode()).hexdigest())
```

**Common Mistakes:**

1. **Wrong header syntax in SSH:**
```bash
# ❌ WRONG - Shell interprets special characters
ssh user@server curl -H "X-API-Key: abc-123" http://...

# ✅ CORRECT - Use single quotes inside double quotes
ssh user@server "curl -H 'X-API-Key: abc-123' http://..."
```

2. **Old API key:**
Check `ADMIN_KEYS.txt` on server for current keys:
```bash
cat /var/www/.../ADMIN_KEYS.txt
```

3. **API key not in database:**
Run seeding script:
```bash
python scripts/seed_api_keys.py
```

### Issue 4: Redis Connection Failed

**Symptoms:**
```
Redis unavailable: Error 111 connecting to localhost:6379. Connection refused.
```

**Diagnosis:**
```bash
# Check if Redis is running
sudo systemctl status redis-server

# Test connection
redis-cli ping
```

**Fixes:**

1. **Start Redis:**
```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server  # Start on boot
```

2. **Check Redis is listening:**
```bash
sudo netstat -tlnp | grep 6379
```

3. **Verify configuration:**
```bash
redis-cli CONFIG GET bind
# Should show: 127.0.0.1 ::1
```

4. **Check logs:**
```bash
sudo journalctl -u redis-server -n 50
```

### Issue 5: Cache Serialization Error

**Symptoms:**
```
Cache set error for bad_days:abc123: Object of type UUID is not JSON serializable
```

**Diagnosis:**
The response contains UUID objects that can't be converted to JSON.

**Fix:**
```python
# ❌ WRONG
cache_set(key, response.dict(), ttl)

# ✅ CORRECT - Use mode='json' for proper serialization
cache_set(key, response.model_dump(mode='json'), ttl)
```

**Understanding the Issue:**

Python's `json.dumps()` can't handle:
- UUID objects
- datetime objects (in some formats)
- Custom classes

Pydantic's `model_dump(mode='json')` converts these to strings automatically.

### Issue 6: Indexes Not Being Used

**Symptoms:**
- Queries still slow after creating indexes
- `EXPLAIN` shows `type: ALL` (full table scan)

**Diagnosis:**
```sql
-- Check if index exists
SHOW INDEXES FROM trip;

-- Check if index is used
EXPLAIN SELECT * FROM trip WHERE start_time > 123456789;
```

**Common Issues:**

1. **Wrong column type:**
```sql
-- Index on INT won't help VARCHAR queries
CREATE INDEX idx ON trip(start_time);  -- start_time is INT
SELECT * FROM trip WHERE start_time = '123456789';  -- String literal!

-- Fix: Use correct type
SELECT * FROM trip WHERE start_time = 123456789;  -- Integer
```

2. **Function on indexed column:**
```sql
-- Index won't be used
SELECT * FROM trip WHERE UNIX_TIMESTAMP(start_time) > 123456789;

-- Fix: Remove function
SELECT * FROM trip WHERE start_time > 123456789;
```

3. **OR conditions:**
```sql
-- Index may not be used optimally
SELECT * FROM trip WHERE start_time > 123 OR driverProfileId = 'abc';

-- Fix: Use UNION or separate queries
```

4. **MySQL optimizer choice:**
Sometimes MySQL thinks a full scan is faster. Force index:
```sql
SELECT * FROM trip USE INDEX (idx_trip_start_time) WHERE start_time > 123;
```

### Issue 7: Cache Not Expiring

**Symptoms:**
- Old data returned from cache
- Changes in database not reflected

**Diagnosis:**
```bash
# Check TTL of cache key
redis-cli TTL bad_days:abc123

# -1 means no expiration set!
```

**Fix:**
Ensure you're passing `ttl` parameter:
```python
# ❌ WRONG
cache_set(key, value)  # No expiration!

# ✅ CORRECT
cache_set(key, value, CACHE_TTL_SHORT)  # 300 seconds
```

**Manual Cache Invalidation:**
```bash
# Delete specific key
redis-cli DEL bad_days:abc123

# Delete all bad_days caches
redis-cli KEYS "bad_days:*" | xargs redis-cli DEL

# Or use the Python function
from safedrive.core.cache import cache_invalidate_pattern
cache_invalidate_pattern("bad_days:*")
```

### Issue 8: Server Restarting Clears Cache

**Symptom:**
All cache lost after server reboot.

**Explanation:**
Redis is an **in-memory** store. By default, data lives in RAM only.

**Solutions:**

1. **Accept it (recommended for our use case):**
- Analytics caches are short-lived anyway (5 minutes)
- First request after restart will be slow, then fast again
- No disk I/O overhead

2. **Enable Redis persistence:**
```bash
# Edit /etc/redis/redis.conf
save 900 1      # Save after 900 seconds if 1 key changed
save 300 10     # Save after 300 seconds if 10 keys changed
save 60 10000   # Save after 60 seconds if 10000 keys changed
```

Trade-offs:
- ✅ Survives restarts
- ❌ Slower writes
- ❌ More disk usage

### Issue 9: Memory Usage Growing

**Symptoms:**
```bash
redis-cli INFO memory
# used_memory_human:250.00M
# maxmemory_human:256.00M  <- Almost full!
```

**Diagnosis:**
```bash
# Check eviction stats
redis-cli INFO stats | grep evicted
```

**Fixes:**

1. **Increase max memory:**
```bash
# /etc/redis/redis.conf
maxmemory 512mb  # Increase to 512MB (in bytes: 536870912)
```

2. **Verify eviction policy:**
```bash
redis-cli CONFIG GET maxmemory-policy
# Should be: allkeys-lru (removes least recently used)
```

3. **Monitor key sizes:**
```bash
# Find largest keys
redis-cli --bigkeys
```

4. **Reduce TTL:**
```python
# If cache is filling up, reduce expiration time
CACHE_TTL_SHORT = 180  # 3 minutes instead of 5
```

### Issue 10: Different Results Cached vs Uncached

**Symptoms:**
- First request returns correct data
- Cached request returns stale/wrong data

**Diagnosis:**

1. **Check cache key generation:**
```python
# Make sure all parameters are included
cache_key = generate_cache_key(
    "bad_days",
    cohort=sorted(cohort_ids),  # ← Don't forget parameters!
    page=page,
    page_size=page_size,
    # Missing: start_date? fleet_id?
)
```

2. **Test cache key consistency:**
```python
# Same parameters should generate same key
key1 = generate_cache_key("test", [1,2,3], page=1)
key2 = generate_cache_key("test", [1,2,3], page=1)
assert key1 == key2  # Should be True

# Different order should generate different key
key3 = generate_cache_key("test", [3,2,1], page=1)
assert key1 != key3  # Should be True
```

**Fix:**
Include ALL parameters that affect the result:
```python
cache_key = generate_cache_key(
    "bad_days",
    cohort=sorted(cohort_ids) if cohort_ids else None,
    page=page,
    page_size=page_size,
    fleet_id=str(fleet_id) if fleet_id else None,
    partner_id=str(insurance_partner_id) if insurance_partner_id else None,
)
```

---

## Results and Verification

### Performance Metrics

| Stage | Time | Improvement |
|-------|------|-------------|
| **Original (no optimization)** | 165 seconds | Baseline |
| **After indexes** | 188 seconds | -14% (worse!) |
| **After query restructure** | 10.3 seconds | **16x faster** |
| **After caching (cache hit)** | 0.013 seconds | **12,692x faster** |
| **HTTPS with cache** | 0.079 seconds | **2,088x faster** |

### Why Indexes Made It Worse Initially

This is counter-intuitive but educational!

**Reason:** MySQL was scanning indexes instead of the table, but with:
- Many indexes to check
- No covering index (had to lookup table anyway)
- Optimizer chose wrong index

**Lesson:** More indexes ≠ faster queries. The query structure matters more.

### Verification Commands

**1. Check Cache Hit Rate:**
```bash
# Make 10 requests to same endpoint
for i in {1..10}; do
  time curl -s -H 'X-API-Key: KEY' \
    'http://localhost:8000/api/analytics/bad-days?page=1&pageSize=25' > /dev/null
done

# First should be ~10s, rest should be <0.1s
```

**2. Monitor Redis:**
```bash
# Watch Redis in real-time
redis-cli MONITOR

# In another terminal, make API request
curl -H 'X-API-Key: KEY' http://localhost:8000/api/analytics/bad-days?page=1

# You should see:
# "SETEX" "bad_days:abc123" "300" "{...json...}"
# "GET" "bad_days:abc123"
```

**3. Check Cache Memory:**
```bash
redis-cli INFO memory

# Look for:
# used_memory_human: 45.12M
# maxmemory_human: 256.00M
```

**4. View Cache Contents:**
```bash
# List all cache keys
redis-cli KEYS "*"

# Get specific cache
redis-cli GET bad_days:3d051f1cdda3

# Check when it expires
redis-cli TTL bad_days:3d051f1cdda3
# Returns seconds remaining (0-300)
```

**5. Test Cache Invalidation:**
```bash
# Delete all bad_days caches
redis-cli KEYS "bad_days:*" | xargs redis-cli DEL

# Next request should be slow (cache miss)
time curl -H 'X-API-Key: KEY' http://localhost:8000/api/analytics/bad-days?page=1
# Should take ~10s

# Second request should be fast (cache hit)
time curl -H 'X-API-Key: KEY' http://localhost:8000/api/analytics/bad-days?page=1
# Should take <0.1s
```

### Production Monitoring

**Server Logs:**
```bash
# Watch application logs
sudo journalctl -u safedriveapi-prod -f

# Look for:
# "Cache HIT for bad_days:abc123"
# "Cache MISS for bad_days:abc123 - computing..."
# "Cached bad_days:abc123 for 300s"
```

**Redis Stats:**
```bash
# Get comprehensive stats
redis-cli INFO

# Key metrics:
# - used_memory: Current memory usage
# - evicted_keys: How many keys were removed (should be low)
# - keyspace_hits: Cache hits
# - keyspace_misses: Cache misses
```

**Calculate Hit Rate:**
```bash
# Get stats
redis-cli INFO stats | grep keyspace

# Example output:
# keyspace_hits:1523
# keyspace_misses:48

# Hit rate = hits / (hits + misses)
# 1523 / (1523 + 48) = 96.9% hit rate 🎉
```

---

## Maintenance and Best Practices

### Daily Monitoring

**1. Check Service Health:**
```bash
# All should be "active (running)"
sudo systemctl status safedriveapi-prod
sudo systemctl status redis-server
sudo systemctl status nginx
```

**2. Monitor Response Times:**
```bash
# Test endpoint
time curl -s -H 'X-API-Key: KEY' \
  'https://api.safedriveafrica.com/api/analytics/bad-days?page=1&pageSize=25' \
  > /dev/null

# Should be <1 second if cached
```

**3. Check Redis Memory:**
```bash
redis-cli INFO memory | grep used_memory_human

# Alert if approaching maxmemory
```

### Weekly Tasks

**1. Analyze Slow Queries:**
```bash
# Check database slow query log
sudo tail -100 /var/log/mysql/slow-query.log

# Look for queries taking >5 seconds
```

**2. Review Cache Hit Rate:**
```bash
redis-cli INFO stats | grep keyspace

# Target: >80% hit rate
```

**3. Check Error Logs:**
```bash
# Application errors
sudo journalctl -u safedriveapi-prod -p err -n 50

# Redis errors
sudo journalctl -u redis-server -p err -n 50
```

### Monthly Tasks

**1. Database Maintenance:**
```sql
-- Analyze tables to update statistics
ANALYZE TABLE trip, raw_sensor_data, location, unsafe_behaviour;

-- Check index health
SHOW INDEX FROM trip;
```

**2. Review Index Usage:**
```sql
-- Which indexes are unused?
SELECT * FROM sys.schema_unused_indexes;

-- Which indexes are rarely used?
SELECT * FROM sys.schema_index_statistics 
WHERE table_schema = 'drive_safe_db' 
ORDER BY rows_selected;
```

**3. Capacity Planning:**
```bash
# Check database size growth
mysql -e "SELECT table_name, 
  ROUND(data_length/1024/1024, 2) AS 'Data(MB)',
  ROUND(index_length/1024/1024, 2) AS 'Index(MB)'
FROM information_schema.tables
WHERE table_schema = 'drive_safe_db'
ORDER BY data_length DESC;"

# Predict when to implement Phase 2 (trip_summary table)
# Trigger: >2,000 trips
```

### Cache Best Practices

**1. TTL Selection:**
```python
# Data that changes rarely: Long TTL
FLEET_CONFIG_TTL = 1800  # 30 minutes

# Analytics/aggregations: Medium TTL
ANALYTICS_TTL = 300  # 5 minutes

# Real-time data: Short TTL or no cache
LIVE_LOCATION_TTL = 10  # 10 seconds
```

**2. Cache Key Naming:**
```python
# Good: Descriptive, versioned, includes parameters
"bad_days:v1:cohort_abc:page_1:size_25"

# Bad: Generic, no version, missing parameters
"analytics:data"
```

**3. Cache Invalidation:**
```python
# Invalidate related caches when data changes
def update_trip(trip_id: UUID, data: dict):
    # Update database
    db.query(Trip).filter(Trip.id == trip_id).update(data)
    db.commit()
    
    # Invalidate relevant caches
    cache_invalidate_pattern(f"bad_days:*")
    cache_invalidate_pattern(f"leaderboard:*")
    cache_invalidate_pattern(f"driver_kpis:*")
```

**4. Graceful Degradation:**
Always ensure app works without cache:
```python
def get_data():
    # Try cache
    cached = cache_get(key)
    if cached:
        return cached
    
    # Fallback to database
    data = expensive_query()
    
    # Try to cache (don't fail if Redis is down)
    cache_set(key, data, ttl)
    
    return data
```

### When to Scale to Phase 2

**Triggers:**
- Trip count > 2,000
- Uncached queries consistently > 10 seconds
- Cache hit rate < 70%
- Users complaining about slow initial loads

**Phase 2: Pre-aggregated Tables**

```sql
-- Create summary table
CREATE TABLE trip_summary (
    trip_id BINARY(16) PRIMARY KEY,
    driverProfileId BINARY(16),
    start_date DATE,
    total_distance_m DOUBLE,
    unsafe_count INT,
    ubpk DOUBLE,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_driver_date (driverProfileId, start_date)
);

-- Create trigger to auto-populate
DELIMITER //
CREATE TRIGGER after_trip_insert 
AFTER INSERT ON trip
FOR EACH ROW
BEGIN
    INSERT INTO trip_summary (trip_id, driverProfileId, start_date, ...)
    SELECT NEW.id, NEW.driverProfileId, ...;
END//
DELIMITER ;
```

### When to Scale to Phase 3

**Triggers:**
- Driver count > 10,000
- Even cached responses feel slow (>500ms)
- High traffic during peak hours
- Multiple analytics requests simultaneously

**Phase 3: Background Jobs**

```python
# Use Celery for scheduled tasks
from celery import Celery
from celery.schedules import crontab

@celery.task
def precompute_all_analytics():
    """Run every 15 minutes"""
    for cohort in get_all_cohorts():
        result = compute_bad_days(cohort)
        cache_set(f"bad_days:{cohort.id}", result, ttl=1800)

# Schedule
celery.conf.beat_schedule = {
    'precompute-analytics': {
        'task': 'tasks.precompute_all_analytics',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
```

### Security Considerations

**1. Cache Poisoning:**
```python
# Don't cache sensitive data
if current_user.role == Role.ADMIN:
    # Don't cache admin-only results
    return compute_result()  # Skip cache

# Separate cache keys by role
cache_key = generate_cache_key(
    "bad_days",
    role=current_user.role,  # ← Include role in key
    cohort=cohort_ids,
)
```

**2. Redis Security:**
```bash
# Only accept local connections
bind 127.0.0.1 ::1

# Require password (optional)
requirepass your_secure_password_here

# Disable dangerous commands
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG ""
```

**3. API Key Security:**
```python
# Always hash API keys in database
api_key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

# Never log full API keys
logger.info(f"Auth with key: {raw_key[:4]}****")  # Only first 4 chars
```

### Common Pitfalls to Avoid

**1. Over-caching:**
```python
# ❌ BAD: Caching for too long
CACHE_TTL = 86400  # 24 hours - data might be stale!

# ✅ GOOD: Appropriate TTL for data freshness
CACHE_TTL = 300  # 5 minutes - fresh enough
```

**2. Under-indexing:**
```sql
-- ❌ BAD: No indexes on foreign keys
CREATE TABLE raw_sensor_data (
    id BINARY(16),
    trip_id BINARY(16),  -- No index!
    ...
);

-- ✅ GOOD: Index on foreign keys
CREATE TABLE raw_sensor_data (
    id BINARY(16),
    trip_id BINARY(16),
    ...,
    INDEX idx_trip_id (trip_id)
);
```

**3. Over-indexing:**
```sql
-- ❌ BAD: Too many indexes slow down writes
CREATE INDEX idx1 ON trip(start_time);
CREATE INDEX idx2 ON trip(driverProfileId);
CREATE INDEX idx3 ON trip(start_time, driverProfileId);
CREATE INDEX idx4 ON trip(driverProfileId, start_time);
-- Last two are redundant!

-- ✅ GOOD: Minimal necessary indexes
CREATE INDEX idx_start_time ON trip(start_time);
CREATE INDEX idx_composite ON trip(driverProfileId, start_time);
```

**4. Ignoring Cache Misses:**
```python
# ❌ BAD: Always trying cache first even if it always misses
def get_live_location():
    cached = cache_get("location")  # Always None!
    if cached:
        return cached
    return query_gps_device()

# ✅ GOOD: Don't cache frequently changing data
def get_live_location():
    return query_gps_device()  # Skip cache entirely
```

**5. Not Monitoring:**
```python
# ❌ BAD: No visibility into performance
def slow_function():
    result = expensive_query()
    return result

# ✅ GOOD: Log performance metrics
import time

def slow_function():
    start = time.time()
    result = expensive_query()
    elapsed = time.time() - start
    logger.info(f"Query took {elapsed:.2f}s")
    return result
```

---

## Conclusion

### What We Learned

1. **CORS is critical** for web clients to access APIs
2. **Query structure matters more than indexes** - aggregate before joining
3. **Caching provides exponential speedups** for read-heavy workloads
4. **Graceful degradation** ensures reliability when cache is unavailable
5. **Monitor everything** - you can't optimize what you don't measure

### Key Takeaways

- **Start with measurement:** Use `EXPLAIN`, logs, and timing
- **Optimize the bottleneck:** Don't guess, measure and target the slowest part
- **Layer optimizations:** Database → Caching → Pre-computation
- **Plan for scale:** Know when to move to next phase
- **Keep it simple:** Don't over-engineer for traffic you don't have yet

### Performance Achievement

From **165 seconds** to **79 milliseconds** - a **2,088x improvement**:
- Users get instant results
- Server load reduced
- Dashboard feels responsive
- Scalable to 10,000+ drivers

### Next Steps

1. **Monitor** cache hit rates and response times
2. **Iterate** on TTL values based on usage patterns
3. **Prepare** Phase 2 when trips exceed 2,000
4. **Document** any new optimizations in this guide

---

## Appendix A: Quick Reference Commands

### Redis Commands
```bash
# Connection
redis-cli ping
redis-cli INFO

# Keys
redis-cli KEYS "pattern*"
redis-cli GET key_name
redis-cli DEL key_name
redis-cli TTL key_name

# Stats
redis-cli INFO stats
redis-cli INFO memory

# Monitoring
redis-cli MONITOR
```

### MySQL Commands
```sql
-- Index management
SHOW INDEXES FROM table_name;
CREATE INDEX idx_name ON table(column);
DROP INDEX idx_name ON table;

-- Query analysis
EXPLAIN SELECT ...;
SHOW PROFILE FOR QUERY 1;

-- Performance
SHOW PROCESSLIST;
SHOW STATUS LIKE 'Slow_queries';
```

### Service Management
```bash
# Status
sudo systemctl status service_name

# Start/Stop/Restart
sudo systemctl start service_name
sudo systemctl stop service_name
sudo systemctl restart service_name

# Logs
sudo journalctl -u service_name -f
sudo journalctl -u service_name -n 100
```

### Testing Performance
```bash
# Single request timing
time curl -s URL > /dev/null

# Multiple requests
for i in {1..10}; do
  time curl -s URL > /dev/null
done

# With authentication
time curl -s -H 'X-API-Key: KEY' URL > /dev/null
```

## Appendix B: Configuration Files

### Redis Config Snippet
```bash
# /etc/redis/redis.conf
bind 127.0.0.1 ::1
port 6379
maxmemory 268435456
maxmemory-policy allkeys-lru
supervised systemd
```

### Nginx Config Snippet
```nginx
# /etc/nginx/sites-available/api.safedriveafrica.com
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_read_timeout 300s;
    
    add_header 'Access-Control-Allow-Origin' 'https://datahub.safedriveafrica.com' always;
    add_header 'Access-Control-Allow-Credentials' 'true' always;
}
```

### Systemd Service Snippet
```ini
# /etc/systemd/system/safedriveapi-prod.service
[Service]
WorkingDirectory=/var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com
ExecStart=/var/www/.../venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker --timeout 120 main:app
```

---

## Appendix C: Troubleshooting Checklist

### Slow Queries
- [ ] Check if indexes exist (`SHOW INDEXES`)
- [ ] Run `EXPLAIN` on query
- [ ] Verify correct data types in WHERE clauses
- [ ] Check for functions on indexed columns
- [ ] Review N+1 query patterns
- [ ] Consider query restructuring (subqueries)

### Cache Not Working
- [ ] Redis service running (`systemctl status redis-server`)
- [ ] Can connect to Redis (`redis-cli ping`)
- [ ] Check cache keys exist (`redis-cli KEYS "*"`)
- [ ] Verify TTL is set (`redis-cli TTL key`)
- [ ] Check for serialization errors in logs
- [ ] Verify cache key generation is consistent

### Authentication Issues
- [ ] API key exists in database
- [ ] API key hash matches
- [ ] Header syntax correct in curl/code
- [ ] CORS headers present
- [ ] Check application logs for auth errors

### Memory Issues
- [ ] Check Redis memory (`redis-cli INFO memory`)
- [ ] Verify eviction policy (`allkeys-lru`)
- [ ] Check for memory leaks (`ps aux | grep python`)
- [ ] Review cache TTLs (too long?)
- [ ] Consider increasing maxmemory

---

**Document Version:** 1.0  
**Last Updated:** January 15, 2026  
**Next Review:** February 15, 2026  
**Maintainer:** Safe Drive Africa Development Team

---

*This guide is a living document. Please update it when making performance changes or discovering new optimization techniques.*
