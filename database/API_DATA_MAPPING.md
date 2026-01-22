# API Data Mapping và Schema Design

## 📋 Tổng quan

Hệ thống sử dụng **2 cách tiếp cận** để lưu data:

1. **Lưu riêng từng bảng** (enrollments, h5p_scores, video_progress, etc.) - **Dễ maintain, debug, query chi tiết**
2. **Aggregate vào raw_data** - **Bảng chính cho training model**

---

## 🔌 APIs Cần Dùng

### 1. H5P APIs (Base: `https://h5p.itp.vn/wp-json/mooc/v1`)

#### 1.1. H5P Scores API
```
GET /scores/{user_id}/{course_id}
```
**Mục đích:** Lấy điểm số H5P của user
- **Lưu vào:** `h5p_scores` (chi tiết từng content) + `h5p_scores_summary` (tổng hợp)
- **Features cho raw_data:**
  - `h5p_total_contents`, `h5p_completed_contents`
  - `h5p_total_score`, `h5p_total_max_score`
  - `h5p_overall_percentage`
  - `h5p_total_time_spent`
  - `h5p_completion_rate` (calculated)
  - `quiz_attempts`, `quiz_avg_score`, `quiz_completion_rate` (từ H5P scores)

#### 1.2. Video Progress API
```
GET /video-progress/{user_id}/{course_id}
```
**Mục đích:** Lấy tiến độ xem video
- **Lưu vào:** `video_progress` (chi tiết từng video) + `video_progress_summary` (tổng hợp)
- **Features cho raw_data:**
  - `video_total_videos`, `video_completed_videos`, `video_in_progress_videos`
  - `video_total_duration`, `video_total_watched_time`
  - `video_completion_rate` (calculated)
  - `video_watch_rate` (calculated: watched_time/total_duration)

#### 1.3. Dashboard API
```
GET /dashboard/{user_id}/{course_id}
```
**Mục đích:** Tổng hợp toàn bộ tiến độ học tập
- **Lưu vào:** `dashboard_summary`
- **Features cho raw_data:**
  - `overall_completion`, `total_items`, `completed_items`
  - Tổng hợp từ H5P và Video stats

#### 1.4. Combined Progress API (Optional)
```
GET /combined-progress/{user_id}/{course_id}
```
**Mục đích:** Tổng hợp video + scores trong 1 API
- Có thể dùng thay vì gọi riêng scores và video

---

### 2. MOOC APIs (Base: `https://mooc.vnuhcm.edu.vn/api/custom/v1`)

#### 2.1. Course Enrollments Attributes API
```
GET /course-enrollments-attributes/{course_id}/?limit={limit}&offset={offset}
```
**Mục đích:** Lấy danh sách học viên trong course
- **Lưu vào:** `enrollments`
- **Features cho raw_data:**
  - `enrollment_date`, `enrollment_mode`, `is_active`
  - `weeks_since_enrollment` (calculated)

#### 2.2. Student Grades Export API ⭐ NEW
```
GET /export/student-grades/{course_id}/
```
**Mục đích:** Xuất điểm số MOOC của tất cả học sinh
- **Lưu vào:** `mooc_grades` (bảng mới)
- **Features cho raw_data:**
  - `mooc_grade_percentage`, `mooc_letter_grade`, `mooc_is_passed`
- **Query params:** `email_filter`, `sort_by`, `sort_order`

#### 2.3. Student Progress Export API ⭐ NEW
```
GET /export/student-progress/{course_id}/
```
**Mục đích:** Xuất tiến độ học tập chi tiết (chapter/section/unit)
- **Lưu vào:** `mooc_progress` (cập nhật với columns mới)
- **Features cho raw_data:**
  - `current_chapter`, `current_section`, `current_unit`
  - `mooc_completion_rate`
- **Query params:** `email_filter`, `sort_by`, `sort_order`

#### 2.4. Student Discussions Export API ⭐ NEW
```
GET /export/student-discussions/{course_id}/
```
**Mục đích:** Xuất tương tác discussion/forum
- **Lưu vào:** `mooc_discussions` (bảng mới)
- **Features cho raw_data:**
  - `discussion_threads_count`, `discussion_comments_count`
  - `discussion_total_interactions`, `discussion_questions_count`, `discussion_total_upvotes`
- **Query params:** `email_filter`, `sort_by`, `sort_order`

#### 2.5. Complete Student Data Export API ⭐ NEW
```
GET /export/complete-student-data/{course_id}/
```
**Mục đích:** Tổng hợp TẤT CẢ dữ liệu (Grades + Progress + Discussions) + H5P
- **Lưu vào:** Aggregate từ tất cả bảng trên
- **Features:** Bao gồm tất cả features từ API 2.2, 2.3, 2.4 trên
- **Query params:** `email_filter`, `sort_by`, `sort_order`
- **Note:** API này có thể thay thế cho việc gọi riêng 3 API trên

#### 2.6. Progress Statistics API (Legacy)
```
GET /stats/progress/{course_id}/
```
**Mục đích:** Lấy tiến độ từ MOOC (aggregate stats)
- **Lưu vào:** `mooc_progress` (nếu có per-user data)
- **Features cho raw_data:**
  - `progress_percent`, `total_blocks`, `completed_blocks`
  - `last_activity`, `days_since_last_activity` (calculated)

**Lưu ý:** API này có thể chỉ trả về aggregate stats, không có per-user. Cần kiểm tra response structure.

#### 2.7. Activity Statistics API (Optional)
```
GET /stats/activity/{course_id}/?module_type={type}
```
**Mục đích:** Thống kê hoạt động (nếu có per-user data)
- Có thể dùng để tính `access_frequency`, `active_days`

#### 2.8. Assessment Statistics API (Optional)
```
GET /stats/assessment/{course_id}/
```
**Mục đích:** Thống kê bài kiểm tra (nếu có per-user data)
- Có thể dùng để bổ sung quiz features

---

## 📊 Schema Design

### Cấu trúc Database (Updated)

```
enrollments (Table 1)
    ↓
h5p_scores (Table 2) → h5p_scores_summary (Table 3)
    ↓
video_progress (Table 4) → video_progress_summary (Table 5)
    ↓
dashboard_summary (Table 6)
    ↓
mooc_progress (Table 7) ⭐ Updated - added current_chapter/section/unit
    ↓
mooc_grades (Table 8) ⭐ NEW - MOOC điểm số
    ↓
mooc_discussions (Table 9) ⭐ NEW - MOOC tương tác
    ↓
raw_data (Table 10) ⭐ Updated - thêm 13 columns mới
```

### Quy trình xử lý data:

1. **Fetch từ APIs** → Lưu vào các bảng chi tiết (enrollments, h5p_scores, video_progress, etc.)
2. **Aggregate/Calculate** → Tính toán các features từ bảng chi tiết
3. **Insert vào raw_data** → Tổng hợp tất cả features cho training

---

## 🎯 Features trong raw_data

### Enrollment Features
- `enrollment_date`, `enrollment_mode`, `is_active`
- `weeks_since_enrollment` (calculated)

### Progress Features
- `progress_percent`, `overall_completion`
- `completed_blocks`, `total_blocks`
- `last_activity`, `days_since_last_activity` (calculated)

### Activity Features
- `access_frequency` (times per week)
- `active_days` (số ngày có hoạt động)

### H5P/Quiz Features
- `h5p_total_contents`, `h5p_completed_contents`
- `h5p_total_score`, `h5p_total_max_score`
- `h5p_overall_percentage`
- `h5p_total_time_spent`
- `h5p_completion_rate` (completed/total)
- `quiz_attempts`, `quiz_avg_score`, `quiz_completion_rate`

### Video Features
- `video_total_videos`, `video_completed_videos`, `video_in_progress_videos`
- `video_total_duration`, `video_total_watched_time`
- `video_completion_rate` (completed/total)
- `video_watch_rate` (watched_time/total_duration)

### Forum Features (TODO: nếu có API)
- `forum_posts`, `forum_comments`, `forum_upvotes`

### Calculated Features
- `is_passed` (progress_percent >= 50)
- `dropout_risk_score` (tính từ các features khác)

---

## 🔄 Quy trình Fetch và Aggregate

### Bước 1: Fetch từ APIs
```python
# 1. Fetch enrollments (đã có)
enrollments = fetch_mooc_course_students(course_id)

# 2. Với mỗi user_id, fetch:
for user_id in user_ids:
    # H5P Scores
    h5p_data = fetch_h5p_scores(user_id, course_id)
    save_h5p_scores(h5p_data)  # → h5p_scores + h5p_scores_summary
    
    # Video Progress
    video_data = fetch_video_progress(user_id, course_id)
    save_video_progress(video_data)  # → video_progress + video_progress_summary
    
    # Dashboard
    dashboard_data = fetch_dashboard(user_id, course_id)
    save_dashboard_summary(dashboard_data)  # → dashboard_summary
    
    # MOOC Progress (nếu có API per-user)
    mooc_progress_data = fetch_mooc_progress(user_id, course_id)
    save_mooc_progress(mooc_progress_data)  # → mooc_progress
```

### Bước 2: Aggregate vào raw_data
```python
# Aggregate từ các bảng trên
for user_id in user_ids:
    # Lấy data từ các bảng
    enrollment = get_enrollment(user_id, course_id)
    h5p_summary = get_h5p_scores_summary(user_id, course_id)
    video_summary = get_video_progress_summary(user_id, course_id)
    dashboard = get_dashboard_summary(user_id, course_id)
    mooc_progress = get_mooc_progress(user_id, course_id)
    
    # Tính toán features
    features = calculate_features(
        enrollment, h5p_summary, video_summary, 
        dashboard, mooc_progress
    )
    
    # Insert vào raw_data
    save_raw_data(features)
```

---

## ✅ Lợi ích của cách tiếp cận này

1. **Dễ maintain:** Mỗi bảng có mục đích rõ ràng
2. **Dễ debug:** Có thể kiểm tra từng nguồn data riêng
3. **Linh hoạt:** Có thể tính lại raw_data nếu cần
4. **Query chi tiết:** Có thể query chi tiết từng content/video
5. **Mở rộng dễ:** Thêm API mới chỉ cần thêm bảng mới

---

## 📝 Next Steps

1. ✅ Tạo schema với các bảng trên
2. ⏳ Implement fetch functions cho từng API
3. ⏳ Implement save functions cho từng bảng
4. ⏳ Implement aggregate function để tính raw_data
5. ⏳ Test với data thực tế



