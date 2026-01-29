-- Rollback Migration 08: Restore H5P early activity features to raw_data table
-- ⚠️ WARNING: This script will re-add the columns but will NOT restore the data
-- Data will need to be recalculated if needed

USE dropout_prediction_db;

-- =====================================================
-- Re-add H5P early activity features columns
-- =====================================================

ALTER TABLE raw_data 
ADD COLUMN h5p_first_activity_date DATETIME COMMENT 'First H5P activity date',
ADD COLUMN h5p_early_attempts_2weeks INT DEFAULT 0 COMMENT 'Total attempts in first 2 weeks',
ADD COLUMN h5p_early_avg_score_2weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Average percentage in first 2 weeks',
ADD COLUMN h5p_early_max_score_2weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Max percentage in first 2 weeks',
ADD COLUMN h5p_early_min_score_2weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Min percentage in first 2 weeks',
ADD COLUMN h5p_early_pass_rate_2weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Pass rate (>=60%) in first 2 weeks',
ADD COLUMN h5p_early_fail_rate_2weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Fail rate (<60%) in first 2 weeks',
ADD COLUMN h5p_early_time_spent_2weeks INT DEFAULT 0 COMMENT 'Total time spent in seconds in first 2 weeks',
ADD COLUMN h5p_early_unique_content_2weeks INT DEFAULT 0 COMMENT 'Number of unique content items in first 2 weeks',
ADD COLUMN h5p_early_activity_frequency_2weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Activities per day in first 2 weeks',
ADD COLUMN h5p_early_completion_rate_2weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Completion rate (finished>0) in first 2 weeks',
ADD COLUMN h5p_early_attempts_3weeks INT DEFAULT 0 COMMENT 'Total attempts in first 3 weeks',
ADD COLUMN h5p_early_avg_score_3weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Average percentage in first 3 weeks',
ADD COLUMN h5p_early_max_score_3weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Max percentage in first 3 weeks',
ADD COLUMN h5p_early_min_score_3weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Min percentage in first 3 weeks',
ADD COLUMN h5p_early_pass_rate_3weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Pass rate (>=60%) in first 3 weeks',
ADD COLUMN h5p_early_fail_rate_3weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Fail rate (<60%) in first 3 weeks',
ADD COLUMN h5p_early_time_spent_3weeks INT DEFAULT 0 COMMENT 'Total time spent in seconds in first 3 weeks',
ADD COLUMN h5p_early_unique_content_3weeks INT DEFAULT 0 COMMENT 'Number of unique content items in first 3 weeks',
ADD COLUMN h5p_early_activity_frequency_3weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Activities per day in first 3 weeks',
ADD COLUMN h5p_early_completion_rate_3weeks DECIMAL(5,2) DEFAULT 0 COMMENT 'Completion rate (finished>0) in first 3 weeks',
ADD COLUMN h5p_max_inactive_gap_days_early INT DEFAULT 0 COMMENT 'Max gap between activities in first 3 weeks (days)',
ADD COLUMN h5p_activity_consistency_early DECIMAL(5,2) DEFAULT 0 COMMENT 'Activity consistency in early period';

-- Verification
SELECT 'Rollback 08 completed successfully - H5P early features restored' AS status;
SHOW COLUMNS FROM raw_data LIKE 'h5p_early%';
SHOW COLUMNS FROM raw_data LIKE 'h5p_first%';

