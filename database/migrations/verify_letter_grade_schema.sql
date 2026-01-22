-- ============================================================
-- Verification Queries for Letter Grade Schema Updates
-- Purpose: Verify that letter_grade schema comments have been updated correctly
-- Date: 2026-01-20
-- ============================================================

-- Query 1: Verify mooc_grades table letter_grade column comment
SELECT 
    TABLE_NAME,
    COLUMN_NAME, 
    DATA_TYPE, 
    COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'dropout_prediction_db' 
  AND TABLE_NAME = 'mooc_grades'
  AND COLUMN_NAME = 'letter_grade';

-- Expected: COLUMN_COMMENT should contain "Pass if is_passed=true, empty string if is_passed=false"

-- Query 2: Verify raw_data table mooc_letter_grade column comment
SELECT 
    TABLE_NAME,
    COLUMN_NAME, 
    DATA_TYPE, 
    COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'dropout_prediction_db' 
  AND TABLE_NAME = 'raw_data'
  AND COLUMN_NAME = 'mooc_letter_grade';

-- Expected: COLUMN_COMMENT should contain "MOOC letter grade (Pass or empty string)"

-- Query 3: Check data consistency (if data exists)
-- Verify that existing data follows the Pass/"" pattern
SELECT 
    is_passed,
    letter_grade,
    COUNT(*) as count,
    CONCAT(ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2), '%') as percentage
FROM mooc_grades
GROUP BY is_passed, letter_grade
ORDER BY is_passed, letter_grade;

-- Expected distribution:
-- is_passed = 1 (true)  → letter_grade = 'Pass'
-- is_passed = 0 (false) → letter_grade = '' or NULL

-- Query 4: Find any anomalies (data that doesn't match expected pattern)
SELECT 
    user_id,
    course_id,
    username,
    is_passed,
    letter_grade,
    grade_percentage
FROM mooc_grades
WHERE 
    (is_passed = 1 AND letter_grade != 'Pass')
    OR (is_passed = 0 AND letter_grade NOT IN ('', NULL))
LIMIT 20;

-- Expected: Should return 0 rows if all data is consistent
