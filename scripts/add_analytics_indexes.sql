-- Critical indexes for analytics endpoints performance
-- Run this on the production database to optimize bad-days query from 165s to <3s

-- Trip table indexes for time-based queries and joins
CREATE INDEX IF NOT EXISTS idx_trip_start_time ON trip(start_time);
CREATE INDEX IF NOT EXISTS idx_trip_driver_start_time ON trip(driverProfileId, start_time);

-- RawSensorData indexes for joining with trips and locations
CREATE INDEX IF NOT EXISTS idx_raw_sensor_data_trip_id ON raw_sensor_data(trip_id);
CREATE INDEX IF NOT EXISTS idx_raw_sensor_data_location_id ON raw_sensor_data(location_id);

-- Location indexes for distance aggregation
CREATE INDEX IF NOT EXISTS idx_location_id ON location(id);

-- UnsafeBehaviour indexes for counting unsafe behaviors per trip
CREATE INDEX IF NOT EXISTS idx_unsafe_behaviour_trip_id ON unsafe_behaviour(trip_id);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_trip_driver_time_composite ON trip(driverProfileId, start_time, id);

-- Verify indexes were created
SELECT 
    tablename, 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename IN ('trip', 'raw_sensor_data', 'location', 'unsafe_behaviour')
ORDER BY tablename, indexname;
