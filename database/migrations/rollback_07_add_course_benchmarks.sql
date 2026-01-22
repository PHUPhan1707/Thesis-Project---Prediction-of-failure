-- Rollback Migration 07: Remove course benchmarks

USE dropout_prediction_db;

-- Drop comparative columns from raw_data
ALTER TABLE raw_data
DROP COLUMN IF EXISTS relative_to_course_problem_score,
DROP COLUMN IF EXISTS relative_to_course_completion,
DROP COLUMN IF EXISTS relative_to_course_video_completion,
DROP COLUMN IF EXISTS relative_to_course_discussion,
DROP COLUMN IF EXISTS performance_percentile,
DROP COLUMN IF EXISTS is_below_course_average,
DROP COLUMN IF EXISTS is_top_performer,
DROP COLUMN IF EXISTS is_bottom_performer;

-- Drop table
DROP TABLE IF EXISTS course_stats_benchmarks;

SELECT 'Rollback 07 completed successfully' AS status;
