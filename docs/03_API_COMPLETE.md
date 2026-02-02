# 🔌 API - TÀI LIỆU TỔNG HỢP

## 📋 Mục Lục

1. [Backend REST API](#backend-rest-api)
2. [MOOC APIs](#mooc-apis)
3. [H5P APIs](#h5p-apis)
4. [API Requirements](#api-requirements)

---

## 🌐 BACKEND REST API

### Base URL: `http://localhost:5000`

### Endpoints

#### 1. Health Check
```http
GET /api/health
```
**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-01-25T10:00:00",
  "service": "Teacher Dashboard API"
}
```

#### 2. Get Courses
```http
GET /api/courses
```
**Response:**
```json
{
  "courses": [
    {
      "course_id": "course-v1:DHQG-HCM+FM101+2025_S2",
      "student_count": 921
    }
  ],
  "total": 1
}
```

#### 3. Get Students
```http
GET /api/students/{course_id}?risk_level=HIGH&sort_by=risk_score&order=desc
```
**Query Parameters:**
- `risk_level`: HIGH, MEDIUM, LOW (optional)
- `sort_by`: risk_score, name, grade, last_activity
- `order`: desc, asc

**Response:**
```json
{
  "students": [
    {
      "user_id": 123,
      "email": "student@example.com",
      "full_name": "Nguyễn Văn A",
      "fail_risk_score": 85.5,
      "risk_level": "HIGH",
      "mooc_grade_percentage": 35.2,
      "mooc_completion_rate": 25.5,
      "days_since_last_activity": 15
    }
  ],
  "total": 25,
  "course_id": "course-v1:..."
}
```

#### 4. Get Student Detail
```http
GET /api/student/{user_id}/{course_id}
```
**Response:**
```json
{
  "user_id": 123,
  "email": "student@example.com",
  "full_name": "Nguyễn Văn A",
  "username": "student123",
  "mssv": "20120001",
  "fail_risk_score": 85.5,
  "risk_level": "HIGH",
  "suggestions": [
    {
      "icon": "📞",
      "title": "Liên hệ khẩn cấp",
      "description": "Sinh viên không hoạt động 15 ngày...",
      "priority": "high"
    }
  ]
}
```

#### 5. Get Course Statistics
```http
GET /api/statistics/{course_id}
```
**Response:**
```json
{
  "course_id": "course-v1:...",
  "statistics": {
    "total_students": 921,
    "avg_risk_score": 45.2,
    "avg_grade": 72.5,
    "high_risk_count": 150,
    "medium_risk_count": 300,
    "low_risk_count": 471
  }
}
```

#### 6. Record Intervention
```http
POST /api/interventions/{user_id}/{course_id}
Content-Type: application/json

{
  "action": "email_sent",
  "notes": "Đã gửi email nhắc nhở"
}
```

**Xem chi tiết:** `backend/app.py`

---

## 📡 MOOC APIs

### Base URL: `https://mooc.vnuhcm.edu.vn/api/custom/v1`

### Export APIs (Course-Level)

#### 1. Student Grades Export
```http
GET /export/student-grades/{course_id}/
```
**Lưu vào:** `mooc_grades`
**Features:** `mooc_grade_percentage`, `mooc_letter_grade`, `mooc_is_passed`

#### 2. Student Progress Export
```http
GET /export/student-progress/{course_id}/
```
**Lưu vào:** `mooc_progress`
**Features:** `current_chapter`, `current_section`, `mooc_completion_rate`

#### 3. Student Discussions Export
```http
GET /export/student-discussions/{course_id}/
```
**Lưu vào:** `mooc_discussions`
**Features:** `discussion_threads_count`, `discussion_total_interactions`

### Advanced Statistics APIs

#### 1. Activity Statistics
```http
GET /stats/activity/{course_id}/?days=90&module_type=problem
```
**Lưu vào:** `course_stats_benchmarks`
**Features:** `activity_avg_score` (benchmark)

#### 2. Assessment Statistics
```http
GET /stats/assessment/{course_id}/?days=90&min_score=50
```
**Lưu vào:** `course_stats_benchmarks`
**Features:** `assessment_avg_score` (benchmark)

#### 3. Progress Statistics
```http
GET /stats/progress/{course_id}/?days=90&min_progress=50
```
**Lưu vào:** `course_stats_benchmarks`
**Features:** `progress_avg_completion` (benchmark)

**Xem chi tiết:** Folder `hướng dẫn về api mooc_h5p/ADVANCED_STATISTICS_API.md`

---

## 🎯 H5P APIs

### Base URL: `https://h5p.itp.vn/wp-json/mooc/v1`

#### 1. H5P Scores
```http
GET /scores/{user_id}/{course_id}
```
**Lưu vào:** `h5p_scores` + `h5p_scores_summary`
**Features:** `h5p_total_contents`, `h5p_completed_contents`, `quiz_avg_score`

#### 2. Video Progress
```http
GET /video-progress/{user_id}/{course_id}
```
**Lưu vào:** `video_progress` + `video_progress_summary`
**Features:** `video_total_videos`, `video_completed_videos`, `video_completion_rate`

#### 3. Combined Progress
```http
GET /combined-progress/{user_id}/{course_id}
```
**Lưu vào:** `dashboard_summary`
**Features:** `overall_completion`, `total_items`, `completed_items`

**Xem chi tiết:** Folder `hướng dẫn về api mooc_h5p/H5P_MOOC-API-DOCUMENTATION.md`

---

## 📋 API REQUIREMENTS

### APIs Cần Implement (Future)

#### 1. Activity Stats per Student
```http
GET /api/courses/{course_id}/students/{user_id}/activity-stats/?days=90
```
**Trả về:**
- Problem attempts, scores, improvement rate
- Activity consistency
- Time patterns
- Streaks

#### 2. Assessment Details per Student
```http
GET /api/courses/{course_id}/students/{user_id}/assessments/
```
**Trả về:**
- Average attempts to pass
- First attempt vs best score
- Time spent per assessment
- Pass/fail rate

#### 3. Progress Tracking per Student
```http
GET /api/courses/{course_id}/students/{user_id}/progress-weekly/
```
**Trả về:**
- Weekly completion rate
- Velocity (blocks/week)
- Trend (improving/stable/declining)
- On track status

**Xem chi tiết:** `API_REQUIREMENTS_SUMMARY.md`, `API_VISUAL_GUIDE.md`

---

## 🔐 Authentication

### MOOC APIs
- Cần `sessionid` cookie từ browser
- Lấy từ: F12 → Application → Cookies → `sessionid`

### H5P APIs
- Public access (không cần authentication)

### Backend API
- CORS enabled cho frontend
- Không cần authentication (có thể thêm sau)

---

## 📊 Data Flow

```
Frontend → Backend API → Database
    ↓
MOOC/H5P APIs → fetch_mooc_h5p_data.py → Database
    ↓
Database → ML Pipeline → Predictions → Database
```

---

## 🧪 Testing

### Test Backend
```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/courses
curl "http://localhost:5000/api/students/course-v1:...?risk_level=HIGH"
```

### Test MOOC APIs
```bash
# Cần sessionid
curl -H "Cookie: sessionid=YOUR_SESSION_ID" \
  "https://mooc.vnuhcm.edu.vn/api/custom/v1/export/student-grades/course-v1:.../"
```

### Test H5P APIs
```bash
curl "https://h5p.itp.vn/wp-json/mooc/v1/scores/123/course-v1:..."
```

---

## 📚 Tài Liệu Liên Quan

- **Backend API:** `backend/app.py`
- **API Requirements:** `API_REQUIREMENTS_SUMMARY.md`
- **API Visual Guide:** `API_VISUAL_GUIDE.md`
- **API Data Mapping:** `database/API_DATA_MAPPING.md`
- **MOOC API Docs:** Folder `hướng dẫn về api mooc_h5p/`
- **Frontend Connection:** `FRONTEND_BACKEND_CONNECTION_GUIDE.md`

