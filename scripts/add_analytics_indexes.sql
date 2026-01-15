-- Critical indexes for analytics endpoints performance (MySQL version)
-- Run this on the production database to optimize bad-days query from 165s to <3s
-- Note: Some indexes may already exist or be part of foreign key constraints

-- Trip table indexes for time-based queries and joins
DROP INDEX IF EXISTS idx_trip_start_time ON trip;
CREATE INDEX idx_trip_start_time ON trip(start_time);

DROP INDEX IF EXISTS idx_trip_driver_start_time ON trip;
CREATE INDEX idx_trip_driver_start_time ON trip(driverProfileId, start_time);

DROP INDEX IF EXISTS idx_trip_driver_time_composite ON trip;
CREATE INDEX idx_trip_driver_time_composite ON trip(driverProfileId, start_time, id);

-- RawSensorData indexes for joining with trips and locations
-- Note: These columns may already have indexes from foreign key constraints
-- Skip DROP to avoid foreign key constraint errors, CREATE will fail safely if index exists
CREATE INDEX idx_raw_sensor_data_trip_id ON raw_sensor_data(trip_id);
CREATE INDEX idx_raw_sensor_data_location_id ON raw_sensor_data(location_id);

-- Location indexes for distance aggregation  
-- Primary key already indexed, this will fail if id is PK (safe to ignore)
CREATE INDEX idx_location_id ON location(id);

-- UnsafeBehaviour indexes for counting unsafe behaviors per trip
-- May already exist from foreign key constraint
CREATE INDEX idx_unsafe_behaviour_trip_id ON unsafe_behaviour(trip_id);

-- Verify indexes were created (MySQL version)
SELECT 
    TABLE_NAME, 
    INDEX_NAME, 
    COLUMN_NAME,
    SEQ_IN_INDEX
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'drive_safe_db'
  AND TABLE_NAME IN ('trip', 'raw_sensor_data', 'location', 'unsafe_behaviour')
  AND INDEX_NAME LIKE 'idx_%'
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
