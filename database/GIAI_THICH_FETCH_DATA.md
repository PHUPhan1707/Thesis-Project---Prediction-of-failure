# 📚 Giải Thích Chi Tiết File `fetch_mooc_h5p_data.py`

## 🎯 Mục Đích File

File này **thu thập dữ liệu** từ 2 nguồn:
1. **MOOC API** (Open edX) - Điểm số, tiến độ, thảo luận
2. **H5P API** - Điểm H5P, tiến độ xem video

Sau đó **lưu vào database** và **tổng hợp** thành bảng `raw_data` để dùng cho ML model.

---

## 📋 Cấu Trúc Class: `MOOCH5PDataFetcher`

### 1. **`__init__(self)`** - Khởi tạo
```python
def __init__(self):
    self.mooc_base_url = "https://mooc.vnuhcm.edu.vn/api/custom/v1"
    self.h5p_base_url = "https://h5p.itp.vn/wp-json/mooc/v1"
    self.session = requests.Session()  # Tạo session để giữ cookies
    self.db_connection = None  # Kết nối database (chưa mở)
```

**Tác dụng:**
- Khởi tạo URLs của 2 API
- Tạo HTTP session để giữ cookies (cần cho authentication)
- Chuẩn bị biến database connection

---

### 2. **`connect_db(self)`** - Kết nối Database
```python
def connect_db(self):
    self.db_connection = mysql.connector.connect(**DB_CONFIG)
```

**Tác dụng:**
- Kết nối MySQL với thông tin trong `DB_CONFIG`
- Trả về `True` nếu thành công, `False` nếu lỗi

**Khi nào dùng:** Mỗi khi cần truy vấn database

---

### 3. **`close_db(self)`** - Đóng Database
```python
def close_db(self):
    if self.db_connection and self.db_connection.is_connected():
        self.db_connection.close()
```

**Tác dụng:** Đóng kết nối database khi xong việc

---

### 4. **`set_mooc_session(self, sessionid: str)`** - Thiết lập Cookie
```python
def set_mooc_session(self, sessionid: str):
    self.session.cookies.set("sessionid", sessionid)
    self.session.cookies.set("edx-session", sessionid)
```

**Tác dụng:**
- Set cookie `sessionid` để authenticate với MOOC API
- Cookie này lấy từ trình duyệt khi bạn đăng nhập vào MOOC

**Ví dụ:** Bạn đăng nhập MOOC → F12 → Application → Cookies → copy `sessionid` → truyền vào script

---

### 5. **`url_encode_course_id(self, course_id: str)`** - Encode Course ID
```python
def url_encode_course_id(self, course_id: str) -> str:
    return quote(course_id, safe='')
```

**Tác dụng:**
- Encode course_id để dùng trong URL (ví dụ: `:` → `%3A`, `+` → `%2B`)
- **MOOC API** cần encode, **H5P API** không cần

**Ví dụ:**
- Input: `course-v1:DHQG-HCM+FM101+2025_S2`
- Output: `course-v1%3ADHQG-HCM%2BFM101%2B2025_S2`

---

### 6. **`parse_datetime(self, date_str)`** - Parse Ngày Tháng
```python
def parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
    # Thử nhiều format: ISO, với Z, không có timezone...
```

**Tác dụng:**
- Chuyển string ngày tháng thành object `datetime`
- Hỗ trợ nhiều format khác nhau từ API

**Ví dụ:**
- `"2024-01-15T10:30:00Z"` → `datetime(2024, 1, 15, 10, 30, 0)`
- `"2024-01-15T10:30:00"` → `datetime(2024, 1, 15, 10, 30, 0)`

---

## 📥 PHẦN 1: ENROLLMENTS (Đăng Ký Học Viên)

### 7. **`save_enrollments(self, enrollments, course_id)`** - Lưu Danh Sách Đăng Ký
```python
def save_enrollments(self, enrollments: List[Dict], course_id: str) -> bool:
    # INSERT INTO enrollments (...) VALUES (...)
    # ON DUPLICATE KEY UPDATE ... (nếu đã có thì update)
```

**Tác dụng:**
- Lưu thông tin đăng ký học viên vào bảng `enrollments`
- Mỗi enrollment chứa: `user_id`, `username`, `email`, `full_name`, `mode`, `is_active`, `created`, `mssv`, `class_code`, v.v.

**Luồng:**
1. Nhận danh sách enrollments từ API
2. Loop qua từng enrollment
3. INSERT hoặc UPDATE vào database
4. Commit transaction

**Bảng lưu:** `enrollments`

---

### 8. **`fetch_mooc_course_students(self, course_id)`** - Lấy Danh Sách Học Viên
```python
def fetch_mooc_course_students(self, course_id: str) -> Optional[List[int]]:
    # Gọi API: /course-enrollments-attributes/{course_id}/?limit=200&offset=0
    # Pagination: lặp cho đến khi hết data
    # Lưu vào enrollments table
    # Trả về list user_ids
```

**Tác dụng:**
- Gọi MOOC API để lấy **tất cả học viên** đã đăng ký khóa học
- **Pagination:** Lấy từng batch 200 học viên (limit=200, offset tăng dần)
- Lưu vào bảng `enrollments`
- Trả về danh sách `user_id` để fetch data chi tiết sau

**Luồng:**
```
1. Encode course_id
2. Gọi API với limit=200, offset=0
3. Parse response → lấy enrollments
4. Lưu vào database (save_enrollments)
5. Nếu còn data → tăng offset → lặp lại
6. Trả về list user_ids
```

**API Endpoint:** `GET /api/custom/v1/course-enrollments-attributes/{course_id}/`

---

## 📊 PHẦN 2: H5P SCORES (Điểm H5P)

### 9. **`save_h5p_scores(self, user_id, course_id, scores_data)`** - Lưu Điểm H5P
```python
def save_h5p_scores(self, user_id: int, course_id: str, scores_data: Dict) -> bool:
    # Lưu chi tiết từng content vào h5p_scores
    # Lưu summary vào h5p_scores_summary
```

**Tác dụng:**
- Lưu **chi tiết** từng H5P content (bài tập) vào `h5p_scores`
- Lưu **tổng hợp** (summary) vào `h5p_scores_summary`

**Dữ liệu lưu:**
- **Chi tiết:** `content_id`, `score`, `max_score`, `percentage`, `opened`, `finished`, `time_spent`
- **Summary:** `total_contents`, `completed_contents`, `total_score`, `total_max_score`, `overall_percentage`

**Bảng lưu:** `h5p_scores`, `h5p_scores_summary`

---

### 10. **`fetch_h5p_scores(self, user_id, course_id)`** - Lấy Điểm H5P
```python
def fetch_h5p_scores(self, user_id: int, course_id: str) -> Optional[Dict]:
    url = f"{self.h5p_base_url}/scores/{user_id}/{course_id}"
    # Gọi API → trả về JSON
```

**Tác dụng:**
- Gọi H5P API để lấy điểm số của một học viên
- **KHÔNG encode** course_id (H5P API chấp nhận ký tự đặc biệt)

**API Endpoint:** `GET https://h5p.itp.vn/wp-json/mooc/v1/scores/{user_id}/{course_id}`

**Response:**
```json
{
  "user_id": "123",
  "course_id": "course-v1:...",
  "summary": {
    "total_contents": 30,
    "completed_contents": 25,
    "total_score": 850,
    "total_max_score": 1000,
    "overall_percentage": 85.0
  },
  "scores": [
    {
      "content_id": 45,
      "score": 90,
      "max_score": 100,
      "percentage": 90.0,
      "opened": 1,
      "finished": 1,
      "time": 300
    }
  ]
}
```

---

## 🎥 PHẦN 3: VIDEO PROGRESS (Tiến Độ Xem Video)

### 11. **`save_video_progress(self, user_id, course_id, video_data)`** - Lưu Tiến Độ Video
```python
def save_video_progress(self, user_id: int, course_id: str, video_data: Dict) -> bool:
    # Lưu chi tiết từng video vào video_progress
    # Lưu summary vào video_progress_summary
```

**Tác dụng:**
- Lưu **chi tiết** từng video vào `video_progress`
- Lưu **tổng hợp** vào `video_progress_summary`

**Dữ liệu lưu:**
- **Chi tiết:** `content_id`, `progress_percent`, `current_time`, `duration`, `status`
- **Summary:** `total_videos`, `completed_videos`, `in_progress_videos`, `total_watched_time`, `overall_progress`

**Bảng lưu:** `video_progress`, `video_progress_summary`

---

### 12. **`fetch_video_progress(self, user_id, course_id)`** - Lấy Tiến Độ Video
```python
def fetch_video_progress(self, user_id: int, course_id: str) -> Optional[Dict]:
    url = f"{self.h5p_base_url}/video-progress/{user_id}/{course_id}"
```

**Tác dụng:**
- Gọi H5P API để lấy tiến độ xem video của một học viên

**API Endpoint:** `GET https://h5p.itp.vn/wp-json/mooc/v1/video-progress/{user_id}/{course_id}`

---

## 🔄 PHẦN 4: COMBINED PROGRESS (Tổng Hợp)

### 13. **`fetch_combined_progress(self, user_id, course_id)`** - Lấy Tổng Hợp
```python
def fetch_combined_progress(self, user_id: int, course_id: str) -> Optional[Dict]:
    url = f"{self.h5p_base_url}/combined-progress/{user_id}/{course_id}"
```

**Tác dụng:**
- Gọi API tổng hợp cả video + scores trong 1 lần
- **Thay thế** dashboard API (dashboard API không hoạt động)

**API Endpoint:** `GET https://h5p.itp.vn/wp-json/mooc/v1/combined-progress/{user_id}/{course_id}`

**Response:**
```json
{
  "overall": {
    "total_items": 50,
    "completed_items": 40,
    "overall_completion": 80.0
  },
  "video_progress": {...},
  "scores": {...}
}
```

---

### 14. **`save_combined_progress(self, user_id, course_id, combined_data)`** - Lưu Tổng Hợp
```python
def save_combined_progress(self, user_id: int, course_id: str, combined_data: Dict) -> bool:
    # Lưu vào dashboard_summary table
```

**Tác dụng:**
- Lưu dữ liệu tổng hợp vào bảng `dashboard_summary`
- Chứa: `overall_completion`, `total_items`, `completed_items`, H5P stats, Video stats

**Bảng lưu:** `dashboard_summary`

---

## 📈 PHẦN 5: MOOC EXPORT APIs (Điểm, Tiến Độ, Thảo Luận)

### 15. **`save_mooc_grades(self, course_id, grades_data)`** - Lưu Điểm MOOC
```python
def save_mooc_grades(self, course_id: str, grades_data: Dict) -> bool:
    # Lưu vào mooc_grades table
```

**Tác dụng:**
- Lưu điểm số từ MOOC Export API vào bảng `mooc_grades`
- Mỗi record: `user_id`, `grade_percentage`, `letter_grade`, `is_passed`

**Bảng lưu:** `mooc_grades`

---

### 16. **`fetch_mooc_grades(self, course_id)`** - Lấy Điểm MOOC
```python
def fetch_mooc_grades(self, course_id: str) -> Optional[Dict]:
    url = f"{self.mooc_base_url}/export/student-grades/{encoded_course_id}/"
```

**Tác dụng:**
- Gọi MOOC Export API để lấy **bảng điểm** của tất cả học viên trong course

**API Endpoint:** `GET /api/custom/v1/export/student-grades/{course_id}/`

**Response:**
```json
{
  "grade_data": {
    "grade_table": [
      {
        "user_id": 123,
        "grade_percentage": 85.5,
        "letter_grade": "B",
        "is_passed": true
      }
    ]
  }
}
```

---

### 17. **`save_mooc_progress(self, course_id, progress_data)`** - Lưu Tiến Độ MOOC
```python
def save_mooc_progress(self, course_id: str, progress_data: Dict) -> bool:
    # Lưu vào mooc_progress table
```

**Tác dụng:**
- Lưu tiến độ học tập từ MOOC Export API vào `mooc_progress`
- Mỗi record: `user_id`, `current_chapter`, `current_section`, `current_unit`, `completion_rate`, `last_activity`

**Bảng lưu:** `mooc_progress`

---

### 18. **`fetch_mooc_progress(self, course_id)`** - Lấy Tiến Độ MOOC
```python
def fetch_mooc_progress(self, course_id: str) -> Optional[Dict]:
    url = f"{self.mooc_base_url}/export/student-progress/{encoded_course_id}/"
```

**Tác dụng:**
- Gọi MOOC Export API để lấy **tiến độ** của tất cả học viên

**API Endpoint:** `GET /api/custom/v1/export/student-progress/{course_id}/`

---

### 19. **`save_mooc_discussions(self, course_id, discussions_data)`** - Lưu Thảo Luận
```python
def save_mooc_discussions(self, course_id: str, discussions_data: Dict) -> bool:
    # Lưu vào mooc_discussions table
```

**Tác dụng:**
- Lưu tương tác thảo luận vào `mooc_discussions`
- Mỗi record: `user_id`, `threads_count`, `comments_count`, `total_interactions`, `questions_count`, `total_upvotes`

**Bảng lưu:** `mooc_discussions`

---

### 20. **`fetch_mooc_discussions(self, course_id)`** - Lấy Thảo Luận
```python
def fetch_mooc_discussions(self, course_id: str) -> Optional[Dict]:
    url = f"{self.mooc_base_url}/export/student-discussions/{encoded_course_id}/"
```

**Tác dụng:**
- Gọi MOOC Export API để lấy **tương tác thảo luận** của tất cả học viên

**API Endpoint:** `GET /api/custom/v1/export/student-discussions/{course_id}/`

---

### 21. **`fetch_all_mooc_export_data(self, course_id)`** - Lấy Tất Cả MOOC Data
```python
def fetch_all_mooc_export_data(self, course_id: str) -> Dict:
    # 1. Fetch grades → save
    # 2. Fetch progress → save
    # 3. Fetch discussions → save
    # 4. Fetch course benchmarks (Advanced Stats)
```

**Tác dụng:**
- **Tổng hợp** tất cả MOOC Export APIs:
  1. Grades (điểm số)
  2. Progress (tiến độ)
  3. Discussions (thảo luận)
  4. Course benchmarks (thống kê khóa học)

**Luồng:**
```
1. Gọi fetch_mooc_grades() → save_mooc_grades()
2. Sleep 0.5s (rate limiting)
3. Gọi fetch_mooc_progress() → save_mooc_progress()
4. Sleep 0.5s
5. Gọi fetch_mooc_discussions() → save_mooc_discussions()
6. Sleep 0.5s
7. Gọi fetch_and_store_course_benchmarks() (Advanced Stats)
```

**Trả về:** Dict với `{"grades": True/False, "progress": ..., "discussions": ...}`

---

## 📊 PHẦN 6: ADVANCED STATS (Thống Kê Nâng Cao)

### 22. **`fetch_activity_stats_summary(self, course_id)`** - Lấy Thống Kê Hoạt Động
```python
def fetch_activity_stats_summary(self, course_id: str) -> Optional[Dict]:
    url = f"{self.mooc_base_url}/stats/activity/{encoded_course_id}/"
    params = {'days': 90, 'group_by': 'day'}
```

**Tác dụng:**
- Gọi Advanced Stats API để lấy thống kê hoạt động của course
- Dùng để tính **course benchmarks** (trung bình của lớp)

**API Endpoint:** `GET /api/custom/v1/stats/activity/{course_id}/?days=90`

---

### 23. **`fetch_assessment_stats_summary(self, course_id)`** - Lấy Thống Kê Đánh Giá
```python
def fetch_assessment_stats_summary(self, course_id: str) -> Optional[Dict]:
    url = f"{self.mooc_base_url}/stats/assessment/{encoded_course_id}/"
```

**Tác dụng:**
- Lấy thống kê điểm số trung bình của course

**API Endpoint:** `GET /api/custom/v1/stats/assessment/{course_id}/`

---

### 24. **`fetch_progress_stats_summary(self, course_id)`** - Lấy Thống Kê Tiến Độ
```python
def fetch_progress_stats_summary(self, course_id: str) -> Optional[Dict]:
    url = f"{self.mooc_base_url}/stats/progress/{encoded_course_id}/"
```

**Tác dụng:**
- Lấy thống kê tiến độ trung bình của course

**API Endpoint:** `GET /api/custom/v1/stats/progress/{course_id}/`

---

### 25. **`fetch_and_store_course_benchmarks(self, course_id)`** - Lưu Benchmarks
```python
def fetch_and_store_course_benchmarks(self, course_id: str) -> bool:
    # 1. Fetch Activity, Assessment, Progress stats
    # 2. Parse → extract averages
    # 3. Lưu vào course_stats_benchmarks table
```

**Tác dụng:**
- Fetch tất cả Advanced Stats APIs
- Trích xuất các **chỉ số trung bình** của course:
  - `activity_avg_score` - Điểm hoạt động trung bình
  - `assessment_avg_score` - Điểm đánh giá trung bình
  - `progress_avg_completion` - Tiến độ trung bình
  - `total_students` - Tổng số học viên
  - v.v.
- Lưu vào `course_stats_benchmarks` để so sánh với từng học viên

**Bảng lưu:** `course_stats_benchmarks`

**Ví dụ:**
- Course có 150 học viên
- Điểm trung bình: 75.5%
- Tiến độ trung bình: 65.3%
- → Lưu vào benchmarks để so sánh: học viên A có điểm 80% → cao hơn trung bình 4.5%

---

### 26. **`get_course_benchmarks(self, course_id)`** - Lấy Benchmarks Từ DB
```python
def get_course_benchmarks(self, course_id: str) -> Optional[Dict]:
    # SELECT * FROM course_stats_benchmarks WHERE course_id = %s
```

**Tác dụng:**
- Lấy benchmarks đã lưu từ database
- Dùng để tính **comparative features** (so sánh học viên với trung bình lớp)

---

### 27. **`calculate_comparative_features(self, user_metrics, course_benchmarks)`** - Tính So Sánh
```python
def calculate_comparative_features(self, user_metrics: Dict, course_benchmarks: Dict) -> Dict:
    # So sánh user với course average
    # Tính: relative_to_course_problem_score, relative_to_course_completion, ...
    # Tính: performance_percentile, is_below_course_average, ...
```

**Tác dụng:**
- Tính các **features so sánh** (Option 2):
  - `relative_to_course_problem_score` = điểm học viên - điểm trung bình lớp
  - `relative_to_course_completion` = tiến độ học viên - tiến độ trung bình lớp
  - `performance_percentile` = xếp hạng học viên (10, 25, 50, 75, 90)
  - `is_below_course_average` = 1 nếu dưới trung bình, 0 nếu trên
  - `is_top_performer` = 1 nếu top 25%
  - `is_bottom_performer` = 1 nếu bottom 25%

**Ví dụ:**
- Course avg: 75%
- Học viên A: 80% → `relative_to_course_problem_score = 5.0`, `is_below_course_average = 0`
- Học viên B: 60% → `relative_to_course_problem_score = -15.0`, `is_below_course_average = 1`

---

## 🔄 PHẦN 7: AGGREGATE RAW DATA (Tổng Hợp Dữ Liệu)

### 28. **`aggregate_raw_data(self, user_id, course_id, batch_id)`** - Tổng Hợp 1 User
```python
def aggregate_raw_data(self, user_id: int, course_id: str, batch_id: Optional[str] = None) -> bool:
    # 1. Lấy data từ các bảng: enrollments, h5p_scores_summary, video_progress_summary, 
    #    mooc_grades, mooc_progress, mooc_discussions
    # 2. Tính toán các features
    # 3. Tính comparative features (nếu có benchmarks)
    # 4. INSERT/UPDATE vào raw_data table
```

**Tác dụng:**
- **Tổng hợp** tất cả dữ liệu từ các bảng riêng lẻ thành **1 record** trong `raw_data`
- Tính toán các **features** cho ML model:
  - `weeks_since_enrollment` - Số tuần từ khi đăng ký
  - `days_since_last_activity` - Số ngày không hoạt động
  - `h5p_completion_rate` - Tỉ lệ hoàn thành H5P
  - `video_completion_rate` - Tỉ lệ hoàn thành video
  - `quiz_avg_score` - Điểm quiz trung bình
  - `discussion_total_interactions` - Tổng tương tác thảo luận
  - `relative_to_course_*` - So sánh với trung bình lớp
  - v.v.

**Luồng:**
```
1. Query enrollments → lấy mode, is_active, created
2. Query h5p_scores_summary → lấy H5P stats
3. Query video_progress_summary → lấy video stats
4. Query mooc_grades → lấy điểm số
5. Query mooc_progress → lấy tiến độ
6. Query mooc_discussions → lấy thảo luận
7. Tính toán features:
   - weeks_since_enrollment = (now - created) / 7
   - days_since_last_activity = (now - last_activity)
   - h5p_completion_rate = completed / total * 100
   - video_completion_rate = completed / total * 100
   - quiz_avg_score = h5p_overall_percentage
   - ...
8. Lấy course_benchmarks → tính comparative features
9. INSERT/UPDATE vào raw_data
```

**Bảng lưu:** `raw_data` (bảng chính cho ML model)

**Labels tự động:**
- `is_passed` - Lấy từ `mooc_grades.is_passed` (True/False/NULL)
- `is_dropout` - Tự động label:
  - `True` nếu `is_active = False` VÀ `days_since_last_activity > 30`
  - `False` nếu `is_active = True` HOẶC `days_since_last_activity < 7`
  - `NULL` nếu 7-30 ngày (không chắc chắn)

---

### 29. **`aggregate_all_raw_data(self, course_id, batch_id)`** - Tổng Hợp Tất Cả Users
```python
def aggregate_all_raw_data(self, course_id: str, batch_id: Optional[str] = None) -> Dict:
    # 1. Lấy danh sách user_ids từ enrollments
    # 2. Loop qua từng user → gọi aggregate_raw_data()
    # 3. Trả về kết quả
```

**Tác dụng:**
- Tổng hợp raw_data cho **tất cả học viên** trong course
- Dùng khi đã fetch xong tất cả data, chỉ cần aggregate

**Luồng:**
```
1. SELECT DISTINCT user_id FROM enrollments WHERE course_id = ?
2. Loop qua từng user_id:
   - aggregate_raw_data(user_id, course_id, batch_id)
3. Trả về: {success: True, total_users: 150, success_count: 148, failed_count: 2}
```

---

## 🎯 PHẦN 8: FETCH ALL DATA (Thu Thập Tất Cả)

### 30. **`fetch_user_data(self, user_id, course_id, delay)`** - Fetch Data 1 User
```python
def fetch_user_data(self, user_id: int, course_id: str, delay: float = 0.5) -> bool:
    # 1. Fetch H5P scores → save
    # 2. Fetch video progress → save
    # 3. Fetch combined progress → save (hoặc dashboard nếu fail)
```

**Tác dụng:**
- Fetch **tất cả H5P data** cho 1 học viên:
  1. H5P scores (điểm số)
  2. Video progress (tiến độ video)
  3. Combined progress (tổng hợp)

**Luồng:**
```
1. fetch_h5p_scores() → save_h5p_scores()
2. Sleep delay (0.5s) - rate limiting
3. fetch_video_progress() → save_video_progress()
4. Sleep delay
5. fetch_combined_progress() → save_combined_progress()
   - Nếu fail → thử fetch_dashboard() → save_dashboard_summary()
6. Sleep delay
7. Return True/False
```

**Lưu ý:** Có `delay` giữa các API calls để tránh rate limiting

---

### 31. **`fetch_all_course_data(self, course_id, delay, max_users, aggregate)`** - Fetch Tất Cả
```python
def fetch_all_course_data(self, course_id: str, delay: float = 0.5, 
                         max_users: Optional[int] = None, aggregate: bool = True) -> Dict:
    # Bước 1: Fetch enrollments
    # Bước 2: Fetch MOOC Export data (grades, progress, discussions)
    # Bước 3: Fetch H5P data cho từng user
    # Bước 4: Aggregate vào raw_data
```

**Tác dụng:**
- **Hàm chính** để fetch tất cả data cho một course
- Thực hiện **4 bước** tuần tự

**Luồng chi tiết:**

#### **Bước 1: Fetch Enrollments**
```python
user_ids = self.fetch_mooc_course_students(course_id)
# → Lấy danh sách tất cả học viên, lưu vào enrollments table
# → Trả về list user_ids
```

#### **Bước 2: Fetch MOOC Export Data (Course-level)**
```python
mooc_export_results = self.fetch_all_mooc_export_data(course_id)
# → Gọi 3 APIs:
#   1. fetch_mooc_grades() → lưu vào mooc_grades
#   2. fetch_mooc_progress() → lưu vào mooc_progress
#   3. fetch_mooc_discussions() → lưu vào mooc_discussions
# → Fetch course benchmarks (Advanced Stats)
```

#### **Bước 3: Fetch H5P Data (User-level)**
```python
for user_id in user_ids:
    self.fetch_user_data(user_id, course_id, delay)
    # → Fetch H5P scores, video progress, combined progress
    # → Lưu vào các bảng tương ứng
```

#### **Bước 4: Aggregate Raw Data**
```python
if aggregate:
    self.aggregate_all_raw_data(course_id, batch_id)
    # → Tổng hợp tất cả data vào raw_data table
```

**Trả về:**
```python
{
    "success": True,
    "total_users": 150,
    "success_count": 148,
    "failed_count": 2,
    "mooc_export_results": {"grades": True, "progress": True, "discussions": True},
    "aggregated": True
}
```

---

## 🚀 PHẦN 9: MAIN FUNCTION

### 32. **`main()`** - Hàm Chính
```python
def main():
    # Parse command line arguments
    # Tạo MOOCH5PDataFetcher instance
    # Set sessionid (nếu có)
    # Connect database
    # Gọi fetch_all_course_data() hoặc aggregate_all_raw_data()
```

**Tác dụng:**
- **Entry point** của script
- Xử lý command line arguments
- Điều phối toàn bộ quá trình fetch data

**Command Line Arguments:**
```bash
python fetch_mooc_h5p_data.py \
    --course-id "course-v1:DHQG-HCM+FM101+2025_S2" \
    --sessionid "abc123..." \
    --delay 0.5 \
    --max-users 10 \
    --no-aggregate \
    --aggregate-only
```

**Các options:**
- `--course-id` (required): Course ID cần fetch
- `--sessionid` (optional): Cookie session để authenticate
- `--delay` (default: 0.5): Delay giữa các API calls (giây)
- `--max-users` (optional): Giới hạn số users để test
- `--no-aggregate`: Chỉ fetch, không aggregate vào raw_data
- `--aggregate-only`: Chỉ aggregate data đã có, không fetch mới

**Luồng:**
```
1. Parse arguments
2. Tạo MOOCH5PDataFetcher()
3. Nhập sessionid (nếu chưa có)
4. Set sessionid → set_mooc_session()
5. Connect database → connect_db()
6. Nếu --aggregate-only:
   → aggregate_all_raw_data()
7. Nếu không:
   → fetch_all_course_data()
8. Close database → close_db()
```

---

## 📊 TÓM TẮT LUỒNG HOẠT ĐỘNG

### Khi chạy script:
```bash
python fetch_mooc_h5p_data.py --course-id "course-v1:..." --sessionid "..."
```

### Luồng thực thi:

```
1. KHỞI TẠO
   ├─ Tạo MOOCH5PDataFetcher()
   ├─ Set sessionid cookie
   └─ Connect database

2. FETCH ENROLLMENTS (Bước 1)
   ├─ fetch_mooc_course_students()
   │  ├─ Gọi API: /course-enrollments-attributes/{course_id}/
   │  ├─ Pagination: lấy từng batch 200 users
   │  └─ save_enrollments() → lưu vào enrollments table
   └─ Trả về: list user_ids [1, 2, 3, ..., 150]

3. FETCH MOOC EXPORT DATA (Bước 2)
   ├─ fetch_all_mooc_export_data()
   │  ├─ fetch_mooc_grades() → save_mooc_grades()
   │  ├─ fetch_mooc_progress() → save_mooc_progress()
   │  ├─ fetch_mooc_discussions() → save_mooc_discussions()
   │  └─ fetch_and_store_course_benchmarks()
   │     ├─ fetch_activity_stats_summary()
   │     ├─ fetch_assessment_stats_summary()
   │     ├─ fetch_progress_stats_summary()
   │     └─ Lưu vào course_stats_benchmarks
   └─ Kết quả: Đã có grades, progress, discussions cho TẤT CẢ users

4. FETCH H5P DATA (Bước 3) - Cho từng user
   └─ Loop qua từng user_id:
      ├─ fetch_user_data(user_id, course_id)
      │  ├─ fetch_h5p_scores() → save_h5p_scores()
      │  │  ├─ Lưu chi tiết vào h5p_scores
      │  │  └─ Lưu summary vào h5p_scores_summary
      │  ├─ fetch_video_progress() → save_video_progress()
      │  │  ├─ Lưu chi tiết vào video_progress
      │  │  └─ Lưu summary vào video_progress_summary
      │  └─ fetch_combined_progress() → save_combined_progress()
      │     └─ Lưu vào dashboard_summary
      └─ Sleep delay (0.5s) giữa mỗi user

5. AGGREGATE RAW DATA (Bước 4)
   └─ aggregate_all_raw_data()
      └─ Loop qua từng user_id:
         └─ aggregate_raw_data(user_id, course_id)
            ├─ Query tất cả bảng: enrollments, h5p_scores_summary, 
            │  video_progress_summary, mooc_grades, mooc_progress, 
            │  mooc_discussions, course_stats_benchmarks
            ├─ Tính toán features:
            │  ├─ weeks_since_enrollment
            │  ├─ days_since_last_activity
            │  ├─ h5p_completion_rate
            │  ├─ video_completion_rate
            │  ├─ quiz_avg_score
            │  └─ ...
            ├─ Lấy course_benchmarks
            ├─ calculate_comparative_features()
            │  ├─ relative_to_course_problem_score
            │  ├─ relative_to_course_completion
            │  ├─ performance_percentile
            │  └─ ...
            ├─ Tính labels:
            │  ├─ is_passed (từ mooc_grades)
            │  └─ is_dropout (tự động: inactive > 30 ngày)
            └─ INSERT/UPDATE vào raw_data table

6. HOÀN TẤT
   ├─ Close database
   └─ Log kết quả
```

---

## 🗄️ CÁC BẢNG DATABASE ĐƯỢC SỬ DỤNG

| Bảng | Mục Đích | Được Lưu Bởi |
|------|----------|--------------|
| `enrollments` | Thông tin đăng ký học viên | `save_enrollments()` |
| `h5p_scores` | Chi tiết điểm từng H5P content | `save_h5p_scores()` |
| `h5p_scores_summary` | Tổng hợp điểm H5P | `save_h5p_scores()` |
| `video_progress` | Chi tiết tiến độ từng video | `save_video_progress()` |
| `video_progress_summary` | Tổng hợp tiến độ video | `save_video_progress()` |
| `dashboard_summary` | Tổng hợp tổng thể | `save_combined_progress()` |
| `mooc_grades` | Điểm số MOOC | `save_mooc_grades()` |
| `mooc_progress` | Tiến độ MOOC | `save_mooc_progress()` |
| `mooc_discussions` | Thảo luận MOOC | `save_mooc_discussions()` |
| `course_stats_benchmarks` | Benchmarks của course | `fetch_and_store_course_benchmarks()` |
| `raw_data` | **Bảng chính** - Tổng hợp tất cả | `aggregate_raw_data()` |

---

## 🔑 CÁC API ENDPOINTS ĐƯỢC SỬ DỤNG

### MOOC APIs (Open edX):
1. `GET /api/custom/v1/course-enrollments-attributes/{course_id}/` - Lấy enrollments
2. `GET /api/custom/v1/export/student-grades/{course_id}/` - Lấy bảng điểm
3. `GET /api/custom/v1/export/student-progress/{course_id}/` - Lấy tiến độ
4. `GET /api/custom/v1/export/student-discussions/{course_id}/` - Lấy thảo luận
5. `GET /api/custom/v1/stats/activity/{course_id}/` - Thống kê hoạt động
6. `GET /api/custom/v1/stats/assessment/{course_id}/` - Thống kê đánh giá
7. `GET /api/custom/v1/stats/progress/{course_id}/` - Thống kê tiến độ

### H5P APIs:
1. `GET https://h5p.itp.vn/wp-json/mooc/v1/scores/{user_id}/{course_id}` - Điểm H5P
2. `GET https://h5p.itp.vn/wp-json/mooc/v1/video-progress/{user_id}/{course_id}` - Tiến độ video
3. `GET https://h5p.itp.vn/wp-json/mooc/v1/combined-progress/{user_id}/{course_id}` - Tổng hợp

---

## 💡 LƯU Ý QUAN TRỌNG

1. **Rate Limiting:** Có `delay` (0.5s) giữa các API calls để tránh bị block
2. **Session Cookie:** MOOC APIs cần `sessionid` cookie để authenticate
3. **URL Encoding:** MOOC APIs cần encode course_id, H5P APIs không cần
4. **Pagination:** Enrollments API dùng pagination (limit=200, offset tăng dần)
5. **Error Handling:** Mỗi function có try-catch để log lỗi, không crash toàn bộ script
6. **Transaction:** Mỗi save operation dùng transaction (commit/rollback)
7. **ON DUPLICATE KEY UPDATE:** Tất cả INSERT đều có logic update nếu record đã tồn tại

---

## 🎯 KẾT QUẢ CUỐI CÙNG

Sau khi chạy script, bạn sẽ có:

1. ✅ **Bảng `raw_data`** chứa tất cả features cho ML model
2. ✅ **Các bảng chi tiết** (enrollments, h5p_scores, video_progress, ...) để query riêng lẻ
3. ✅ **Course benchmarks** để so sánh học viên với trung bình lớp
4. ✅ **Labels** (`is_passed`, `is_dropout`) để train model

**Bảng `raw_data` là input chính cho ML model!** 🚀

---

**Tài liệu được tạo:** 2026-01-24
**Phiên bản:** 1.0

