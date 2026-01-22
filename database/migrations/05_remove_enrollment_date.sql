-- Migration: Remove enrollment_date column from raw_data
-- Date: 2026-01-21
-- Reason: enrollment_date is not needed for model training

USE dropout_prediction_db;

-- Remove enrollment_date column
ALTER TABLE raw_data DROP COLUMN IF EXISTS enrollment_date;

-- Verify column removed
SHOW COLUMNS FROM raw_data LIKE 'enrollment_date';
