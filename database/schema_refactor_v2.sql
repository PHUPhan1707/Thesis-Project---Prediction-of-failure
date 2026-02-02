-- ============================================================================
-- REFACTOR: Tách raw_data thành 3 tables riêng biệt
-- Version: 2.0
-- Date: 2026-01-29
-- Purpose: Tách biệt Training data, Student features, và Predictions
-- ============================================================================

-- ============================================================================
-- TABLE 1: STUDENT_FEATURES
-- Chứa features real-time của sinh viên (Production data)
-- Update liên tục khi fetch data mới
-- ============================================================================
CREATE TABLE IF NOT EXISTS student_features (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    
    -- Enrollment features
    enrollment_mode VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    weeks_since_enrollment DECIMAL(5,2) DEFAULT 0,
    
    -- MOOC Grades features
    mooc_grade_percentage DECIMAL(5,2) DEFAULT 0 COMMENT 'MOOC grade percentage (0-100)',
    mooc_letter_grade VARCHAR(5) COMMENT 'MOOC letter grade (Pass or empty string)',
    mooc_is_passed BOOLEAN DEFAULT NULL COMMENT 'MOOC pass/fail status',
    
    -- Progress features
    progress_percent DECIMAL(5,2) DEFAULT 0,
    current_chapter VARCHAR(500) COMMENT 'Current chapter being studied',
    current_section VARCHAR(500) COMMENT 'Current section being studied',
    current_unit VARCHAR(500) COMMENT 'Current unit being studied',
    mooc_completion_rate DECIMAL(5,2) DEFAULT 0 COMMENT 'MOOC completion rate',
    overall_completion DECIMAL(5,2) DEFAULT 0,
    completed_blocks INT DEFAULT 0,
    total_blocks INT DEFAULT 0,
    last_activity DATETIME,
    days_since_last_activity INT DEFAULT 999,
    
    -- Activity features
    access_frequency DECIMAL(10,2) DEFAULT 0,
    active_days INT DEFAULT 0,
    
    -- H5P Scores features
    h5p_total_contents INT DEFAULT 0,
    h5p_completed_contents INT DEFAULT 0,
    h5p_total_score INT DEFAULT 0,
    h5p_total_max_score INT DEFAULT 0,
    h5p_overall_percentage DECIMAL(5,2) DEFAULT 0,
    h5p_total_time_spent INT DEFAULT 0,
    h5p_completion_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Video features
    video_total_videos INT DEFAULT 0,
    video_completed_videos INT DEFAULT 0,
    video_in_progress_videos INT DEFAULT 0,
    video_total_duration INT DEFAULT 0,
    video_total_watched_time INT DEFAULT 0,
    video_completion_rate DECIMAL(5,2) DEFAULT 0,
    video_watch_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Quiz features
    quiz_attempts INT DEFAULT 0,
    quiz_avg_score DECIMAL(5,2) DEFAULT 0,
    quiz_completion_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Forum features
    forum_posts INT DEFAULT 0,
    forum_comments INT DEFAULT 0,
    forum_upvotes INT DEFAULT 0,
    
    -- Discussion features
    discussion_threads_count INT DEFAULT 0,
    discussion_comments_count INT DEFAULT 0,
    discussion_total_interactions INT DEFAULT 0,
    discussion_questions_count INT DEFAULT 0,
    discussion_total_upvotes INT DEFAULT 0,
    
    -- Comparative features (so với các sinh viên khác)
    relative_to_course_problem_score DECIMAL(5,2) DEFAULT 0,
    relative_to_course_completion DECIMAL(5,2) DEFAULT 0,
    relative_to_course_video_completion DECIMAL(5,2) DEFAULT 0,
    relative_to_course_discussion DECIMAL(5,2) DEFAULT 0,
    performance_percentile DECIMAL(5,2) DEFAULT 50,
    is_below_course_average BOOLEAN DEFAULT FALSE,
    is_top_performer BOOLEAN DEFAULT FALSE,
    is_bottom_performer BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    extraction_batch_id VARCHAR(100),
    
    -- Indexes
    UNIQUE KEY uk_user_course (user_id, course_id),
    INDEX idx_course_id (course_id),
    INDEX idx_mooc_grade (mooc_grade_percentage),
    INDEX idx_mooc_is_passed (mooc_is_passed),
    INDEX idx_completion_rate (mooc_completion_rate),
    INDEX idx_last_activity (last_activity),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Real-time student features for production predictions';

-- ============================================================================
-- TABLE 2: PREDICTIONS
-- Chứa kết quả predictions từ các models
-- Có history, track model version, có thể compare models
-- ============================================================================
CREATE TABLE IF NOT EXISTS predictions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    
    -- Model metadata
    model_name VARCHAR(100) NOT NULL COMMENT 'e.g., fm101_v4, nltt_v1',
    model_version VARCHAR(50) COMMENT 'e.g., v4.2.1',
    model_path VARCHAR(500) COMMENT 'Path to model file',
    
    -- Prediction results
    fail_risk_score DECIMAL(5,2) NOT NULL COMMENT 'Predicted dropout/fail risk (0-100)',
    risk_level ENUM('LOW', 'MEDIUM', 'HIGH') NOT NULL,
    confidence_score DECIMAL(5,2) COMMENT 'Model confidence (if available)',
    
    -- Prediction context (snapshot of key features at prediction time)
    snapshot_grade DECIMAL(5,2),
    snapshot_completion_rate DECIMAL(5,2),
    snapshot_days_inactive INT,
    
    -- Metadata
    predicted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_latest BOOLEAN DEFAULT TRUE COMMENT 'Is this the most recent prediction?',
    
    -- Indexes
    INDEX idx_user_course (user_id, course_id),
    INDEX idx_course_model (course_id, model_name),
    INDEX idx_predicted_at (predicted_at),
    INDEX idx_is_latest (is_latest),
    INDEX idx_risk_level (risk_level),
    INDEX idx_model_name (model_name),
    
    -- Composite index for "latest prediction by student"
    INDEX idx_latest_prediction (user_id, course_id, is_latest, predicted_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='ML model predictions with history and versioning';

-- ============================================================================
-- TABLE 3: TRAINING_DATA
-- Chứa historical data đã có labels để train models
-- IMMUTABLE - chỉ INSERT, không UPDATE
-- ============================================================================
CREATE TABLE IF NOT EXISTS training_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    
    -- Enrollment features
    enrollment_mode VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    weeks_since_enrollment DECIMAL(5,2) DEFAULT 0,
    
    -- MOOC Grades features
    mooc_grade_percentage DECIMAL(5,2) DEFAULT 0,
    mooc_letter_grade VARCHAR(5),
    mooc_is_passed BOOLEAN DEFAULT NULL,
    
    -- Progress features
    progress_percent DECIMAL(5,2) DEFAULT 0,
    current_chapter VARCHAR(500),
    current_section VARCHAR(500),
    current_unit VARCHAR(500),
    mooc_completion_rate DECIMAL(5,2) DEFAULT 0,
    overall_completion DECIMAL(5,2) DEFAULT 0,
    completed_blocks INT DEFAULT 0,
    total_blocks INT DEFAULT 0,
    last_activity DATETIME,
    days_since_last_activity INT DEFAULT 999,
    
    -- Activity features
    access_frequency DECIMAL(10,2) DEFAULT 0,
    active_days INT DEFAULT 0,
    
    -- H5P features
    h5p_total_contents INT DEFAULT 0,
    h5p_completed_contents INT DEFAULT 0,
    h5p_total_score INT DEFAULT 0,
    h5p_total_max_score INT DEFAULT 0,
    h5p_overall_percentage DECIMAL(5,2) DEFAULT 0,
    h5p_total_time_spent INT DEFAULT 0,
    h5p_completion_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Video features
    video_total_videos INT DEFAULT 0,
    video_completed_videos INT DEFAULT 0,
    video_in_progress_videos INT DEFAULT 0,
    video_total_duration INT DEFAULT 0,
    video_total_watched_time INT DEFAULT 0,
    video_completion_rate DECIMAL(5,2) DEFAULT 0,
    video_watch_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Quiz features
    quiz_attempts INT DEFAULT 0,
    quiz_avg_score DECIMAL(5,2) DEFAULT 0,
    quiz_completion_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Forum features
    forum_posts INT DEFAULT 0,
    forum_comments INT DEFAULT 0,
    forum_upvotes INT DEFAULT 0,
    
    -- Discussion features
    discussion_threads_count INT DEFAULT 0,
    discussion_comments_count INT DEFAULT 0,
    discussion_total_interactions INT DEFAULT 0,
    discussion_questions_count INT DEFAULT 0,
    discussion_total_upvotes INT DEFAULT 0,
    
    -- Comparative features
    relative_to_course_problem_score DECIMAL(5,2) DEFAULT 0,
    relative_to_course_completion DECIMAL(5,2) DEFAULT 0,
    relative_to_course_video_completion DECIMAL(5,2) DEFAULT 0,
    relative_to_course_discussion DECIMAL(5,2) DEFAULT 0,
    performance_percentile DECIMAL(5,2) DEFAULT 50,
    is_below_course_average BOOLEAN DEFAULT FALSE,
    is_top_performer BOOLEAN DEFAULT FALSE,
    is_bottom_performer BOOLEAN DEFAULT FALSE,
    
    -- *** GROUND TRUTH LABELS (đã verified) ***
    is_dropout BOOLEAN NOT NULL COMMENT 'TRUE label: Student dropped out',
    is_passed BOOLEAN NOT NULL COMMENT 'TRUE label: Student passed the course',
    final_grade DECIMAL(5,2) COMMENT 'Final verified grade',
    
    -- Training metadata
    semester VARCHAR(50) COMMENT 'e.g., 2024_S1, 2024_S2',
    snapshot_week INT COMMENT 'Week of semester when snapshot taken (for early warning)',
    used_in_training BOOLEAN DEFAULT FALSE COMMENT 'Was this record used in model training?',
    training_model VARCHAR(100) COMMENT 'Model(s) trained with this data',
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    extraction_batch_id VARCHAR(100),
    
    -- Indexes
    INDEX idx_course_id (course_id),
    INDEX idx_semester (semester),
    INDEX idx_snapshot_week (snapshot_week),
    INDEX idx_is_dropout (is_dropout),
    INDEX idx_is_passed (is_passed),
    INDEX idx_used_in_training (used_in_training),
    INDEX idx_training_model (training_model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Historical training data with verified labels - IMMUTABLE';

-- ============================================================================
-- TABLE 4: MODEL_REGISTRY
-- Quản lý các models và ánh xạ với courses
-- ============================================================================
CREATE TABLE IF NOT EXISTS model_registry (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL UNIQUE COMMENT 'e.g., fm101_v4',
    model_version VARCHAR(50) NOT NULL COMMENT 'e.g., v4.2.1',
    model_path VARCHAR(500) NOT NULL COMMENT 'Path to .cbm file',
    features_csv_path VARCHAR(500) COMMENT 'Path to features CSV',
    
    -- Model metadata
    model_type VARCHAR(50) DEFAULT 'CatBoost' COMMENT 'CatBoost, XGBoost, etc.',
    num_features INT COMMENT 'Number of features',
    training_samples INT COMMENT 'Number of training samples',
    accuracy DECIMAL(5,4) COMMENT 'Model accuracy on test set',
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    auc_score DECIMAL(5,4),
    
    -- Applicability
    domain VARCHAR(100) COMMENT 'e.g., finance, linguistics, programming',
    required_features JSON COMMENT 'List of required feature names',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE COMMENT 'Default model for new courses',
    
    -- Metadata
    trained_at DATETIME COMMENT 'When model was trained',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    notes TEXT COMMENT 'Additional notes about the model',
    
    INDEX idx_model_name (model_name),
    INDEX idx_is_active (is_active),
    INDEX idx_is_default (is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Registry of available ML models';

-- ============================================================================
-- TABLE 5: COURSE_MODEL_MAPPING
-- Ánh xạ course → model (tự động chọn model)
-- ============================================================================
CREATE TABLE IF NOT EXISTS course_model_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id VARCHAR(255) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    
    -- Configuration
    auto_predict BOOLEAN DEFAULT TRUE COMMENT 'Automatically predict when new data arrives',
    predict_frequency VARCHAR(50) DEFAULT 'daily' COMMENT 'hourly, daily, weekly',
    min_features_required INT DEFAULT 5 COMMENT 'Minimum features needed to predict',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(100) COMMENT 'Who/what assigned this mapping',
    notes TEXT,
    
    UNIQUE KEY uk_course_model (course_id, model_name),
    INDEX idx_course_id (course_id),
    INDEX idx_model_name (model_name),
    INDEX idx_auto_predict (auto_predict),
    
    FOREIGN KEY (model_name) REFERENCES model_registry(model_name) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Mapping between courses and models for auto-prediction';

-- ============================================================================
-- RENAME OLD TABLE (Backup)
-- ============================================================================
-- RENAME TABLE raw_data TO raw_data_legacy_backup;

-- ============================================================================
-- INSERT DEFAULT MODEL REGISTRY
-- ============================================================================
INSERT INTO model_registry (
    model_name, model_version, model_path, features_csv_path,
    model_type, domain, is_active, is_default,
    notes
) VALUES (
    'fm101_v4',
    'v4.0.0',
    './models/fm101_model_v4.cbm',
    './models/fm101_model_v4_features.csv',
    'CatBoost',
    'finance',
    TRUE,
    TRUE,
    'Model V4 trained on FM101 course data - 36 features including video, quiz, discussion'
) ON DUPLICATE KEY UPDATE
    model_path = VALUES(model_path),
    features_csv_path = VALUES(features_csv_path),
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- INSERT DEFAULT COURSE MAPPINGS
-- ============================================================================
INSERT INTO course_model_mapping (
    course_id, model_name, auto_predict, predict_frequency, notes
) VALUES 
(
    'course-v1:DHQG-HCM+FM101+2025_S2',
    'fm101_v4',
    TRUE,
    'daily',
    'FM101 uses its own trained model'
),
(
    'course-v1:UEL+NLTT241225+2025_12',
    'fm101_v4',
    TRUE,
    'daily',
    'NLTT uses FM101 model (transfer learning) until NLTT-specific model is trained'
)
ON DUPLICATE KEY UPDATE
    auto_predict = VALUES(auto_predict),
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- VIEWS FOR BACKWARD COMPATIBILITY
-- ============================================================================

-- View mô phỏng raw_data cũ (để code cũ vẫn chạy được trong transition period)
CREATE OR REPLACE VIEW raw_data_view AS
SELECT 
    f.id,
    f.user_id,
    f.course_id,
    
    -- Features từ student_features
    f.enrollment_mode,
    f.is_active,
    f.weeks_since_enrollment,
    f.mooc_grade_percentage,
    f.mooc_letter_grade,
    f.mooc_is_passed,
    f.progress_percent,
    f.current_chapter,
    f.current_section,
    f.current_unit,
    f.mooc_completion_rate,
    f.overall_completion,
    f.completed_blocks,
    f.total_blocks,
    f.last_activity,
    f.days_since_last_activity,
    f.access_frequency,
    f.active_days,
    f.h5p_total_contents,
    f.h5p_completed_contents,
    f.h5p_total_score,
    f.h5p_total_max_score,
    f.h5p_overall_percentage,
    f.h5p_total_time_spent,
    f.h5p_completion_rate,
    f.video_total_videos,
    f.video_completed_videos,
    f.video_in_progress_videos,
    f.video_total_duration,
    f.video_total_watched_time,
    f.video_completion_rate,
    f.video_watch_rate,
    f.quiz_attempts,
    f.quiz_avg_score,
    f.quiz_completion_rate,
    f.forum_posts,
    f.forum_comments,
    f.forum_upvotes,
    f.discussion_threads_count,
    f.discussion_comments_count,
    f.discussion_total_interactions,
    f.discussion_questions_count,
    f.discussion_total_upvotes,
    f.relative_to_course_problem_score,
    f.relative_to_course_completion,
    f.relative_to_course_video_completion,
    f.relative_to_course_discussion,
    f.performance_percentile,
    f.is_below_course_average,
    f.is_top_performer,
    f.is_bottom_performer,
    
    -- Predictions từ predictions table (latest only)
    p.fail_risk_score,
    p.model_name,
    p.predicted_at AS extracted_at,
    f.extraction_batch_id
    
FROM student_features f
LEFT JOIN predictions p ON f.user_id = p.user_id 
    AND f.course_id = p.course_id 
    AND p.is_latest = TRUE;

-- ============================================================================
-- HELPER VIEW: Latest predictions per student
-- ============================================================================
CREATE OR REPLACE VIEW latest_predictions AS
SELECT 
    p.*,
    f.mooc_grade_percentage,
    f.mooc_completion_rate,
    f.mooc_is_passed
FROM predictions p
JOIN student_features f ON p.user_id = f.user_id AND p.course_id = f.course_id
WHERE p.is_latest = TRUE;

-- ============================================================================
-- COMMENTS
-- ============================================================================

/*
USAGE EXAMPLES:

-- 1. Fetch new course data
python database/fetch_mooc_h5p_data.py --course-id "..." --sessionid "..."
→ Inserts into student_features (NOT raw_data anymore)

-- 2. Predict with Model V4
python predict.py --course-id "..." --model fm101_v4
→ Reads from student_features
→ Inserts into predictions

-- 3. Query for dashboard
SELECT 
    e.full_name,
    f.mooc_grade_percentage,
    p.fail_risk_score,
    p.risk_level,
    p.model_name
FROM enrollments e
JOIN student_features f ON e.user_id = f.user_id
LEFT JOIN predictions p ON f.user_id = p.user_id 
    AND f.course_id = p.course_id 
    AND p.is_latest = TRUE
WHERE f.course_id = 'course-v1:...';

-- 4. Prepare training data (after semester ends)
INSERT INTO training_data 
SELECT 
    NULL as id,
    f.*,
    -- Add verified labels
    CASE WHEN f.days_since_last_activity > 30 THEN TRUE ELSE FALSE END as is_dropout,
    f.mooc_is_passed as is_passed,
    f.mooc_grade_percentage as final_grade,
    '2025_S1' as semester,
    NULL as snapshot_week,
    FALSE as used_in_training,
    NULL as training_model,
    NOW() as created_at,
    f.extraction_batch_id
FROM student_features f
WHERE f.course_id = 'course-v1:...'
  AND f.mooc_is_passed IS NOT NULL;  -- Đã có kết quả cuối kỳ

-- 5. Compare models
SELECT 
    model_name,
    AVG(fail_risk_score) as avg_risk,
    COUNT(*) as predictions_count
FROM predictions
WHERE course_id = 'course-v1:...'
GROUP BY model_name;
*/
