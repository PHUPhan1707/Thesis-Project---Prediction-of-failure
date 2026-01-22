-- Migration 06: Create tables for additional API data sources
-- Activity Statistics, Assessment Details, Progress Tracking

USE dropout_prediction_db;

-- =====================================================
-- Table 1: activity_stats
-- Lưu chi tiết hoạt động của từng user từ Activity Stats API
-- =====================================================
CREATE TABLE IF NOT EXISTS activity_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    
    -- Problem/Assignment activities
    problem_total_attempts INT DEFAULT 0 COMMENT 'Total problem attempts',
    problem_total_correct INT DEFAULT 0 COMMENT 'Total correct problems',
    problem_avg_score DECIMAL(5,2) DEFAULT 0 COMMENT 'Average problem score',
    problem_unique_problems INT DEFAULT 0 COMMENT 'Unique problems attempted',
    
    -- Video activities  
    video_total_views INT DEFAULT 0 COMMENT 'Total video views',
    video_unique_videos INT DEFAULT 0 COMMENT 'Unique videos watched',
    video_avg_watch_time INT DEFAULT 0 COMMENT 'Average watch time (seconds)',
    
    -- Discussion activities
    discussion_posts_count INT DEFAULT 0 COMMENT 'Discussion posts',
    discussion_replies_count INT DEFAULT 0 COMMENT 'Discussion replies',
    
    -- Time-based patterns
    late_night_activities INT DEFAULT 0 COMMENT 'Activities after 22:00',
    weekend_activities INT DEFAULT 0 COMMENT 'Weekend activities',
    total_activities INT DEFAULT 0 COMMENT 'Total activities',
    
    -- Consistency metrics
    active_days_count INT DEFAULT 0 COMMENT 'Number of active days',
    max_gap_days INT DEFAULT 0 COMMENT 'Longest inactive gap',
    activity_variance DECIMAL(10,2) DEFAULT 0 COMMENT 'Activity variance',
    
    -- Timestamps
    first_activity_date DATETIME COMMENT 'First activity date',
    last_activity_date DATETIME COMMENT 'Last activity date',
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Data fetch time',
    
    UNIQUE KEY unique_user_course (user_id, course_id),
    INDEX idx_course (course_id),
    INDEX idx_user (user_id),
    INDEX idx_fetched (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Activity statistics from Activity Stats API';

-- =====================================================
-- Table 2: assessment_details
-- Lưu chi tiết từng assignment/quiz từ Assessment Stats API
-- =====================================================
CREATE TABLE IF NOT EXISTS assessment_details (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    assessment_id VARCHAR(500) NOT NULL COMMENT 'Block ID of assessment',
    assessment_type VARCHAR(50) COMMENT 'quiz, exam, assignment',
    
    -- Attempt tracking
    total_attempts INT DEFAULT 0 COMMENT 'Total attempts',
    first_attempt_score DECIMAL(5,2) COMMENT 'First attempt score',
    best_score DECIMAL(5,2) COMMENT 'Best score achieved',
    latest_score DECIMAL(5,2) COMMENT 'Latest score',
    
    -- Learning indicators
    improvement_rate DECIMAL(5,2) DEFAULT 0 COMMENT '(best - first) / first * 100',
    attempts_to_pass INT COMMENT 'Attempts needed to pass',
    
    -- Time spent
    total_time_spent INT DEFAULT 0 COMMENT 'Total time in seconds',
    avg_time_per_attempt INT DEFAULT 0 COMMENT 'Average time per attempt',
    
    -- Timestamps
    first_attempt_date DATETIME COMMENT 'First attempt date',
    last_attempt_date DATETIME COMMENT 'Last attempt date',
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Data fetch time',
    
    UNIQUE KEY unique_user_assessment (user_id, course_id, assessment_id),
    INDEX idx_course (course_id),
    INDEX idx_user (user_id),
    INDEX idx_assessment (assessment_id),
    INDEX idx_fetched (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Assessment details from Assessment Stats API';

-- =====================================================
-- Table 3: progress_tracking
-- Lưu tiến độ theo thời gian từ Progress Stats API
-- =====================================================
CREATE TABLE IF NOT EXISTS progress_tracking (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    tracked_week INT NOT NULL COMMENT 'Week number (1-16)',
    
    -- Progress metrics
    completion_percent DECIMAL(5,2) DEFAULT 0 COMMENT 'Completion percentage',
    completed_blocks INT DEFAULT 0 COMMENT 'Completed blocks',
    total_blocks INT DEFAULT 0 COMMENT 'Total blocks',
    
    -- Weekly velocity
    blocks_completed_this_week INT DEFAULT 0 COMMENT 'Blocks completed this week',
    velocity DECIMAL(5,2) DEFAULT 0 COMMENT 'Blocks per week',
    
    -- Timestamps
    week_start_date DATE COMMENT 'Week start date',
    week_end_date DATE COMMENT 'Week end date',
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Record time',
    
    UNIQUE KEY unique_user_week (user_id, course_id, tracked_week),
    INDEX idx_course (course_id),
    INDEX idx_user (user_id),
    INDEX idx_week (tracked_week),
    INDEX idx_recorded (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Progress tracking from Progress Stats API';

-- =====================================================
-- Alter raw_data to add aggregated features
-- Note: IF NOT EXISTS not supported in MySQL 8.0 ALTER TABLE
-- Run only once or check if columns exist first
-- =====================================================
ALTER TABLE raw_data 
-- Activity features (from activity_stats)
ADD COLUMN problem_attempts INT DEFAULT 0 COMMENT 'Total problem attempts',
ADD COLUMN problem_avg_score DECIMAL(5,2) DEFAULT 0 COMMENT 'Average problem score',
ADD COLUMN problem_success_rate DECIMAL(5,2) DEFAULT 0 COMMENT 'Problem success rate',
ADD COLUMN video_views INT DEFAULT 0 COMMENT 'Total video views',
ADD COLUMN late_night_ratio DECIMAL(5,2) DEFAULT 0 COMMENT 'Late night activity ratio',
ADD COLUMN weekend_ratio DECIMAL(5,2) DEFAULT 0 COMMENT 'Weekend activity ratio',
ADD COLUMN activity_consistency DECIMAL(5,2) DEFAULT 0 COMMENT 'Activity consistency score',
ADD COLUMN max_inactive_gap_days INT DEFAULT 0 COMMENT 'Max inactive gap',
-- Assessment features (from assessment_details)
ADD COLUMN assessment_attempts_avg DECIMAL(5,2) DEFAULT 0 COMMENT 'Average attempts per assessment',
ADD COLUMN assessment_improvement_rate DECIMAL(5,2) DEFAULT 0 COMMENT 'Average improvement rate',
ADD COLUMN first_attempt_success_rate DECIMAL(5,2) DEFAULT 0 COMMENT 'First attempt success rate',
ADD COLUMN struggling_assessments_count INT DEFAULT 0 COMMENT 'Number of struggling assessments',
-- Progress features (from progress_tracking)
ADD COLUMN progress_velocity DECIMAL(5,2) DEFAULT 0 COMMENT 'Progress velocity (% per week)',
ADD COLUMN progress_acceleration DECIMAL(5,2) DEFAULT 0 COMMENT 'Progress acceleration',
ADD COLUMN weeks_to_complete_estimate DECIMAL(5,2) COMMENT 'Estimated weeks to complete';

-- Verification
SELECT 'Migration 06 completed successfully' AS status;
SHOW TABLES LIKE '%stats%';
SHOW TABLES LIKE '%assessment%';
SHOW TABLES LIKE '%progress%';
