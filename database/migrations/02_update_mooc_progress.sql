-- ============================================================
-- Migration: Update mooc_progress table
-- Purpose: Thêm chi tiết tiến độ từ API /api/custom/v1/export/student-progress/{course_id}/
-- Date: 2026-01-20
-- ============================================================

USE dropout_prediction_db;

-- Add new columns to mooc_progress
ALTER TABLE mooc_progress
ADD COLUMN IF NOT EXISTS current_chapter VARCHAR(500) AFTER progress_percent COMMENT 'Chapter đang học',
ADD COLUMN IF NOT EXISTS current_section VARCHAR(500) AFTER current_chapter COMMENT 'Section đang học',
ADD COLUMN IF NOT EXISTS current_unit VARCHAR(500) AFTER current_section COMMENT 'Unit đang học',
ADD COLUMN IF NOT EXISTS completion_rate DECIMAL(5,2) DEFAULT 0 AFTER current_unit COMMENT 'Completion rate from API (may differ from progress_percent)';

-- Add indexes for new columns
ALTER TABLE mooc_progress
ADD INDEX IF NOT EXISTS idx_completion_rate (completion_rate),
ADD INDEX IF NOT EXISTS idx_current_chapter (current_chapter(255)),
ADD INDEX IF NOT EXISTS idx_current_section (current_section(255));

-- Update table comment
ALTER TABLE mooc_progress 
COMMENT='MOOC progress with detailed chapter/section/unit info from student-progress export API';

-- Verify columns added
SELECT 'mooc_progress table updated successfully' AS status;
DESCRIBE mooc_progress;
