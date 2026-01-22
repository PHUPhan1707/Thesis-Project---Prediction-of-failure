# MOOC Export Tables Migration

## Overview

Thư mục này chứa migration scripts để thêm database schema cho MOOC Export APIs.

## Migration Scripts

### Individual Migrations

1. **`01_create_mooc_grades.sql`**
   - Tạo bảng `mooc_grades`
   - Lưu điểm số MOOC từ API `/api/custom/v1/export/student-grades/`

2. **`02_update_mooc_progress.sql`**
   - Cập nhật bảng `mooc_progress`  
   - Thêm columns: `current_chapter`, `current_section`, `current_unit`, `completion_rate`

3. **`03_create_mooc_discussions.sql`**
   - Tạo bảng `mooc_discussions`
   - Lưu tương tác discussion từ API `/api/custom/v1/export/student-discussions/`

4. **`04_update_raw_data.sql`**
   - Cập nhật bảng `raw_data`
   - Thêm các features từ MOOC grades, progress, discussions

### Master Migration

- **`add_mooc_export_tables.sql`**
  - Script tổng hợp tất cả migrations ở trên
  - Running trong 1 transaction
  - **Recommended:** Chạy script này thay vì chạy từng script riêng lẻ

### Rollback

- **`rollback_mooc_export_tables.sql`**
  - Undo tất cả thay đổi từ migration
  - ⚠️ **WARNING:** Sẽ xóa data, backup trước khi chạy

## Usage

### Chạy Migration

```bash
# Option 1: Chạy master migration (recommended)
mysql -u root -p dropout_prediction_db < migrations/add_mooc_export_tables.sql

# Option 2: Chạy từng migration riêng lẻ (nếu cần kiểm soát chi tiết)
mysql -u root -p dropout_prediction_db < migrations/01_create_mooc_grades.sql
mysql -u root -p dropout_prediction_db < migrations/02_update_mooc_progress.sql
mysql -u root -p dropout_prediction_db < migrations/03_create_mooc_discussions.sql
mysql -u root -p dropout_prediction_db < migrations/04_update_raw_data.sql
```

### Rollback (Nếu Cần)

```bash
mysql -u root -p dropout_prediction_db < migrations/rollback_mooc_export_tables.sql
```

## Verification

Sau khi chạy migration, verify schema:

```sql
-- Check tables created
SHOW TABLES LIKE 'mooc_%';

-- Check mooc_grades structure
DESCRIBE mooc_grades;

-- Check mooc_discussions structure
DESCRIBE mooc_discussions;

-- Check mooc_progress new columns
SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'dropout_prediction_db' 
  AND TABLE_NAME = 'mooc_progress'
  AND COLUMN_NAME IN ('current_chapter', 'current_section', 'current_unit', 'completion_rate');

-- Check raw_data new columns
SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'dropout_prediction_db' 
  AND TABLE_NAME = 'raw_data'
  AND (COLUMN_NAME LIKE 'mooc_%' OR COLUMN_NAME LIKE 'discussion_%' OR COLUMN_NAME LIKE 'current_%');
```

## Schema Summary

### New Tables

#### `mooc_grades`
```
- user_id, course_id
- username, email, full_name
- percent_grade, grade_percentage
- letter_grade: "Pass" nếu is_passed=true, "" (empty) nếu is_passed=false
- is_passed
- fetched_at, updated_at
```

#### `mooc_discussions`
```
- user_id, course_id
- username, email, full_name
- threads_count, comments_count, total_interactions
- questions_count, total_upvotes
- fetched_at, updated_at
```

### Updated Tables

#### `mooc_progress` (added columns)
```
+ current_chapter
+ current_section
+ current_unit
+ completion_rate
```

#### `raw_data` (added columns)
```
MOOC Grades:
+ mooc_grade_percentage
+ mooc_letter_grade
+ mooc_is_passed

MOOC Progress:
+ current_chapter
+ current_section
+ current_unit
+ mooc_completion_rate

MOOC Discussions:
+ discussion_threads_count
+ discussion_comments_count
+ discussion_total_interactions
+ discussion_questions_count
+ discussion_total_upvotes
```

## Next Steps

Sau khi migration, cập nhật `storage_manager.py` để thêm functions:

1. `save_mooc_grades(user_id, course_id, data)`
2. `save_mooc_discussions(user_id, course_id, data)`
3. `update_mooc_progress_details(user_id, course_id, data)`
4. `aggregate_raw_data_with_mooc_apis(user_id, course_id)`
