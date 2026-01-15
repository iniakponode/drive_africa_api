# Analytics Performance Fix Deployment Guide

## Issue Summary
- **Problem**: `/api/analytics/bad-days` returns all zeros and takes 165+ seconds
- **Root Causes**: 
  1. Incomplete implementation (hardcoded zeros)
  2. Missing database indexes on critical columns
  
## Solution
1. **Code fix**: Complete bad days calculation logic
2. **Database indexes**: Add 7 critical indexes to optimize joins and aggregations

## Deployment Steps

### Step 1: Deploy Code Fix
```bash
# On production server
cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com
git pull origin main  # or deploy your updated code

# Restart service
sudo systemctl restart safedriveapi-prod
sudo systemctl status safedriveapi-prod
```

### Step 2: Apply Database Indexes
**CRITICAL**: Run during low-traffic period as index creation locks tables

```bash
# Connect to your MySQL/PostgreSQL database
# For MySQL:
mysql -u your_user -p drive_safe_db < scripts/add_analytics_indexes.sql

# For PostgreSQL:
psql -U your_user -d drive_safe_db -f scripts/add_analytics_indexes.sql
```

**Note**: If using PostgreSQL, the SQL is already compatible. If using MySQL, replace:
- `CREATE INDEX IF NOT EXISTS` with `CREATE INDEX` (remove IF NOT EXISTS)
- Remove the pg_indexes verification query at the end

### Step 3: Verify Performance
Test the endpoint directly on backend:

```bash
time curl -X GET "http://127.0.0.1:8000/api/analytics/bad-days?page=1&pageSize=50" \
  -H "X-API-Key: 02QDlql_JlwQXjdcj-Awsw8gBPs06-6JEP-aasDKf38" \
  -H "Content-Type: application/json"
```

**Expected Results**:
- **Response time**: < 3 seconds (down from 165s)
- **Data accuracy**: Real bad_days counts (not zeros)
- **Proper thresholds**: Non-zero threshold values

### Step 4: Test Through Nginx
```bash
curl -X GET "https://api.safedriveafrica.com/api/analytics/bad-days?page=1&pageSize=50" \
  -H "X-API-Key: 02QDlql_JlwQXjdcj-Awsw8gBPs06-6JEP-aasDKf38"
```

Should return 200 OK in < 5 seconds.

## Index Creation Impact

| Table | Index | Purpose | Est. Performance Gain |
|-------|-------|---------|----------------------|
| trip | idx_trip_start_time | Filter by date range | 50x faster |
| trip | idx_trip_driver_start_time | Driver-time queries | 100x faster |
| raw_sensor_data | idx_raw_sensor_data_trip_id | Join with trips | 200x faster |
| location | idx_location_id | Distance aggregation | 50x faster |
| unsafe_behaviour | idx_unsafe_behaviour_trip_id | Count unsafe per trip | 100x faster |

**Combined Impact**: 165s → <3s (55x improvement)

## Monitoring

After deployment, monitor:
1. Response times via application logs
2. Database query slow log for queries >1s
3. CORS headers still present in responses
4. Web client dashboard loads without 504 errors

## Rollback Plan

If issues occur:

**Code Rollback**:
```bash
cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com
git checkout <previous-commit-hash>
sudo systemctl restart safedriveapi-prod
```

**Index Removal** (if indexes cause problems):
```sql
DROP INDEX IF EXISTS idx_trip_start_time;
DROP INDEX IF EXISTS idx_trip_driver_start_time;
DROP INDEX IF EXISTS idx_raw_sensor_data_trip_id;
DROP INDEX IF EXISTS idx_raw_sensor_data_location_id;
DROP INDEX IF EXISTS idx_location_id;
DROP INDEX IF EXISTS idx_unsafe_behaviour_trip_id;
DROP INDEX IF EXISTS idx_trip_driver_time_composite;
```

## Next Steps

After successful deployment:
1. Update web client to use pagination (`?page=1&pageSize=50`)
2. Consider materialized views for aggregated analytics (future optimization)
3. Add Redis caching for frequently accessed driver cohorts
4. Monitor index usage and adjust as needed
