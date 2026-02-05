# API H5P Content Performance Analytics

## Tổng quan

Các API này giúp phân tích performance của H5P content trong khóa học, bao gồm:
- Xác định các bài H5P có điểm thấp và tỉ lệ hoàn thành kém
- Chi tiết performance từng bài H5P (sinh viên nào làm tốt/kém)
- Performance H5P của từng sinh viên

---

## 1. Lấy danh sách bài H5P có performance thấp

### Endpoint
```
GET /api/h5p-analytics/{course_id}/low-performance
```

### Mô tả
Lấy danh sách các bài H5P có điểm trung bình thấp và tỉ lệ hoàn thành kém nhất trong khóa học.

### Query Parameters
- `min_students` (optional, default=5): Số sinh viên tối thiểu phải làm bài để tính vào kết quả
- `limit` (optional, default=20): Số lượng bài H5P trả về (top N bài kém nhất)

### Response

```json
{
  "success": true,
  "course_id": "course-v1:VNUHCM+FM101+2024_T1",
  "statistics": {
    "total_contents_analyzed": 20,
    "avg_completion_rate": 65.5,
    "avg_score_all": 58.3,
    "high_difficulty_count": 8,
    "needs_attention_count": 12
  },
  "contents": [
    {
      "content_id": 123,
      "content_title": "Bài tập về hàm số",
      "folder_name": "Chương 3 - Hàm số",
      "total_students": 45,
      "completed_students": 28,
      "completion_rate": 62.22,
      "avg_score": 45.5,
      "avg_score_completed": 52.3,
      "min_score": 0,
      "max_score": 95,
      "avg_time_spent_minutes": 12.5,
      "difficulty_level": "HIGH",
      "needs_attention": true
    }
  ]
}
```

### Difficulty Levels
- **HIGH**: Bài rất khó (avg_score < 50 hoặc completion_rate < 50)
- **MEDIUM**: Bài khá khó (avg_score < 70 hoặc completion_rate < 70)
- **LOW**: Bài dễ (avg_score >= 70 và completion_rate >= 70)

### Use Cases
- Giáo viên xác định bài tập nào cần giải thích lại
- Xác định nội dung nào khó và cần điều chỉnh
- Ưu tiên can thiệp vào các bài có nhiều sinh viên gặp khó khăn

---

## 2. Chi tiết performance của một bài H5P

### Endpoint
```
GET /api/h5p-analytics/{course_id}/content/{content_id}
```

### Mô tả
Lấy chi tiết performance của một bài H5P cụ thể, bao gồm:
- Thông tin tổng quan
- Phân bố điểm số
- Danh sách sinh viên làm tốt/kém

### Response

```json
{
  "success": true,
  "course_id": "course-v1:VNUHCM+FM101+2024_T1",
  "content": {
    "content_id": 123,
    "content_title": "Bài tập về hàm số",
    "folder_name": "Chương 3 - Hàm số",
    "total_students": 45,
    "completed_students": 28,
    "completion_rate": 62.22,
    "avg_score": 45.5,
    "min_score": 0,
    "max_score": 95
  },
  "score_distribution": {
    "excellent": 3,
    "good": 5,
    "average": 8,
    "below_average": 7,
    "poor": 5,
    "not_attempted": 17
  },
  "student_performance": {
    "high_performers": [
      {
        "user_id": 101,
        "full_name": "Nguyễn Văn A",
        "email": "a.nguyen@example.com",
        "mssv": "20120001",
        "score": 95,
        "max_score": 100,
        "percentage": 95.0,
        "is_completed": true,
        "time_spent_minutes": 15.5,
        "opened_time": "2024-01-15T10:30:00",
        "finished_time": "2024-01-15T10:45:30"
      }
    ],
    "medium_performers": [],
    "low_performers": [
      {
        "user_id": 102,
        "full_name": "Trần Thị B",
        "email": "b.tran@example.com",
        "mssv": "20120002",
        "score": 30,
        "max_score": 100,
        "percentage": 30.0,
        "is_completed": true,
        "time_spent_minutes": 8.2,
        "opened_time": "2024-01-15T11:00:00",
        "finished_time": "2024-01-15T11:08:12"
      }
    ],
    "not_attempted": []
  }
}
```

### Performance Categories
- **High Performers**: Điểm >= 80%
- **Medium Performers**: 50% <= Điểm < 80%
- **Low Performers**: Điểm < 50%
- **Not Attempted**: Chưa làm bài (finished = 0)

### Score Distribution
- **Excellent**: 90-100%
- **Good**: 80-89%
- **Average**: 70-79%
- **Below Average**: 50-69%
- **Poor**: 1-49%
- **Not Attempted**: 0%

### Use Cases
- Xác định sinh viên cần hỗ trợ thêm cho bài này
- Liên hệ sinh viên chưa làm bài
- Phân tích tại sao bài này khó (thời gian làm, điểm số)

---

## 3. Performance H5P của một sinh viên

### Endpoint
```
GET /api/h5p-analytics/{course_id}/student/{user_id}
```

### Mô tả
Lấy chi tiết performance H5P của một sinh viên cụ thể, bao gồm:
- Bài nào làm tốt, bài nào làm kém
- Bài nào chưa hoàn thành
- Thống kê tổng quan

### Response

```json
{
  "success": true,
  "course_id": "course-v1:VNUHCM+FM101+2024_T1",
  "student": {
    "user_id": 101,
    "full_name": "Nguyễn Văn A",
    "email": "a.nguyen@example.com",
    "mssv": "20120001"
  },
  "statistics": {
    "total_attempted": 15,
    "total_in_progress": 2,
    "avg_score": 72.5,
    "excellent_count": 5,
    "good_count": 4,
    "needs_improvement_count": 4,
    "poor_count": 2
  },
  "performance": {
    "excellent": [
      {
        "content_id": 123,
        "content_title": "Bài tập về đạo hàm",
        "folder_name": "Chương 2 - Đạo hàm",
        "score": 95,
        "max_score": 100,
        "percentage": 95.0,
        "time_spent_minutes": 15.5,
        "opened_time": "2024-01-15T10:30:00",
        "finished_time": "2024-01-15T10:45:30"
      }
    ],
    "good": [],
    "needs_improvement": [
      {
        "content_id": 124,
        "content_title": "Bài tập về tích phân",
        "folder_name": "Chương 4 - Tích phân",
        "score": 55,
        "max_score": 100,
        "percentage": 55.0,
        "time_spent_minutes": 10.2,
        "opened_time": "2024-01-16T14:00:00",
        "finished_time": "2024-01-16T14:10:12"
      }
    ],
    "poor": [],
    "in_progress": [
      {
        "content_id": 125,
        "content_title": "Bài tập về ma trận",
        "folder_name": "Chương 5 - Ma trận",
        "score": 0,
        "max_score": 100,
        "percentage": 0.0,
        "time_spent_minutes": 5.0,
        "opened_time": "2024-01-17T09:00:00",
        "finished_time": null
      }
    ]
  }
}
```

### Use Cases
- Xem overview performance H5P của sinh viên
- Xác định bài nào sinh viên cần làm lại hoặc ôn tập
- Theo dõi tiến độ làm bài H5P

---

## Ví dụ sử dụng

### JavaScript/Fetch

```javascript
// Lấy danh sách bài H5P có performance thấp
const courseId = 'course-v1:VNUHCM+FM101+2024_T1';
fetch(`http://localhost:5000/api/h5p-analytics/${encodeURIComponent(courseId)}/low-performance?limit=10&min_students=3`)
  .then(res => res.json())
  .then(data => {
    console.log('Bài H5P khó:', data.contents);
    console.log('Statistics:', data.statistics);
  });

// Chi tiết một bài H5P
const contentId = 123;
fetch(`http://localhost:5000/api/h5p-analytics/${encodeURIComponent(courseId)}/content/${contentId}`)
  .then(res => res.json())
  .then(data => {
    console.log('Low performers:', data.student_performance.low_performers);
    console.log('Not attempted:', data.student_performance.not_attempted);
  });

// Performance H5P của sinh viên
const userId = 101;
fetch(`http://localhost:5000/api/h5p-analytics/${encodeURIComponent(courseId)}/student/${userId}`)
  .then(res => res.json())
  .then(data => {
    console.log('Avg score:', data.statistics.avg_score);
    console.log('Poor performance:', data.performance.poor);
  });
```

### Python/Requests

```python
import requests
from urllib.parse import quote

course_id = 'course-v1:VNUHCM+FM101+2024_T1'
encoded_course_id = quote(course_id, safe='')

# Lấy bài H5P khó
response = requests.get(
    f'http://localhost:5000/api/h5p-analytics/{encoded_course_id}/low-performance',
    params={'limit': 10, 'min_students': 3}
)
data = response.json()
print(f"Tổng số bài cần chú ý: {data['statistics']['needs_attention_count']}")

# Chi tiết bài H5P
content_id = 123
response = requests.get(
    f'http://localhost:5000/api/h5p-analytics/{encoded_course_id}/content/{content_id}'
)
data = response.json()
print(f"Low performers: {len(data['student_performance']['low_performers'])}")
```

---

## Recommendations

### Cho Giáo viên
1. **Kiểm tra định kỳ**: Gọi API `/low-performance` mỗi tuần để xem bài nào khó
2. **Can thiệp sớm**: Với bài có `needs_attention: true`, nên giải thích lại nội dung
3. **Liên hệ sinh viên**: Dùng API `/content/{content_id}` để lấy danh sách sinh viên cần hỗ trợ

### Cho Dashboard
1. Hiển thị **Top 5-10 bài khó nhất** với visual (biểu đồ, màu đỏ/vàng)
2. Hiển thị **phân bố điểm** cho mỗi bài (histogram)
3. Tạo alert khi có bài có > 50% sinh viên không làm hoặc điểm < 50

### Thresholds đề xuất
- **High Priority**: avg_score < 50 hoặc completion_rate < 50
- **Medium Priority**: avg_score < 70 hoặc completion_rate < 70
- **Needs Review**: min_students đủ nhưng < 60% sinh viên hoàn thành

---

## Error Handling

Tất cả endpoint đều trả về error với format:

```json
{
  "error": "Error message description"
}
```

HTTP Status Codes:
- `200 OK`: Thành công
- `404 Not Found`: Course/Content/Student không tồn tại
- `500 Internal Server Error`: Lỗi server

---

## Database Schema Reference

Các API này dựa trên bảng `h5p_scores`:

```sql
CREATE TABLE h5p_scores (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    content_id INT NOT NULL,
    content_title VARCHAR(500),
    score INT DEFAULT 0,
    max_score INT DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    opened BIGINT DEFAULT 0,
    finished BIGINT DEFAULT 0,
    time_spent BIGINT DEFAULT 0,
    folder_id INT,
    folder_name VARCHAR(255),
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Notes

- Tất cả `course_id` cần URL encode khi gọi API
- Thời gian được lưu dưới dạng UNIX timestamp (seconds) trong database
- `percentage` là phần trăm điểm (0-100)
- `finished = 0` nghĩa là bài chưa hoàn thành
- `opened` là timestamp lần đầu mở bài
