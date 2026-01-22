-- Migration 07: Add course_stats_benchmarks table for Option 2 implementation
-- Store course-level statistics to enable comparative features

USE dropout_prediction_db;

-- =====================================================
-- Table: course_stats_benchmarks
-- Lưu course-level benchmarks từ Advanced Stats APIs
-- =====================================================
CREATE TABLE IF NOT EXISTS course_stats_benchmarks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    course_id VARCHAR(255) NOT NULL,
    
    -- Activity benchmarks
    activity_avg_score DECIMAL(5,2) DEFAULT 0 COMMENT 'Course avg activity score',
    activity_total_activities INT DEFAULT 0 COMMENT 'Total course activities',
    activity_avg_per_user DECIMAL(5,2) DEFAULT 0 COMMENT 'Avg activities per user',
    
    -- Assessment benchmarks  
    assessment_avg_score DECIMAL(5,2) DEFAULT 0 COMMENT 'Course avg assessment score',
    assessment_avg_attempts DECIMAL(5,2) DEFAULT 0 COMMENT 'Avg attempts per assessment',
    assessment_pass_rate DECIMAL(5,2) DEFAULT 0 COMMENT 'Overall pass rate',
    
    -- Progress benchmarks
    progress_avg_completion DECIMAL(5,2) DEFAULT 0 COMMENT 'Avg completion rate',
    progress_median_completion DECIMAL(5,2) DEFAULT 0 COMMENT 'Median completion rate',
    progress_completion_rate DECIMAL(5,2) DEFAULT 0 COMMENT '% students who completed',
    
    -- Video benchmarks
    video_avg_completion DECIMAL(5,2) DEFAULT 0 COMMENT 'Avg video completion',
    video_avg_watch_time INT DEFAULT 0 COMMENT 'Avg watch time (seconds)',
    
    -- Discussion benchmarks
    discussion_avg_interactions DECIMAL(5,2) DEFAULT 0 COMMENT 'Avg discussion interactions',
    discussion_participation_rate DECIMAL(5,2) DEFAULT 0 COMMENT '% students with discussions',
    
    -- Metadata
    total_students INT DEFAULT 0 COMMENT 'Total enrolled students',
    active_students INT DEFAULT 0 COMMENT 'Active students',
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'When benchmarks were fetched',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_course (course_id),
    INDEX idx_course (course_id),
    INDEX idx_fetched (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Course-level benchmarks for comparative features';

-- =====================================================
-- Add comparative columns to raw_data
-- =====================================================
ALTER TABLE raw_data
-- Relative performance features
ADD COLUMN relative_to_course_problem_score DECIMAL(5,2) COMMENT 'Problem score vs course avg',
ADD COLUMN relative_to_course_completion DECIMAL(5,2) COMMENT 'Completion vs course avg',
ADD COLUMN relative_to_course_video_completion DECIMAL(5,2) COMMENT 'Video completion vs course avg',
ADD COLUMN relative_to_course_discussion INT COMMENT 'Discussion interactions vs course avg',

-- Percentile/ranking features  
ADD COLUMN performance_percentile DECIMAL(5,2) COMMENT 'Overall performance percentile (0-100)',
ADD COLUMN is_below_course_average TINYINT(1) DEFAULT 0 COMMENT 'Below course average flag',
ADD COLUMN is_top_performer TINYINT(1) DEFAULT 0 COMMENT 'Top 25% performer flag',
ADD COLUMN is_bottom_performer TINYINT(1) DEFAULT 0 COMMENT 'Bottom 25% performer flag';

-- Verification
SELECT 'Migration 07 completed successfully' AS status;
SHOW TABLES LIKE '%benchmark%';
