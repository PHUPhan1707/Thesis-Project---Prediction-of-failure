-- Drop existing database and recreate
DROP DATABASE IF EXISTS dropout_prediction_db;
CREATE DATABASE dropout_prediction_db;
USE dropout_prediction_db;

-- ============================================================
-- TABLE 1: enrollments
-- Lưu thông tin enrollment từ API: course-enrollments-attributes
-- ============================================================
CREATE TABLE IF NOT EXISTS enrollments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    course_id VARCHAR(255) NOT NULL,
    user_id INT NOT NULL,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(500),
    enrollment_id INT NOT NULL,
    mode VARCHAR(50) DEFAULT 'audit',
    is_active BOOLEAN DEFAULT TRUE,
    created DATETIME,
    -- Student info fields
    mssv VARCHAR(100),
    first_name VARCHAR(255),
    middle_name VARCHAR(255),
    last_name VARCHAR(255),
    full_name_vn VARCHAR(500),
    class_code VARCHAR(100),
    department VARCHAR(255),
    faculty VARCHAR(255),
    -- Store all_attributes as JSON for flexibility
    all_attributes JSON,
    -- Metadata
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Indexes
    UNIQUE KEY uk_enrollment (enrollment_id),
    INDEX idx_user_id (user_id),
    INDEX idx_course_id (course_id),
    INDEX idx_user_course (user_id, course_id),
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_is_active (is_active),
    INDEX idx_mode (mode),
    INDEX idx_created (created)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE 2: h5p_scores
-- Lưu chi tiết điểm H5P từng content từ API: /scores/{user_id}/{course_id}
-- ============================================================
CREATE TABLE IF NOT EXISTS h5p_scores (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    content_id INT NOT NULL,
    content_title VARCHAR(500),
    score INT DEFAULT 0,
    max_score INT DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    opened BIGINT DEFAULT 0,
    finished BIGINT DEFAULT 0,
    time_spent BIGINT DEFAULT 0 COMMENT 'seconds',
    folder_id INT,
    folder_name VARCHAR(255),
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- Indexes
    INDEX idx_user_course (user_id, course_id),
    INDEX idx_content_id (content_id),
    INDEX idx_folder_id (folder_id),
    INDEX idx_fetched_at (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE 3: h5p_scores_summary
-- Tổng hợp điểm H5P per user từ API: /scores/{user_id}/{course_id} (summary)
-- ============================================================
CREATE TABLE IF NOT EXISTS h5p_scores_summary (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    total_contents INT DEFAULT 0,
    completed_contents INT DEFAULT 0,
    total_score INT DEFAULT 0,
    total_max_score INT DEFAULT 0,
    overall_percentage DECIMAL(5,2) DEFAULT 0,
    total_time_spent INT DEFAULT 0, -- seconds
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Indexes
    UNIQUE KEY uk_user_course (user_id, course_id),
    INDEX idx_course_id (course_id),
    INDEX idx_fetched_at (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE 4: video_progress
-- Lưu chi tiết tiến độ video từng content từ API: /video-progress/{user_id}/{course_id}
-- ============================================================
CREATE TABLE IF NOT EXISTS video_progress (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    content_id INT NOT NULL,
    content_title VARCHAR(500),
    progress_percent DECIMAL(5,2) DEFAULT 0,
    `current_time` INT DEFAULT 0 COMMENT 'seconds',
    `duration` INT DEFAULT 0 COMMENT 'seconds',
    status VARCHAR(50) COMMENT 'completed, in_progress, not_started',
    folder_id INT,
    folder_name VARCHAR(255),
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- Indexes
    INDEX idx_user_course (user_id, course_id),
    INDEX idx_content_id (content_id),
    INDEX idx_folder_id (folder_id),
    INDEX idx_status (status),
    INDEX idx_fetched_at (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE 5: video_progress_summary
-- Tổng hợp tiến độ video per user từ API: /video-progress/{user_id}/{course_id} (summary)
-- ============================================================
CREATE TABLE IF NOT EXISTS video_progress_summary (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    total_videos INT DEFAULT 0,
    completed_videos INT DEFAULT 0,
    in_progress_videos INT DEFAULT 0,
    not_started_videos INT DEFAULT 0,
    total_duration INT DEFAULT 0, -- seconds
    total_watched_time INT DEFAULT 0, -- seconds
    overall_progress DECIMAL(5,2) DEFAULT 0,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Indexes
    UNIQUE KEY uk_user_course (user_id, course_id),
    INDEX idx_course_id (course_id),
    INDEX idx_fetched_at (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE 6: dashboard_summary
-- Tổng hợp dashboard từ API: /dashboard/{user_id}/{course_id}
-- ============================================================
CREATE TABLE IF NOT EXISTS dashboard_summary (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    -- Overview
    overall_completion DECIMAL(5,2) DEFAULT 0,
    total_items INT DEFAULT 0,
    completed_items INT DEFAULT 0,
    items_to_complete INT DEFAULT 0,
    -- H5P Stats
    h5p_total_contents INT DEFAULT 0,
    h5p_completed_contents INT DEFAULT 0,
    h5p_total_score INT DEFAULT 0,
    h5p_total_max_score INT DEFAULT 0,
    h5p_average_percentage DECIMAL(5,2) DEFAULT 0,
    h5p_total_time_spent INT DEFAULT 0,
    -- Video Stats
    video_total_videos INT DEFAULT 0,
    video_completed_videos INT DEFAULT 0,
    video_in_progress_videos INT DEFAULT 0,
    video_average_progress DECIMAL(5,2) DEFAULT 0,
    -- Folder Stats
    folder_total_folders INT DEFAULT 0,
    folder_completed_folders INT DEFAULT 0,
    folder_average_percentage DECIMAL(5,2) DEFAULT 0,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Indexes
    UNIQUE KEY uk_user_course (user_id, course_id),
    INDEX idx_course_id (course_id),
    INDEX idx_fetched_at (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE 7: mooc_progress
-- Lưu tiến độ từ MOOC API: /stats/progress/{course_id}/ (per user data)
-- Hoặc từ API khác lấy được per-user progress
-- ============================================================
CREATE TABLE IF NOT EXISTS mooc_progress (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    total_blocks INT DEFAULT 0,
    completed_blocks INT DEFAULT 0,
    progress_percent DECIMAL(5,2) DEFAULT 0,
    current_chapter VARCHAR(500) COMMENT 'Chapter đang học',
    current_section VARCHAR(500) COMMENT 'Section đang học',
    current_unit VARCHAR(500) COMMENT 'Unit đang học',
    completion_rate DECIMAL(5,2) DEFAULT 0 COMMENT 'Completion rate from API',
    last_activity DATETIME,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Indexes
    UNIQUE KEY uk_user_course (user_id, course_id),
    INDEX idx_course_id (course_id),
    INDEX idx_progress_percent (progress_percent),
    INDEX idx_completion_rate (completion_rate),
    INDEX idx_last_activity (last_activity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE 8: mooc_grades
-- Lưu điểm số MOOC từ API: /api/custom/v1/export/student-grades/{course_id}/
-- ============================================================
CREATE TABLE IF NOT EXISTS mooc_grades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    username VARCHAR(255),
    email VARCHAR(255),
    full_name VARCHAR(500),
    percent_grade DECIMAL(5,2) DEFAULT 0 COMMENT 'Grade as 0-1 decimal',
    grade_percentage DECIMAL(5,2) DEFAULT 0 COMMENT 'Grade as 0-100 percentage',
    letter_grade VARCHAR(5) COMMENT 'Pass if is_passed=true, empty string if is_passed=false',
    is_passed BOOLEAN DEFAULT FALSE,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Indexes
    UNIQUE KEY uk_user_course (user_id, course_id),
    INDEX idx_course_id (course_id),
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_grade_percentage (grade_percentage),
    INDEX idx_letter_grade (letter_grade),
    INDEX idx_is_passed (is_passed),
    INDEX idx_fetched_at (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='MOOC grades from student-grades export API';

-- ============================================================
-- TABLE 9: mooc_discussions
-- Lưu tương tác discussion từ API: /api/custom/v1/export/student-discussions/{course_id}/
-- ============================================================
CREATE TABLE IF NOT EXISTS mooc_discussions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    username VARCHAR(255),
    email VARCHAR(255),
    full_name VARCHAR(500),
    threads_count INT DEFAULT 0 COMMENT 'Số topic/thread đã tạo',
    comments_count INT DEFAULT 0 COMMENT 'Số comment đã viết',
    total_interactions INT DEFAULT 0 COMMENT 'Tổng tương tác (threads + comments)',
    questions_count INT DEFAULT 0 COMMENT 'Số câu hỏi đã tạo',
    total_upvotes INT DEFAULT 0 COMMENT 'Tổng upvote nhận được',
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Indexes
    UNIQUE KEY uk_user_course (user_id, course_id),
    INDEX idx_course_id (course_id),
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_threads_count (threads_count),
    INDEX idx_comments_count (comments_count),
    INDEX idx_total_interactions (total_interactions),
    INDEX idx_total_upvotes (total_upvotes),
    INDEX idx_fetched_at (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='MOOC discussion interactions from student-discussions export API';

-- ============================================================
-- TABLE 10: raw_data
-- Bảng tổng hợp tất cả features cho training model
-- Data được aggregate từ các bảng trên
-- ============================================================
CREATE TABLE IF NOT EXISTS raw_data (
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
    access_frequency DECIMAL(10,2) DEFAULT 0, -- times per week
    active_days INT DEFAULT 0,
    
    -- H5P Scores features
    h5p_total_contents INT DEFAULT 0,
    h5p_completed_contents INT DEFAULT 0,
    h5p_total_score INT DEFAULT 0,
    h5p_total_max_score INT DEFAULT 0,
    h5p_overall_percentage DECIMAL(5,2) DEFAULT 0,
    h5p_total_time_spent INT DEFAULT 0, -- seconds
    h5p_completion_rate DECIMAL(5,2) DEFAULT 0, -- completed/total
    
    -- Video features
    video_total_videos INT DEFAULT 0,
    video_completed_videos INT DEFAULT 0,
    video_in_progress_videos INT DEFAULT 0,
    video_total_duration INT DEFAULT 0, -- seconds
    video_total_watched_time INT DEFAULT 0, -- seconds
    video_completion_rate DECIMAL(5,2) DEFAULT 0, -- completed/total
    video_watch_rate DECIMAL(5,2) DEFAULT 0, -- watched_time/total_duration
    
    -- Assessment/Quiz features (từ H5P scores)
    quiz_attempts INT DEFAULT 0, -- số lần làm bài (completed_contents)
    quiz_avg_score DECIMAL(5,2) DEFAULT 0, -- h5p_overall_percentage
    quiz_completion_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Forum/Discussion features (Legacy - TODO: từ API khác nếu có)
    forum_posts INT DEFAULT 0,
    forum_comments INT DEFAULT 0,
    forum_upvotes INT DEFAULT 0,
    
    -- MOOC Discussion features (từ mooc_discussions table)
    discussion_threads_count INT DEFAULT 0 COMMENT 'Number of discussion threads created',
    discussion_comments_count INT DEFAULT 0 COMMENT 'Number of discussion comments',
    discussion_total_interactions INT DEFAULT 0 COMMENT 'Total discussion interactions',
    discussion_questions_count INT DEFAULT 0 COMMENT 'Number of questions asked',
    discussion_total_upvotes INT DEFAULT 0 COMMENT 'Total upvotes received',
    
    -- Target labels (để NULL, sẽ được label thủ công hoặc AI dự đoán)
    is_dropout BOOLEAN DEFAULT NULL, -- Target 1: Sinh viên có bỏ học giữa chừng không? (tự động label từ is_active, days_since_last_activity)
    is_passed BOOLEAN DEFAULT NULL, -- Target 2: Sinh viên có pass môn học không? (cần label thủ công sau khi có kết quả cuối khóa)
    dropout_risk_score DECIMAL(5,2) DEFAULT NULL, -- Prediction 1: Tỷ lệ rủi ro bỏ học (0-100), được AI dự đoán
    fail_risk_score DECIMAL(5,2) DEFAULT NULL, -- Prediction 2: Tỷ lệ rủi ro rớt môn (0-100), được AI dự đoán
    
    -- Metadata
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    extraction_batch_id VARCHAR(100),
    
    -- Indexes
    UNIQUE KEY uk_user_course (user_id, course_id),
    INDEX idx_course_id (course_id),
    INDEX idx_mooc_grade_percentage (mooc_grade_percentage),
    INDEX idx_mooc_letter_grade (mooc_letter_grade),
    INDEX idx_mooc_is_passed (mooc_is_passed),
    INDEX idx_progress_percent (progress_percent),
    INDEX idx_mooc_completion_rate (mooc_completion_rate),
    INDEX idx_overall_completion (overall_completion),
    INDEX idx_days_since_last_activity (days_since_last_activity),
    INDEX idx_discussion_total_interactions (discussion_total_interactions),
    INDEX idx_is_passed (is_passed),
    INDEX idx_dropout_risk_score (dropout_risk_score),
    INDEX idx_extraction_batch (extraction_batch_id),
    INDEX idx_extracted_at (extracted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Aggregated features for ML training - includes H5P, Video, MOOC Grades, Progress, and Discussions';
