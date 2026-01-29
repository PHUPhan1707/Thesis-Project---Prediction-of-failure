# 🧪 TEST BACKEND API

## ✅ Đã hoàn thành:
- ✅ `backend/app.py` - Flask application với 8 endpoints
- ✅ `backend/db.py` - Database helper functions
- ✅ `backend/model_v4_service.py` - Model V4 integration
- ✅ `backend/__init__.py` - Package marker

## 🚀 Cách chạy Backend:

### 1. Activate virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install dependencies (nếu chưa có):
```bash
pip install flask flask-cors mysql-connector-python pandas catboost
```

### 3. Chạy backend:
```bash
# Option 1: Module style (recommended)
python -m backend.app

# Option 2: Direct script
python backend/app.py
```

Backend sẽ chạy tại: `http://localhost:5000`

---

## 📋 API Endpoints:

### 1. Health Check
```bash
curl http://localhost:5000/api/health
```
**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-01-29T03:00:00",
  "service": "Teacher Dashboard API"
}
```

### 2. Get Courses
```bash
curl http://localhost:5000/api/courses
```
**Response:**
```json
{
  "courses": [
    {"course_id": "course-v1:DHQG-HCM+FM101+2025_S2", "student_count": 5}
  ],
  "total": 1
}
```

### 3. Get Students (All)
```bash
curl "http://localhost:5000/api/students/course-v1:DHQG-HCM+FM101+2025_S2"
```

### 4. Get Students (HIGH risk only)
```bash
curl "http://localhost:5000/api/students/course-v1:DHQG-HCM+FM101+2025_S2?risk_level=HIGH"
```

### 5. Get Students (Sorted by grade)
```bash
curl "http://localhost:5000/api/students/course-v1:DHQG-HCM+FM101+2025_S2?sort_by=grade&order=desc"
```

**Query Parameters:**
- `risk_level`: `HIGH`, `MEDIUM`, `LOW`, or omit for all
- `sort_by`: `risk_score`, `name`, `grade`, `last_activity`
- `order`: `desc`, `asc`

**Response:**
```json
{
  "students": [
    {
      "user_id": 4,
      "email": "levanluan20112003@gmail.com",
      "full_name": "vănluân lê",
      "username": "levanluan_8",
      "mssv": null,
      "fail_risk_score": null,
      "mooc_grade_percentage": 0,
      "mooc_completion_rate": 0,
      "days_since_last_activity": 17,
      "risk_level": "LOW"
    }
  ],
  "total": 5,
  "course_id": "course-v1:DHQG-HCM+FM101+2025_S2"
}
```

### 6. Get Student Detail
```bash
curl "http://localhost:5000/api/student/4/course-v1:DHQG-HCM+FM101+2025_S2"
```

**Response:**
```json
{
  "user_id": 4,
  "email": "levanluan20112003@gmail.com",
  "full_name": "vănluân lê",
  "username": "levanluan_8",
  "mssv": null,
  "fail_risk_score": 0,
  "risk_level": "LOW",
  "mooc_grade_percentage": 0,
  "mooc_completion_rate": 0,
  "days_since_last_activity": 17,
  "video_completion_rate": 0,
  "quiz_avg_score": 0,
  "discussion_threads_count": 0,
  "suggestions": [
    {
      "icon": "📞",
      "title": "Liên hệ khẩn cấp",
      "description": "Sinh viên không hoạt động 17 ngày, cần liên hệ ngay để tìm hiểu khó khăn.",
      "priority": "high"
    }
  ]
}
```

### 7. Get Course Statistics
```bash
curl "http://localhost:5000/api/statistics/course-v1:DHQG-HCM+FM101+2025_S2"
```

**Response:**
```json
{
  "course_id": "course-v1:DHQG-HCM+FM101+2025_S2",
  "statistics": {
    "total_students": 5,
    "avg_risk_score": 0,
    "avg_grade": 0,
    "avg_completion_rate": 0,
    "high_risk_count": 0,
    "medium_risk_count": 0,
    "low_risk_count": 5
  }
}
```

### 8. Record Intervention
```bash
curl -X POST "http://localhost:5000/api/interventions/4/course-v1:DHQG-HCM+FM101+2025_S2" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "Email nhắc nhở",
    "notes": "Đã gửi email nhắc sinh viên quay lại học"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Intervention recorded successfully",
  "user_id": 4,
  "course_id": "course-v1:DHQG-HCM+FM101+2025_S2",
  "action": "Email nhắc nhở"
}
```

### 9. Predict with Model V4 (All students in course)
```bash
curl "http://localhost:5000/api/predict-v4/course-v1:DHQG-HCM+FM101+2025_S2?save_db=1"
```

**Query Parameters:**
- `save_db`: `0` (không lưu) hoặc `1` (lưu vào database)

**Response:**
```json
{
  "success": true,
  "model": "fm101_model_v4",
  "course_id": "course-v1:DHQG-HCM+FM101+2025_S2",
  "total": 5,
  "students": [...],
  "saved_to_db": true
}
```

### 10. Predict with Model V4 (Single student)
```bash
curl "http://localhost:5000/api/predict-v4/4/course-v1:DHQG-HCM+FM101+2025_S2?save_db=1"
```

---

## 🔍 Troubleshooting:

### Lỗi: `ModuleNotFoundError: No module named 'flask'`
**Giải pháp:**
```bash
pip install flask flask-cors mysql-connector-python pandas catboost
```

### Lỗi: Database connection failed
**Kiểm tra:**
1. MySQL đang chạy (port 4000)
2. Database `dropout_prediction_db` tồn tại
3. User `dropout_user` có quyền truy cập

### Lỗi: Model not found
**Kiểm tra:**
```bash
ls models/fm101_model_v4.cbm
```
Nếu file không tồn tại, cần train model trước.

### Lỗi: Empty student list (full_name = null)
**Nguyên nhân:** Bảng `enrollments` hoặc `mooc_grades` chưa có dữ liệu tên sinh viên.

**Giải pháp:** Chạy script fetch data để populate các bảng này.

---

## 📊 Database Requirements:

Backend cần các bảng sau trong database:
- ✅ `raw_data` - Dữ liệu tổng hợp cho ML
- ✅ `enrollments` - Thông tin đăng ký sinh viên
- ✅ `mooc_grades` - Điểm số MOOC
- ✅ `interventions` - Ghi nhận can thiệp (tự động tạo nếu chưa có)

---

## 🎯 Testing Checklist:

- [ ] Backend starts without errors
- [ ] `/api/health` returns 200 OK
- [ ] `/api/courses` returns course list
- [ ] `/api/students/<course_id>` returns student list with names
- [ ] `/api/student/<user_id>/<course_id>` returns detail with suggestions
- [ ] `/api/statistics/<course_id>` returns correct stats
- [ ] `/api/interventions` can save records
- [ ] `/api/predict-v4` works (if model trained)
- [ ] Frontend can connect to backend
- [ ] CORS is working properly

---

## 🔗 Environment Variables (Optional):

Bạn có thể tùy chỉnh config bằng environment variables:

```bash
# Database
export DB_HOST=localhost
export DB_PORT=4000
export DB_NAME=dropout_prediction_db
export DB_USER=dropout_user
export DB_PASSWORD=dropout_pass_123

# Server
export PORT=5000

# Model paths (optional)
export MODEL_V4_PATH=models/fm101_model_v4.cbm
export MODEL_V4_FEATURES_CSV=models/fm101_model_v4_feature_importance.csv
```

---

## ✅ Next Steps:

1. ✅ Start backend: `python -m backend.app`
2. ✅ Test health check: `curl http://localhost:5000/api/health`
3. ✅ Start frontend: `cd frontend && npm run dev`
4. ✅ Open browser: `http://localhost:5173`
5. ✅ Verify student names are displayed
6. ✅ Test all features in dashboard

**Chúc mừng! Backend đã sẵn sàng! 🎉**

