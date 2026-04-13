-- Migration 09: Remove unused benchmark columns that are never populated
-- Drops legacy fields from course_stats_benchmarks to keep schema lean

USE dropout_prediction_db;

-- Each column is dropped individually because MySQL requires separate statements
ALTER TABLE course_stats_benchmarks DROP COLUMN IF EXISTS progress_median_completion;
ALTER TABLE course_stats_benchmarks DROP COLUMN IF EXISTS progress_completion_rate;
ALTER TABLE course_stats_benchmarks DROP COLUMN IF EXISTS video_avg_completion;
ALTER TABLE course_stats_benchmarks DROP COLUMN IF EXISTS video_avg_watch_time;
ALTER TABLE course_stats_benchmarks DROP COLUMN IF EXISTS discussion_avg_interactions;
ALTER TABLE course_stats_benchmarks DROP COLUMN IF EXISTS discussion_participation_rate;

-- Verification
SELECT 'Migration 09 completed - unused benchmark columns removed' AS status;
SHOW COLUMNS FROM course_stats_benchmarks;
