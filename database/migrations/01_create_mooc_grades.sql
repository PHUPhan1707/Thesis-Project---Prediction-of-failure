-- ============================================================
-- Migration: Create mooc_grades table
-- Purpose: Lưu điểm số MOOC từ API /api/custom/v1/export/student-grades/{course_id}/
-- Date: 2026-01-20
-- ============================================================

USE dropout_prediction_db;

-- Create mooc_grades table
CREATE TABLE IF NOT EXISTS mooc_grades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- User identification
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    username VARCHAR(255),
    email VARCHAR(255),
    full_name VARCHAR(500),
    
    -- Grade data (API trả về cả 2 format)
    percent_grade DECIMAL(5,2) DEFAULT 0 COMMENT 'Grade as 0-1 decimal',
    grade_percentage DECIMAL(5,2) DEFAULT 0 COMMENT 'Grade as 0-100 percentage',
    letter_grade VARCHAR(5) COMMENT 'Pass if is_passed=true, empty string if is_passed=false',
    is_passed BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Constraints and Indexes
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

-- Verify table created
SELECT 'mooc_grades table created successfully' AS status;
DESCRIBE mooc_grades;
