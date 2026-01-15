-- Critical indexes for analytics endpoints performance (MySQL version)
-- Run this on the production database to optimize bad-days query from 165s to <3s

-- Trip table indexes for time-based queries and joins
CREATE INDEX idx_trip_start_time ON trip(start_time);
CREATE INDEX idx_trip_driver_start_time ON trip(driverProfileId, start_time);

-- RawSensorData indexes for joining with trips and locations
CREATE INDEX idx_raw_sensor_data_trip_id ON raw_sensor_data(trip_id);
CREATE INDEX idx_raw_sensor_data_location_id ON raw_sensor_data(location_id);

-- Location indexes for distance aggregation
CREATE INDEX idx_location_id ON location(id);

-- UnsafeBehaviour indexes for counting unsafe behaviors per trip
CREATE INDEX idx_unsafe_behaviour_trip_id ON unsafe_behaviour(trip_id);

-- Composite indexes for common query patterns
CREATE INDEX idx_trip_driver_time_composite ON trip(driverProfileId, start_time, id);

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
