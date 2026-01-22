-- ============================================================
-- ROLLBACK SCRIPT
-- Purpose: Undo tất cả thay đổi từ migration add_mooc_export_tables.sql
-- Date: 2026-01-20
-- Usage: mysql -u root -p dropout_prediction_db < rollback_mooc_export_tables.sql
-- WARNING: Script này sẽ XÓA dữ liệu! Backup trước khi chạy.
-- ============================================================

USE dropout_prediction_db;

SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

START TRANSACTION;

-- ============================================================
-- 1. Drop mooc_grades table
-- ============================================================
DROP TABLE IF EXISTS mooc_grades;
SELECT 'Step 1/4: Dropped mooc_grades table' AS progress;

-- ============================================================
-- 2. Remove columns from mooc_progress
-- ============================================================
ALTER TABLE mooc_progress
DROP COLUMN IF EXISTS current_chapter,
DROP COLUMN IF EXISTS current_section,
DROP COLUMN IF EXISTS current_unit,
DROP COLUMN IF EXISTS completion_rate;

SELECT 'Step 2/4: Removed columns from mooc_progress' AS progress;

-- ============================================================
-- 3. Drop mooc_discussions table
-- ============================================================
DROP TABLE IF EXISTS mooc_discussions;
SELECT 'Step 3/4: Dropped mooc_discussions table' AS progress;

-- ============================================================
-- 4. Remove columns from raw_data
-- ============================================================
ALTER TABLE raw_data
DROP COLUMN IF EXISTS mooc_grade_percentage,
DROP COLUMN IF EXISTS mooc_letter_grade,
DROP COLUMN IF EXISTS mooc_is_passed,
DROP COLUMN IF EXISTS current_chapter,
DROP COLUMN IF EXISTS current_section,
DROP COLUMN IF EXISTS current_unit,
DROP COLUMN IF EXISTS mooc_completion_rate,
DROP COLUMN IF EXISTS discussion_threads_count,
DROP COLUMN IF EXISTS discussion_comments_count,
DROP COLUMN IF EXISTS discussion_total_interactions,
DROP COLUMN IF EXISTS discussion_questions_count,
DROP COLUMN IF EXISTS discussion_total_upvotes;

SELECT 'Step 4/4: Removed columns from raw_data' AS progress;

COMMIT;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;

-- ============================================================
-- Verification
-- ============================================================
SELECT '✅ Rollback completed successfully!' AS status;
SELECT '' AS separator;
SELECT '⚠️  The following tables/columns have been removed:' AS warning;
SELECT '  - mooc_grades table (DELETED)' AS removed;
SELECT '  - mooc_discussions table (DELETED)' AS removed;
SELECT '  - mooc_progress: current_chapter, current_section, current_unit, completion_rate' AS removed;
SELECT '  - raw_data: mooc_*, current_*, discussion_* columns' AS removed;
SELECT '' AS separator;
SELECT 'Verify rollback:' AS next_step;
SELECT '  SHOW TABLES;' AS verification;
SELECT '  DESC mooc_progress;' AS verification;
SELECT '  DESC raw_data;' AS verification;
