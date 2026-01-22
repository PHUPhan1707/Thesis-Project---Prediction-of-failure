-- ============================================================
-- Migration: Create mooc_discussions table
-- Purpose: Lưu tương tác discussion từ API /api/custom/v1/export/student-discussions/{course_id}/
-- Date: 2026-01-20
-- ============================================================

USE dropout_prediction_db;

-- Create mooc_discussions table
CREATE TABLE IF NOT EXISTS mooc_discussions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- User identification
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    username VARCHAR(255),
    email VARCHAR(255),
    full_name VARCHAR(500),
    
    -- Discussion metrics
    threads_count INT DEFAULT 0 COMMENT 'Số topic/thread đã tạo',
    comments_count INT DEFAULT 0 COMMENT 'Số comment đã viết',
    total_interactions INT DEFAULT 0 COMMENT 'Tổng tương tác (threads + comments)',
    questions_count INT DEFAULT 0 COMMENT 'Số câu hỏi đã tạo',
    total_upvotes INT DEFAULT 0 COMMENT 'Tổng upvote nhận được',
    
    -- Metadata
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Constraints and Indexes
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

-- Verify table created
SELECT 'mooc_discussions table created successfully' AS status;
DESCRIBE mooc_discussions;
