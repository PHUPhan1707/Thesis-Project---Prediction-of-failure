# Tổng hợp H5P Content Performance Analytics

## Tổng quan dự án

Đã tạo bộ API phân tích performance H5P content để giúp giáo viên:
- Xác định các bài H5P khó, có điểm thấp
- Tìm sinh viên cần hỗ trợ cho từng bài cụ thể
- Theo dõi performance H5P của từng sinh viên

---

## 🎯 Các tính năng đã triển khai

### 1. API: Low Performance Contents
**Endpoint**: `GET /api/h5p-analytics/{course_id}/low-performance`

**Chức năng**: 
- Liệt kê các bài H5P có điểm TB thấp và tỉ lệ hoàn thành kém nhất
- Sắp xếp theo điểm TB từ thấp đến cao
- Phân loại mức độ khó (HIGH/MEDIUM/LOW)

**Metrics**:
- `avg_score`: Điểm trung bình của tất cả sinh viên (kể cả chưa làm)
- `avg_score_completed`: Điểm TB của sinh viên đã hoàn thành
- `completion_rate`: Tỉ lệ sinh viên hoàn thành bài
- `total_students`: Tổng số sinh viên trong khóa học
- `completed_students`: Số sinh viên đã hoàn thành

**Use Cases**:
- Dashboard hiển thị "Top 10 bài khó nhất"
- Alert khi có bài có > 50% sinh viên không làm
- Xác định nội dung cần giải thích lại

---

### 2. API: Content Detail Analytics
**Endpoint**: `GET /api/h5p-analytics/{course_id}/content/{content_id}`

**Chức năng**:
- Chi tiết performance của một bài H5P cụ thể
- Phân bố điểm số (excellent, good, average, below_average, poor, not_attempted)
- Danh sách sinh viên theo performance (high/medium/low performers)

**Metrics**:
- **Score Distribution**: Phân loại theo 6 nhóm điểm
- **Student Lists**: Danh sách chi tiết sinh viên từng nhóm với điểm số, thời gian làm

**Use Cases**:
- Xem sinh viên nào cần hỗ trợ cho bài này
- Gửi email nhắc nhở cho sinh viên chưa làm
- Phân tích tại sao bài này khó

---

### 3. API: Student H5P Performance
**Endpoint**: `GET /api/h5p-analytics/{course_id}/student/{user_id}`

**Chức năng**:
- Overview performance H5P của một sinh viên
- Danh sách bài làm tốt/kém/chưa hoàn thành
- Thống kê điểm TB, số bài mỗi loại

**Metrics**:
- `avg_score`: Điểm TB các bài đã làm
- `total_attempted`: Số bài đã hoàn thành
- `total_in_progress`: Số bài đang làm dở
- Phân loại: excellent (90+), good (80-89), needs_improvement (50-79), poor (<50)

**Use Cases**:
- Profile sinh viên trong dashboard
- Gợi ý bài nào cần làm lại
- Theo dõi tiến độ H5P của sinh viên

---

## 📊 Database Schema

### Bảng sử dụng: `h5p_scores`

```sql
CREATE TABLE h5p_scores (
    id BIGINT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id VARCHAR(255) NOT NULL,
    content_id INT NOT NULL,
    content_title VARCHAR(500),
    score INT DEFAULT 0,
    max_score INT DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    opened BIGINT DEFAULT 0,          -- UNIX timestamp
    finished BIGINT DEFAULT 0,        -- UNIX timestamp
    time_spent BIGINT DEFAULT 0,      -- seconds
    folder_id INT,
    folder_name VARCHAR(255),
    fetched_at DATETIME,
    INDEX idx_user_course (user_id, course_id),
    INDEX idx_content_id (content_id)
);
```

**Quan trọng**:
- `finished = 0`: Bài chưa hoàn thành hoặc chưa làm
- `finished > 0`: Bài đã hoàn thành
- `percentage`: Phần trăm điểm (0-100)
- `time_spent`: Thời gian làm bài tính bằng giây

---

## 🔧 Cài đặt và Test

### 1. Chạy Backend API

```bash
cd d:/ProjectThesis/dropout_prediction/backend
python app.py
```

Server sẽ chạy tại: `http://localhost:5000`

### 2. Test APIs

```bash
cd d:/ProjectThesis/dropout_prediction
python test_h5p_analytics.py
```

Script test sẽ:
- Kiểm tra server có chạy không
- Test cả 3 endpoints
- Hiển thị kết quả chi tiết

**Lưu ý**: Sửa `COURSE_ID` trong `test_h5p_analytics.py` thành course_id thực tế của bạn.

---

## 📱 Ví dụ sử dụng

### Example 1: Lấy Top 10 bài khó nhất

```bash
curl "http://localhost:5000/api/h5p-analytics/course-v1%3AVNUHCM%2BFM101%2B2024_T1/low-performance?limit=10&min_students=5"
```

**Kết quả**: Danh sách 10 bài H5P có điểm TB thấp nhất (phải có ít nhất 5 sinh viên làm).

### Example 2: Chi tiết bài H5P id=123

```bash
curl "http://localhost:5000/api/h5p-analytics/course-v1%3AVNUHCM%2BFM101%2B2024_T1/content/123"
```

**Kết quả**: 
- Thông tin tổng quan bài 123
- Phân bố điểm
- Danh sách sinh viên theo performance

### Example 3: Performance H5P của sinh viên user_id=101

```bash
curl "http://localhost:5000/api/h5p-analytics/course-v1%3AVNUHCM%2BFM101%2B2024_T1/student/101"
```

**Kết quả**: Overview tất cả bài H5P sinh viên 101 đã làm.

---

## 🎨 Gợi ý hiển thị trong Frontend

### Dashboard cho Giáo viên

#### 1. Widget: "Bài H5P cần chú ý"
```
╔══════════════════════════════════════════════════╗
║  📊 BÀI H5P CẦN CHÚ Ý (12 bài)                   ║
╠══════════════════════════════════════════════════╣
║  🔴 Bài tập về hàm số                            ║
║     Điểm TB: 45.5% | Hoàn thành: 62%             ║
║     28/45 sinh viên đã làm                       ║
║                                                  ║
║  🔴 Bài tập về tích phân                         ║
║     Điểm TB: 48.2% | Hoàn thành: 58%             ║
║     23/45 sinh viên đã làm                       ║
║                                                  ║
║  🟡 Bài tập về ma trận                           ║
║     Điểm TB: 65.0% | Hoàn thành: 70%             ║
║     32/45 sinh viên đã làm                       ║
╚══════════════════════════════════════════════════╝
```

**Màu sắc**:
- 🔴 Red: avg_score < 50 hoặc completion_rate < 50
- 🟡 Yellow: avg_score < 70 hoặc completion_rate < 70
- 🟢 Green: avg_score >= 70 và completion_rate >= 70

#### 2. Chi tiết một bài H5P

```
╔══════════════════════════════════════════════════╗
║  Bài tập về hàm số                               ║
║  Chương 3 - Hàm số                               ║
╠══════════════════════════════════════════════════╣
║  📈 THỐNG KÊ                                     ║
║  • Điểm TB: 45.5%                                ║
║  • Hoàn thành: 28/45 (62%)                       ║
║  • Thời gian TB: 12.5 phút                       ║
║                                                  ║
║  📊 PHÂN BỐ ĐIỂM                                 ║
║  ████████████████████ 90-100: 3 SV               ║
║  ██████████ 80-89: 5 SV                          ║
║  ████████████████ 70-79: 8 SV                    ║
║  ██████████████ 50-69: 7 SV                      ║
║  ██████████ 0-49: 5 SV                           ║
║  ██████████████████████████████████ Chưa: 17 SV  ║
║                                                  ║
║  👥 SINH VIÊN CẦN HỖ TRỢ (5 sinh viên)           ║
║  • Trần Thị B (20120002) - Điểm: 30%            ║
║  • Lê Văn C (20120003) - Điểm: 35%              ║
║  [Xem thêm...]                                   ║
╚══════════════════════════════════════════════════╝
```

#### 3. Profile sinh viên - Tab H5P

```
╔══════════════════════════════════════════════════╗
║  Nguyễn Văn A (20120001)                         ║
║  H5P Performance Overview                        ║
╠══════════════════════════════════════════════════╣
║  📊 THỐNG KÊ                                     ║
║  • Điểm TB: 72.5%                                ║
║  • Bài đã làm: 15/20                             ║
║  • Đang làm: 2 bài                               ║
║                                                  ║
║  ⭐ XUẤT SẮC (5 bài)                             ║
║  • Bài tập về đạo hàm - 95%                     ║
║  • Bài tập về giới hạn - 92%                    ║
║  [Xem thêm...]                                   ║
║                                                  ║
║  ⚠️ CẦN CẢI THIỆN (4 bài)                        ║
║  • Bài tập về tích phân - 55%                   ║
║  • Bài tập về ma trận - 58%                     ║
║  [Xem thêm...]                                   ║
║                                                  ║
║  📉 KÉM (2 bài)                                  ║
║  • Bài tập về hàm số - 35%  [Làm lại]           ║
║  • Bài tập về chuỗi - 40%   [Làm lại]           ║
╚══════════════════════════════════════════════════╝
```

---

## 🚀 Roadmap & Enhancements

### Đã hoàn thành ✅
- [x] API lấy danh sách bài H5P khó
- [x] API chi tiết performance từng bài
- [x] API performance H5P của sinh viên
- [x] Phân loại difficulty level
- [x] Score distribution
- [x] Tài liệu API đầy đủ
- [x] Test script

### Có thể mở rộng 🔮

#### Short-term
- [ ] **Export to Excel**: Export danh sách bài khó/sinh viên cần hỗ trợ ra Excel
- [ ] **Email template**: Tạo template email để gửi cho sinh viên
- [ ] **Time series**: Theo dõi performance theo thời gian
- [ ] **Comparison**: So sánh performance giữa các khóa học

#### Medium-term
- [ ] **Recommendations**: AI gợi ý can thiệp dựa trên pattern
- [ ] **Clustering**: Nhóm sinh viên theo learning pattern
- [ ] **Prediction**: Dự đoán sinh viên nào sẽ gặp khó khăn với bài nào

#### Long-term
- [ ] **Adaptive learning**: Gợi ý bài tập phù hợp với từng sinh viên
- [ ] **Content optimization**: Gợi ý cải thiện nội dung bài H5P
- [ ] **Peer comparison**: So sánh với performance trung bình của khóa

---

## 🔍 Insights có thể rút ra

### Từ Low Performance API:
1. **Content Quality**: Bài nào quá khó → cần review lại nội dung
2. **Teaching Gap**: Nhiều bài khó cùng topic → cần giảng thêm
3. **Engagement**: Tỉ lệ hoàn thành thấp → bài không hấp dẫn hoặc quá dài

### Từ Content Detail API:
1. **Student Segmentation**: Nhóm sinh viên nào cần hỗ trợ
2. **Time Analysis**: Thời gian làm bài vs điểm số
3. **Completion Pattern**: Ai mở nhưng không làm xong

### Từ Student Performance API:
1. **Learning Pattern**: Sinh viên mạnh/yếu phần nào
2. **Intervention Priority**: Bài nào cần làm lại
3. **Progress Tracking**: Theo dõi tiến bộ theo thời gian

---

## 📞 Support

Nếu gặp lỗi hoặc cần hỗ trợ:
1. Kiểm tra server có chạy: `curl http://localhost:5000/`
2. Kiểm tra database có dữ liệu: Query trực tiếp `h5p_scores` table
3. Xem log: Check console output khi chạy `python app.py`
4. Test API: Chạy `python test_h5p_analytics.py`

---

## 📝 Notes

- Course ID cần URL encode khi gọi API
- Thời gian lưu dưới dạng UNIX timestamp (seconds)
- `finished = 0` nghĩa là chưa hoàn thành
- Tất cả điểm số ở dạng percentage (0-100)
- Min students mặc định = 5 để tránh sample size nhỏ

---

**Tạo bởi**: AI Assistant
**Ngày tạo**: 2026-02-05
**Version**: 1.0.0
