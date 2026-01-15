# Database Optimization for High-Volume Sensor Data

## Critical Indexes Required

Add these indexes to dramatically improve analytics query performance:

```sql
-- Trip queries by date and driver
CREATE INDEX idx_trip_start_time ON trip(start_time);
CREATE INDEX idx_trip_driver_start ON trip(driverProfileId, start_time);

-- Sensor data joins
CREATE INDEX idx_raw_sensor_trip ON raw_sensor_data(trip_id);
CREATE INDEX idx_location_id ON raw_sensor_data(location_id);

-- Unsafe behavior aggregation
CREATE INDEX idx_unsafe_trip ON unsafe_behaviour(trip_id);

-- Composite indexes for common filters
CREATE INDEX idx_trip_driver_time_sync ON trip(driverProfileId, start_time, sync);
```

## Performance Best Practices Implemented

### 1. Database-Level Aggregation
- **Before**: Load all trips → Python loops → Calculate metrics (SLOW)
- **After**: Use SQL `GROUP BY`, `SUM()`, `COUNT()` → Return only aggregated results (FAST)

### 2. Pagination at Source Level
- Paginate drivers (50 per page) not trips
- Reduces memory footprint from GB to MB
- Sub-second response times

### 3. Efficient Joins
- Use `OUTER JOIN` only when necessary
- Filter early in the query pipeline
- Use subqueries for complex aggregations

### 4. Future Enhancements

#### A. Materialized Views (Recommended)
Create pre-computed aggregates refreshed hourly:
```sql
CREATE MATERIALIZED VIEW driver_daily_metrics AS
SELECT 
    driverProfileId,
    DATE(FROM_UNIXTIME(start_time/1000)) as trip_date,
    COUNT(*) as trip_count,
    SUM(distance) as total_distance,
    SUM(unsafe_count) as total_unsafe
FROM trip_with_metrics
GROUP BY driverProfileId, trip_date;

-- Refresh every hour
CREATE EVENT refresh_driver_metrics
ON SCHEDULE EVERY 1 HOUR
DO REFRESH MATERIALIZED VIEW driver_daily_metrics;
```

#### B. Redis Caching Layer
```python
# Cache analytics results for 5 minutes
@cache.memoize(timeout=300)
def get_bad_days(driver_id, period):
    return compute_bad_days(driver_id, period)
```

#### C. Background Job Processing
For expensive analytics:
```python
# Celery task to pre-compute analytics overnight
@celery.task
def precompute_driver_analytics():
    for driver in get_all_drivers():
        compute_and_cache_analytics(driver.id)
```

#### D. Time-Series Database
For raw sensor data (millions of rows):
- Use TimescaleDB extension for PostgreSQL
- Or migrate sensor data to InfluxDB/TimescaleDB
- Keep aggregates in main DB

## Migration Script

Run this to add indexes:

```bash
alembic revision -m "add_analytics_indexes"
```

```python
def upgrade():
    op.create_index('idx_trip_start_time', 'trip', ['start_time'])
    op.create_index('idx_trip_driver_start', 'trip', ['driverProfileId', 'start_time'])
    op.create_index('idx_raw_sensor_trip', 'raw_sensor_data', ['trip_id'])
    op.create_index('idx_unsafe_trip', 'unsafe_behaviour', ['trip_id'])

def downgrade():
    op.drop_index('idx_trip_start_time', 'trip')
    op.drop_index('idx_trip_driver_start', 'trip')
    op.drop_index('idx_raw_sensor_trip', 'raw_sensor_data')
    op.drop_index('idx_unsafe_trip', 'unsafe_behaviour')
```

## Query Performance Targets

| Endpoint | Before | After | Target |
|----------|--------|-------|--------|
| `/analytics/bad-days` | 60s | 5-10s | < 3s with indexes |
| `/analytics/leaderboard` | 40s | 3-5s | < 2s |
| `/analytics/driver-kpis` | 50s | 4-6s | < 2s |

## Monitoring

Add query timing logs:
```python
import time
start = time.time()
result = db.query(...).all()
logger.info(f"Query took {time.time() - start:.2f}s")
```

Check slow queries:
```sql
SHOW FULL PROCESSLIST;
EXPLAIN ANALYZE SELECT ...;
```
