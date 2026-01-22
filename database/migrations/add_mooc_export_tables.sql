-- ============================================================
-- MASTER MIGRATION SCRIPT
-- Purpose: Thêm tất cả bảng và columns mới cho MOOC Export APIs
-- Date: 2026-01-20
-- Usage: mysql -u root -p dropout_prediction_db < add_mooc_export_tables.sql
-- ============================================================

USE dropout_prediction_db;

SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- Start transaction
START TRANSACTION;

-- ============================================================
-- 1. Create mooc_grades table
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
    letter_grade VARCHAR(5) COMMENT 'A, B, C, D, F',
    is_passed BOOLEAN DEFAULT FALSE,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
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

SELECT 'Step 1/4: mooc_grades table created' AS progress;

-- ============================================================
-- 2. Update mooc_progress table
-- ============================================================
-- Check and add columns only if they don't exist
SET @dbname = 'dropout_prediction_db';
SET @tablename = 'mooc_progress';
SET @columnname = 'current_chapter';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname)
     AND (TABLE_NAME = @tablename)
     AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'current_chapter already exists' AS info;",
  "ALTER TABLE mooc_progress ADD COLUMN current_chapter VARCHAR(500) AFTER progress_percent COMMENT 'Chapter đang học';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'current_section';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname)
     AND (TABLE_NAME = @tablename)
     AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'current_section already exists' AS info;",
  "ALTER TABLE mooc_progress ADD COLUMN current_section VARCHAR(500) AFTER current_chapter COMMENT 'Section đang học';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'current_unit';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname)
     AND (TABLE_NAME = @tablename)
     AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'current_unit already exists' AS info;",
  "ALTER TABLE mooc_progress ADD COLUMN current_unit VARCHAR(500) AFTER current_section COMMENT 'Unit đang học';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'completion_rate';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname)
     AND (TABLE_NAME = @tablename)
     AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'completion_rate already exists' AS info;",
  "ALTER TABLE mooc_progress ADD COLUMN completion_rate DECIMAL(5,2) DEFAULT 0 AFTER current_unit COMMENT 'Completion rate from API';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SELECT 'Step 2/4: mooc_progress table updated' AS progress;

-- ============================================================
-- 3. Create mooc_discussions table
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

SELECT 'Step 3/4: mooc_discussions table created' AS progress;

-- ============================================================
-- 4. Update raw_data table
-- ============================================================
SET @tablename = 'raw_data';

-- Add MOOC Grade columns
SET @columnname = 'mooc_grade_percentage';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname) AND (TABLE_NAME = @tablename) AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'mooc_grade_percentage already exists' AS info;",
  "ALTER TABLE raw_data ADD COLUMN mooc_grade_percentage DECIMAL(5,2) DEFAULT 0 AFTER enrollment_mode COMMENT 'MOOC grade percentage (0-100)';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'mooc_letter_grade';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname) AND (TABLE_NAME = @tablename) AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'mooc_letter_grade already exists' AS info;",
  "ALTER TABLE raw_data ADD COLUMN mooc_letter_grade VARCHAR(5) AFTER mooc_grade_percentage COMMENT 'MOOC letter grade';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'mooc_is_passed';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname) AND (TABLE_NAME = @tablename) AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'mooc_is_passed already exists' AS info;",
  "ALTER TABLE raw_data ADD COLUMN mooc_is_passed BOOLEAN DEFAULT NULL AFTER mooc_letter_grade COMMENT 'MOOC pass/fail status';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Add Progress detail columns
SET @columnname = 'current_chapter';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname) AND (TABLE_NAME = @tablename) AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'current_chapter already exists' AS info;",
  "ALTER TABLE raw_data ADD COLUMN current_chapter VARCHAR(500) AFTER progress_percent COMMENT 'Current chapter';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'current_section';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname) AND (TABLE_NAME = @tablename) AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'current_section already exists' AS info;",
  "ALTER TABLE raw_data ADD COLUMN current_section VARCHAR(500) AFTER current_chapter COMMENT 'Current section';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'current_unit';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname) AND (TABLE_NAME = @tablename) AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'current_unit already exists' AS info;",
  "ALTER TABLE raw_data ADD COLUMN current_unit VARCHAR(500) AFTER current_section COMMENT 'Current unit';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'mooc_completion_rate';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname) AND (TABLE_NAME = @tablename) AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'mooc_completion_rate already exists' AS info;",
  "ALTER TABLE raw_data ADD COLUMN mooc_completion_rate DECIMAL(5,2) DEFAULT 0 AFTER current_unit COMMENT 'MOOC completion rate';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Add Discussion columns
SET @columnname = 'discussion_threads_count';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname) AND (TABLE_NAME = @tablename) AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'discussion_threads_count already exists' AS info;",
  "ALTER TABLE raw_data ADD COLUMN discussion_threads_count INT DEFAULT 0 AFTER forum_upvotes COMMENT 'Discussion threads created';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'discussion_comments_count';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname) AND (TABLE_NAME = @tablename) AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'discussion_comments_count already exists' AS info;",
  "ALTER TABLE raw_data ADD COLUMN discussion_comments_count INT DEFAULT 0 AFTER discussion_threads_count COMMENT 'Discussion comments';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'discussion_total_interactions';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname) AND (TABLE_NAME = @tablename) AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'discussion_total_interactions already exists' AS info;",
  "ALTER TABLE raw_data ADD COLUMN discussion_total_interactions INT DEFAULT 0 AFTER discussion_comments_count COMMENT 'Total interactions';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'discussion_questions_count';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname) AND (TABLE_NAME = @tablename) AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'discussion_questions_count already exists' AS info;",
  "ALTER TABLE raw_data ADD COLUMN discussion_questions_count INT DEFAULT 0 AFTER discussion_total_interactions COMMENT 'Questions asked';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'discussion_total_upvotes';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE (TABLE_SCHEMA = @dbname) AND (TABLE_NAME = @tablename) AND (COLUMN_NAME = @columnname)) > 0,
  "SELECT 'discussion_total_upvotes already exists' AS info;",
  "ALTER TABLE raw_data ADD COLUMN discussion_total_upvotes INT DEFAULT 0 AFTER discussion_questions_count COMMENT 'Total upvotes';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SELECT 'Step 4/4: raw_data table updated' AS progress;

-- Commit transaction
COMMIT;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;

-- ============================================================
-- Verification
-- ============================================================
SELECT '✅ Migration completed successfully!' AS status;
SELECT '' AS separator;
SELECT 'Created/Updated Tables:' AS info;
SELECT '  - mooc_grades (new)' AS tables;
SELECT '  - mooc_progress (updated)' AS tables;
SELECT '  - mooc_discussions (new)' AS tables;
SELECT '  - raw_data (updated)' AS tables;
SELECT '' AS separator;
SELECT 'Run verification queries to check schema:' AS next_step;
SELECT '  DESCRIBE mooc_grades;' AS verification;
SELECT '  DESCRIBE mooc_discussions;' AS verification;
SELECT '  DESC mooc_progress;' AS verification;
SELECT '  DESC raw_data;' AS verification;
