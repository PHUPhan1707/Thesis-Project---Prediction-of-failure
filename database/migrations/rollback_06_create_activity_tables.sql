-- Rollback Migration 06: Remove activity tables and columns

USE dropout_prediction_db;

-- Drop columns from raw_data
ALTER TABLE raw_data 
DROP COLUMN IF EXISTS problem_attempts,
DROP COLUMN IF EXISTS problem_avg_score,
DROP COLUMN IF EXISTS problem_success_rate,
DROP COLUMN IF EXISTS video_views,
DROP COLUMN IF EXISTS late_night_ratio,
DROP COLUMN IF EXISTS weekend_ratio,
DROP COLUMN IF EXISTS activity_consistency,
DROP COLUMN IF EXISTS max_inactive_gap_days,
DROP COLUMN IF EXISTS assessment_attempts_avg,
DROP COLUMN IF EXISTS assessment_improvement_rate,
DROP COLUMN IF EXISTS first_attempt_success_rate,
DROP COLUMN IF EXISTS struggling_assessments_count,
DROP COLUMN IF EXISTS progress_velocity,
DROP COLUMN IF EXISTS progress_acceleration,
DROP COLUMN IF EXISTS weeks_to_complete_estimate;

-- Drop tables
DROP TABLE IF EXISTS progress_tracking;
DROP TABLE IF EXISTS assessment_details;
DROP TABLE IF EXISTS activity_stats;

SELECT 'Rollback 06 completed successfully' AS status;
