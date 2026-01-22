-- ============================================================
-- Migration: Update raw_data table
-- Purpose: Thêm features từ MOOC grades, progress, discussions
-- Date: 2026-01-20
-- ============================================================

USE dropout_prediction_db;

-- Add MOOC Grades columns
ALTER TABLE raw_data
ADD COLUMN IF NOT EXISTS mooc_grade_percentage DECIMAL(5,2) DEFAULT 0 AFTER enrollment_mode COMMENT 'MOOC grade percentage (0-100)',
ADD COLUMN IF NOT EXISTS mooc_letter_grade VARCHAR(5) AFTER mooc_grade_percentage COMMENT 'MOOC letter grade (A, B, C, D, F)',
ADD COLUMN IF NOT EXISTS mooc_is_passed BOOLEAN DEFAULT NULL AFTER mooc_letter_grade COMMENT 'MOOC pass/fail status';

-- Add MOOC Progress detail columns
ALTER TABLE raw_data
ADD COLUMN IF NOT EXISTS current_chapter VARCHAR(500) AFTER progress_percent COMMENT 'Current chapter being studied',
ADD COLUMN IF NOT EXISTS current_section VARCHAR(500) AFTER current_chapter COMMENT 'Current section being studied',
ADD COLUMN IF NOT EXISTS current_unit VARCHAR(500) AFTER current_section COMMENT 'Current unit being studied',
ADD COLUMN IF NOT EXISTS mooc_completion_rate DECIMAL(5,2) DEFAULT 0 AFTER current_unit COMMENT 'MOOC completion rate';

-- Add MOOC Discussions columns
ALTER TABLE raw_data
ADD COLUMN IF NOT EXISTS discussion_threads_count INT DEFAULT 0 AFTER forum_upvotes COMMENT 'Number of discussion threads created',
ADD COLUMN IF NOT EXISTS discussion_comments_count INT DEFAULT 0 AFTER discussion_threads_count COMMENT 'Number of discussion comments',
ADD COLUMN IF NOT EXISTS discussion_total_interactions INT DEFAULT 0 AFTER discussion_comments_count COMMENT 'Total discussion interactions',
ADD COLUMN IF NOT EXISTS discussion_questions_count INT DEFAULT 0 AFTER discussion_total_interactions COMMENT 'Number of questions asked',
ADD COLUMN IF NOT EXISTS discussion_total_upvotes INT DEFAULT 0 AFTER discussion_questions_count COMMENT 'Total upvotes received';

-- Add indexes for new columns
ALTER TABLE raw_data
ADD INDEX IF NOT EXISTS idx_mooc_grade_percentage (mooc_grade_percentage),
ADD INDEX IF NOT EXISTS idx_mooc_letter_grade (mooc_letter_grade),
ADD INDEX IF NOT EXISTS idx_mooc_is_passed (mooc_is_passed),
ADD INDEX IF NOT EXISTS idx_mooc_completion_rate (mooc_completion_rate),
ADD INDEX IF NOT EXISTS idx_discussion_total_interactions (discussion_total_interactions);

-- Update table comment
ALTER TABLE raw_data
COMMENT='Aggregated features for ML training - includes H5P, Video, MOOC Grades, Progress, and Discussions';

-- Verify columns added
SELECT 'raw_data table updated successfully' AS status;
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    COLUMN_DEFAULT, 
    COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'dropout_prediction_db' 
  AND TABLE_NAME = 'raw_data'
  AND COLUMN_NAME IN (
      'mooc_grade_percentage', 'mooc_letter_grade', 'mooc_is_passed',
      'current_chapter', 'current_section', 'current_unit', 'mooc_completion_rate',
      'discussion_threads_count', 'discussion_comments_count', 'discussion_total_interactions',
      'discussion_questions_count', 'discussion_total_upvotes'
  )
ORDER BY ORDINAL_POSITION;
