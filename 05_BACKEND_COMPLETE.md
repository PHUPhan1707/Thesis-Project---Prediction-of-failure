# ⚙️ BACKEND - TÀI LIỆU TỔNG HỢP

## 📋 Mục Lục

1. [Overview](#overview)
2. [API Endpoints](#api-endpoints)
3. [Database Integration](#database-integration)
4. [Error Handling](#error-handling)
5. [Deployment](#deployment)

---

## 🎯 OVERVIEW

### Technology Stack

- **Framework:** Flask
- **Database:** MySQL (mysql-connector-python)
- **CORS:** flask-cors
- **Data Processing:** pandas

### File Structure

```
backend/
├── app.py                    # Main Flask application
└── requirements_backend.txt  # Dependencies
```

### Configuration

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 4000,
    "database": "dropout_prediction_db",
    "user": "dropout_user",
    "password": "dropout_pass_123"
}
```

---

## 🔌 API ENDPOINTS

### Base URL: `http://localhost:5000`

### 1. Health Check
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

### 2. Get Courses
```http
GET /api/courses
```
**Query:** `SELECT DISTINCT course_id, COUNT(*) FROM raw_data GROUP BY course_id`

**Response:**
```json
{
  "courses": [
    {"course_id": "course-v1:...", "student_count": 921}
  ],
  "total": 1
}
```

### 3. Get Students
```http
GET /api/students/{course_id}?risk_level=HIGH&sort_by=risk_score&order=desc
```
**Query Parameters:**
- `risk_level`: HIGH, MEDIUM, LOW
- `sort_by`: risk_score, name, grade, last_activity
- `order`: desc, asc

**Query:**
```sql
SELECT 
    r.user_id, e.email, e.full_name,
    r.fail_risk_score, r.mooc_grade_percentage,
    r.mooc_completion_rate, r.days_since_last_activity
FROM raw_data r
LEFT JOIN enrollments e ON r.user_id = e.user_id AND r.course_id = e.course_id
WHERE r.course_id = %s
AND r.fail_risk_score >= 70  -- if risk_level=HIGH
ORDER BY r.fail_risk_score DESC
```

**Response:**
```json
{
  "students": [...],
  "total": 25,
  "course_id": "course-v1:..."
}
```

### 4. Get Student Detail
```http
GET /api/student/{user_id}/{course_id}
```
**Query:**
```sql
SELECT r.*, e.*
FROM raw_data r
LEFT JOIN enrollments e ON r.user_id = e.user_id AND r.course_id = e.course_id
WHERE r.user_id = %s AND r.course_id = %s
```

**Response:**
```json
{
  "user_id": 123,
  "email": "student@example.com",
  "full_name": "Nguyễn Văn A",
  "fail_risk_score": 85.5,
  "risk_level": "HIGH",
  "suggestions": [...]
}
```

### 5. Get Course Statistics
```http
GET /api/statistics/{course_id}
```
**Query:**
```sql
SELECT 
    COUNT(*) as total_students,
    AVG(fail_risk_score) as avg_risk_score,
    AVG(mooc_grade_percentage) as avg_grade,
    AVG(mooc_completion_rate) as avg_completion_rate,
    SUM(CASE WHEN fail_risk_score >= 70 THEN 1 ELSE 0 END) as high_risk_count,
    SUM(CASE WHEN fail_risk_score >= 40 AND fail_risk_score < 70 THEN 1 ELSE 0 END) as medium_risk_count,
    SUM(CASE WHEN fail_risk_score < 40 THEN 1 ELSE 0 END) as low_risk_count
FROM raw_data
WHERE course_id = %s
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

### 6. Record Intervention
```http
POST /api/interventions/{user_id}/{course_id}
Content-Type: application/json

{
  "action": "email_sent",
  "notes": "Đã gửi email nhắc nhở"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Intervention recorded successfully",
  "user_id": 123,
  "course_id": "course-v1:...",
  "action": "email_sent"
}
```

---

## 🗄️ DATABASE INTEGRATION

### Connection Helper

```python
def get_db_connection():
    """Tạo kết nối database"""
    return mysql.connector.connect(**DB_CONFIG)

def execute_query(query: str, params: tuple = None) -> Optional[List[Dict]]:
    """Execute query và trả về results as list of dicts"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, params or ())
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return results
```

### Tables Used

- `raw_data` - Main table với predictions
- `enrollments` - Student enrollment info
- `mooc_grades` - Grades
- `mooc_progress` - Progress
- `mooc_discussions` - Discussions

---

## 🛡️ ERROR HANDLING

### Database Errors

```python
try:
    results = execute_query(query, params)
    if results is None:
        return jsonify({"error": "Database connection failed"}), 500
except Error as e:
    logger.error(f"Database error: {e}")
    return jsonify({"error": "Database error"}), 500
```

### Not Found Errors

```python
if not results:
    return jsonify({"error": "Student not found"}), 404
```

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

---

## 🚀 DEPLOYMENT

### Development

```bash
python app.py
```

**Runs on:** `http://0.0.0.0:5000`

### Production

```bash
# Using gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Using uvicorn (if using ASGI)
pip install uvicorn
uvicorn app:app --host 0.0.0.0 --port 5000
```

### Environment Variables

```bash
# .env file
DB_HOST=localhost
DB_PORT=4000
DB_NAME=dropout_prediction_db
DB_USER=dropout_user
DB_PASSWORD=dropout_pass_123
FLASK_ENV=production
```

---

## 🔧 HELPER FUNCTIONS

### Risk Level Classification

```python
def classify_risk_level(risk_score: float) -> str:
    if risk_score >= 70:
        return 'HIGH'
    elif risk_score >= 40:
        return 'MEDIUM'
    else:
        return 'LOW'
```

### Generate Suggestions

```python
def generate_suggestions(student_data: Dict) -> List[Dict]:
    """Tạo gợi ý can thiệp dựa trên student data"""
    suggestions = []
    
    # Check inactivity
    if days_inactive > 14:
        suggestions.append({
            "icon": "📞",
            "title": "Liên hệ khẩn cấp",
            "description": f"Sinh viên không hoạt động {days_inactive} ngày...",
            "priority": "high"
        })
    
    # Check grade, completion, discussion, etc.
    # ...
    
    return suggestions
```

---

## 📊 PERFORMANCE

### Query Optimization

- Use indexes on `user_id`, `course_id`
- Limit results with pagination (future)
- Cache frequently accessed data (future)

### Connection Pooling

```python
# Future: Use connection pooling
from mysql.connector import pooling

config = {
    'pool_name': 'mypool',
    'pool_size': 5,
    **DB_CONFIG
}

pool = pooling.MySQLConnectionPool(**config)
```

---

## 🧪 TESTING

### Manual Testing

```bash
# Health check
curl http://localhost:5000/api/health

# Get courses
curl http://localhost:5000/api/courses

# Get students
curl "http://localhost:5000/api/students/course-v1:...?risk_level=HIGH"

# Get student detail
curl http://localhost:5000/api/student/123/course-v1:...

# Get statistics
curl http://localhost:5000/api/statistics/course-v1:...
```

### Unit Testing (Future)

```python
# tests/test_api.py
import unittest
from app import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
    
    def test_health_check(self):
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
```

---

## 🐛 TROUBLESHOOTING

### Lỗi: "Database connection failed"

**Giải pháp:**
1. Kiểm tra MySQL đang chạy
2. Kiểm tra config trong `DB_CONFIG`
3. Kiểm tra user có quyền truy cập

### Lỗi: "CORS policy blocked"

**Giải pháp:**
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # ✅ Đã có
```

### Lỗi: "Module not found"

**Giải pháp:**
```bash
pip install flask flask-cors mysql-connector-python pandas
```

---

## 📚 Tài Liệu Liên Quan

- **Main File:** `backend/app.py`
- **Database Schema:** `database/schema.sql`
- **Frontend Connection:** `FRONTEND_BACKEND_CONNECTION_GUIDE.md`
- **API Documentation:** `03_API_COMPLETE.md`

