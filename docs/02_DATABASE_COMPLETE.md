# 📊 DATABASE - TÀI LIỆU TỔNG HỢP

## 📋 Mục Lục

1. [Schema & ERD](#schema--erd)
2. [Thu Thập Dữ Liệu](#thu-thập-dữ-liệu)
3. [API Data Mapping](#api-data-mapping)
4. [Migrations](#migrations)
5. [Queries Thường Dùng](#queries-thường-dùng)

---

## 🗄️ SCHEMA & ERD

### Database: `dropout_prediction_db`

**Connection Config:**
```python
DB_CONFIG = {
    "host": "localhost",
    "port": 4000,
    "database": "dropout_prediction_db",
    "user": "dropout_user",
    "password": "dropout_pass_123"
}
```

### Cấu Trúc Bảng

#### 1. **enrollments** - Thông tin đăng ký
- `user_id`, `course_id`, `username`, `email`, `full_name`
- `enrollment_id`, `mode`, `is_active`, `created`
- `mssv`, `class_code`, `department`, `faculty`

#### 2. **raw_data** - Bảng chính cho ML (aggregated)
- Tất cả features từ các bảng khác
- `fail_risk_score`, `dropout_risk_score` (predictions)
- `is_passed`, `is_dropout` (labels)

#### 3. **h5p_scores** - Điểm H5P chi tiết
- `content_id`, `score`, `max_score`, `percentage`
- `opened`, `finished`, `time_spent`

#### 4. **h5p_scores_summary** - Tổng hợp H5P
- `total_contents`, `completed_contents`
- `total_score`, `overall_percentage`

#### 5. **video_progress** - Tiến độ video chi tiết
- `content_id`, `progress_percent`, `current_time`, `duration`
- `status` (completed, in_progress, not_started)

#### 6. **video_progress_summary** - Tổng hợp video
- `total_videos`, `completed_videos`, `in_progress_videos`
- `total_duration`, `total_watched_time`, `overall_progress`

#### 7. **mooc_grades** - Điểm số MOOC
- `grade_percentage`, `letter_grade`, `is_passed`

#### 8. **mooc_progress** - Tiến độ MOOC
- `current_chapter`, `current_section`, `current_unit`
- `completion_rate`, `last_activity`

#### 9. **mooc_discussions** - Thảo luận
- `threads_count`, `comments_count`, `total_interactions`
- `questions_count`, `total_upvotes`

#### 10. **dashboard_summary** - Tổng hợp dashboard
- `overall_completion`, `total_items`, `completed_items`
- Tổng hợp từ H5P và Video

#### 11. **course_stats_benchmarks** - Benchmark khóa học
- `activity_avg_score`, `assessment_avg_score`
- `progress_avg_completion`, `total_students`

### ERD Diagram

```
enrollments (1) ──→ (N) raw_data
enrollments (1) ──→ (N) mooc_grades
enrollments (1) ──→ (N) mooc_progress
enrollments (1) ──→ (N) mooc_discussions
enrollments (1) ──→ (N) h5p_scores_summary
enrollments (1) ──→ (N) video_progress_summary
enrollments (1) ──→ (N) dashboard_summary

h5p_scores (N) ──→ (1) h5p_scores_summary
video_progress (N) ──→ (1) video_progress_summary
```

**Xem chi tiết:** `database/ERD_DIAGRAM.md`

---

## 📥 THU THẬP DỮ LIỆU

### File: `database/fetch_mooc_h5p_data.py`

**Mục đích:** Thu thập dữ liệu từ MOOC và H5P APIs, lưu vào database

### Workflow

```
1. Fetch Enrollments
   └─→ API: /course-enrollments-attributes/{course_id}/
   └─→ Lưu vào: enrollments

2. Fetch MOOC Export Data (course-level)
   ├─→ /export/student-grades/{course_id}/ → mooc_grades
   ├─→ /export/student-progress/{course_id}/ → mooc_progress
   └─→ /export/student-discussions/{course_id}/ → mooc_discussions

3. Fetch H5P Data (per-user)
   ├─→ /scores/{user_id}/{course_id} → h5p_scores + h5p_scores_summary
   ├─→ /video-progress/{user_id}/{course_id} → video_progress + video_progress_summary
   └─→ /combined-progress/{user_id}/{course_id} → dashboard_summary

4. Aggregate vào raw_data
   └─→ Tổng hợp tất cả data từ các bảng → raw_data
```

### Cách Sử Dụng

```bash
# Fetch tất cả data
python fetch_mooc_h5p_data.py \
    --course-id "course-v1:DHQG-HCM+FM101+2025_S2" \
    --sessionid "YOUR_SESSION_ID" \
    --delay 0.5

# Chỉ aggregate từ data đã có
python fetch_mooc_h5p_data.py \
    --aggregate-only \
    --course-id "course-v1:DHQG-HCM+FM101+2025_S2"

# Giới hạn số users (để test)
python fetch_mooc_h5p_data.py \
    --course-id "course-v1:..." \
    --max-users 10
```

**Xem chi tiết:** `database/GIAI_THICH_FETCH_DATA.md`

---

## 🔌 API DATA MAPPING

### H5P APIs (Base: `https://h5p.itp.vn/wp-json/mooc/v1`)

| API Endpoint | Bảng Lưu | Features cho raw_data |
|--------------|-----------|---------------------|
| `/scores/{user_id}/{course_id}` | `h5p_scores` + `h5p_scores_summary` | `h5p_total_contents`, `h5p_completed_contents`, `h5p_overall_percentage`, `quiz_avg_score` |
| `/video-progress/{user_id}/{course_id}` | `video_progress` + `video_progress_summary` | `video_total_videos`, `video_completed_videos`, `video_completion_rate` |
| `/combined-progress/{user_id}/{course_id}` | `dashboard_summary` | `overall_completion`, `total_items`, `completed_items` |

### MOOC APIs (Base: `https://mooc.vnuhcm.edu.vn/api/custom/v1`)

| API Endpoint | Bảng Lưu | Features cho raw_data |
|--------------|-----------|---------------------|
| `/course-enrollments-attributes/{course_id}/` | `enrollments` | `enrollment_mode`, `is_active`, `weeks_since_enrollment` |
| `/export/student-grades/{course_id}/` | `mooc_grades` | `mooc_grade_percentage`, `mooc_letter_grade`, `mooc_is_passed` |
| `/export/student-progress/{course_id}/` | `mooc_progress` | `current_chapter`, `current_section`, `mooc_completion_rate` |
| `/export/student-discussions/{course_id}/` | `mooc_discussions` | `discussion_threads_count`, `discussion_total_interactions` |
| `/stats/activity/{course_id}/` | `course_stats_benchmarks` | `activity_avg_score` (benchmark) |
| `/stats/assessment/{course_id}/` | `course_stats_benchmarks` | `assessment_avg_score` (benchmark) |
| `/stats/progress/{course_id}/` | `course_stats_benchmarks` | `progress_avg_completion` (benchmark) |

**Xem chi tiết:** `database/API_DATA_MAPPING.md`

---

## 🔄 MIGRATIONS

### Thư Mục: `database/migrations/`

### Migration Scripts

1. **`01_create_mooc_grades.sql`** - Tạo bảng `mooc_grades`
2. **`02_update_mooc_progress.sql`** - Thêm columns cho `mooc_progress`
3. **`03_create_mooc_discussions.sql`** - Tạo bảng `mooc_discussions`
4. **`04_update_raw_data.sql`** - Thêm features vào `raw_data`
5. **`05_remove_enrollment_date.sql`** - Cleanup
6. **`06_create_activity_tables.sql`** - Tạo bảng activity (future)
7. **`07_add_course_benchmarks.sql`** - Tạo bảng `course_stats_benchmarks`

### Master Migration

```bash
# Chạy tất cả migrations
mysql -h localhost -P 4000 -u dropout_user -p dropout_prediction_db \
    < database/migrations/add_mooc_export_tables.sql
```

### Rollback

```bash
# Undo migrations
mysql -h localhost -P 4000 -u dropout_user -p dropout_prediction_db \
    < database/migrations/rollback_mooc_export_tables.sql
```

**Xem chi tiết:** `database/migrations/README.md`

---

## 📊 QUERIES THƯỜNG DÙNG

### 1. Kiểm Tra Dữ Liệu

```sql
-- Số lượng records
SELECT COUNT(*) FROM raw_data;
SELECT COUNT(*) FROM enrollments;
SELECT DISTINCT course_id FROM raw_data;

-- Kiểm tra predictions
SELECT 
    COUNT(*) as total,
    AVG(fail_risk_score) as avg_risk,
    SUM(CASE WHEN fail_risk_score >= 70 THEN 1 ELSE 0 END) as high_risk
FROM raw_data
WHERE course_id = 'course-v1:...';
```

### 2. Top Risk Students

```sql
SELECT 
    r.user_id,
    e.full_name,
    e.email,
    r.fail_risk_score,
    r.mooc_grade_percentage,
    r.mooc_completion_rate
FROM raw_data r
JOIN enrollments e ON r.user_id = e.user_id AND r.course_id = e.course_id
WHERE r.course_id = 'course-v1:...'
ORDER BY r.fail_risk_score DESC
LIMIT 10;
```

### 3. Statistics

```sql
SELECT 
    COUNT(*) as total_students,
    AVG(fail_risk_score) as avg_risk,
    AVG(mooc_grade_percentage) as avg_grade,
    AVG(mooc_completion_rate) as avg_completion,
    SUM(CASE WHEN fail_risk_score >= 70 THEN 1 ELSE 0 END) as high_risk,
    SUM(CASE WHEN days_since_last_activity > 7 THEN 1 ELSE 0 END) as inactive
FROM raw_data
WHERE course_id = 'course-v1:...';
```

### 4. Data Quality Check

```sql
-- Kiểm tra missing data
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN fail_risk_score IS NULL THEN 1 ELSE 0 END) as missing_risk,
    SUM(CASE WHEN mooc_grade_percentage IS NULL THEN 1 ELSE 0 END) as missing_grade,
    SUM(CASE WHEN mooc_completion_rate IS NULL THEN 1 ELSE 0 END) as missing_completion
FROM raw_data
WHERE course_id = 'course-v1:...';
```

---

## 🔧 UTILITIES

### Storage Manager

File: `database/storage_manager.py`

**Functions:**
- `save_enrollment()`
- `save_h5p_scores()`
- `save_video_progress()`
- `save_mooc_grades()`
- `save_mooc_progress()`
- `save_mooc_discussions()`
- `aggregate_raw_data()`

### Advanced Stats Functions

File: `database/advanced_stats_functions.py`

**Functions:**
- `fetch_activity_stats()`
- `fetch_assessment_stats()`
- `fetch_progress_stats()`
- `save_course_benchmarks()`

---

## 📝 NOTES

### Data Flow

```
APIs → Raw Tables → Summary Tables → raw_data → ML Features
```

### Best Practices

1. **Luôn aggregate sau khi fetch** - Đảm bảo `raw_data` được update
2. **Sử dụng batch_id** - Track data extraction batches
3. **Backup trước khi migration** - Tránh mất dữ liệu
4. **Index các columns thường query** - `user_id`, `course_id`

### Troubleshooting

**Lỗi: "Table doesn't exist"**
```bash
# Chạy schema
mysql -h localhost -P 4000 -u dropout_user -p dropout_prediction_db < database/schema.sql
```

**Lỗi: "Column doesn't exist"**
```bash
# Chạy migrations
mysql -h localhost -P 4000 -u dropout_user -p dropout_prediction_db < database/migrations/add_mooc_export_tables.sql
```

---

## 📚 Tài Liệu Liên Quan

- **Schema:** `database/schema.sql`
- **ERD:** `database/ERD_DIAGRAM.md`
- **Fetch Data:** `database/GIAI_THICH_FETCH_DATA.md`
- **API Mapping:** `database/API_DATA_MAPPING.md`
- **Migrations:** `database/migrations/README.md`

