-- Migration 08: Remove H5P early activity features from raw_data table
-- Xóa các cột liên quan đến H5P early activity features

USE dropout_prediction_db;

-- =====================================================
-- Remove H5P early activity features columns
-- Note: MySQL doesn't support DROP COLUMN IF EXISTS in single statement
-- Each column must be dropped in a separate ALTER TABLE statement
-- =====================================================

-- Drop h5p_first_activity_date
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_first_activity_date;

-- Drop 2 weeks features
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_attempts_2weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_avg_score_2weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_max_score_2weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_min_score_2weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_pass_rate_2weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_fail_rate_2weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_time_spent_2weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_unique_content_2weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_activity_frequency_2weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_completion_rate_2weeks;

-- Drop 3 weeks features
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_attempts_3weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_avg_score_3weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_max_score_3weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_min_score_3weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_pass_rate_3weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_fail_rate_3weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_time_spent_3weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_unique_content_3weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_activity_frequency_3weeks;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_early_completion_rate_3weeks;

-- Drop other early features
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_max_inactive_gap_days_early;
ALTER TABLE raw_data DROP COLUMN IF EXISTS h5p_activity_consistency_early;

-- Verification
SELECT 'Migration 08 completed successfully - H5P early features removed' AS status;
SHOW COLUMNS FROM raw_data LIKE 'h5p_early%';
SHOW COLUMNS FROM raw_data LIKE 'h5p_first%';
SHOW COLUMNS FROM raw_data LIKE '%inactive_gap%';
SHOW COLUMNS FROM raw_data LIKE '%activity_consistency%';

