-- Rollback: Add back enrollment_date column to raw_data
-- Date: 2026-01-21

USE dropout_prediction_db;

-- Add enrollment_date column back
ALTER TABLE raw_data 
ADD COLUMN enrollment_date DATETIME AFTER course_id;

-- Verify column added
SHOW COLUMNS FROM raw_data LIKE 'enrollment_date';
