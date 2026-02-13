# H5P Content Performance Analytics - Quick Start

## 🎯 Tóm tắt

Đã tạo 3 API mới để phân tích performance H5P content:

1. **Low Performance Contents** - Top bài H5P khó nhất
2. **Content Detail** - Chi tiết từng bài (ai làm tốt/kém)
3. **Student Performance** - Overview H5P của sinh viên

---

## 🚀 Chạy Server

```bash
cd d:/ProjectThesis/dropout_prediction/backend
python app.py
```

Server: `http://localhost:5000`

---

## 📡 API Endpoints

### 1. Top bài H5P khó nhất

```
GET /api/h5p-analytics/{course_id}/low-performance?limit=10&min_students=5
```

**Response**: Danh sách bài có điểm TB thấp nhất + tỉ lệ hoàn thành kém

### 2. Chi tiết một bài H5P

```
GET /api/h5p-analytics/{course_id}/content/{content_id}
```

**Response**: Phân bố điểm + danh sách sinh viên theo performance

### 3. H5P performance của sinh viên

```
GET /api/h5p-analytics/{course_id}/student/{user_id}
```

**Response**: Bài nào làm tốt/kém + statistics

---

## 🧪 Test

```bash
# Sửa COURSE_ID trong file trước
python test_h5p_analytics.py
```

---

## 📚 Tài liệu đầy đủ

- **API Documentation**: `docs/API_H5P_ANALYTICS.md`
- **Summary & Insights**: `docs/H5P_ANALYTICS_SUMMARY.md`

---

## 💡 Use Cases Chính

### Cho Giáo viên:
- ✅ Xem bài nào khó → cần giải thích lại
- ✅ Tìm sinh viên cần hỗ trợ cho từng bài
- ✅ Theo dõi tiến độ H5P của sinh viên

### Cho Dashboard:
- ✅ Hiển thị "Top 10 bài khó nhất" với màu sắc
- ✅ Alert khi bài có > 50% SV không làm
- ✅ Profile sinh viên với tab H5P performance

---

## 🎨 Ví dụ Visualization

**Difficulty Levels**:
- 🔴 HIGH: avg_score < 50 hoặc completion < 50
- 🟡 MEDIUM: avg_score < 70 hoặc completion < 70
- 🟢 LOW: avg_score >= 70 và completion >= 70

**Student Categories**:
- ⭐ High Performers: >= 80%
- 📊 Medium Performers: 50-79%
- 📉 Low Performers: < 50%
- ❌ Not Attempted: Chưa làm

---

## ⚠️ Lưu ý

- Course ID cần URL encode: `course-v1:VNUHCM+FM101+2024_T1` → `course-v1%3AVNUHCM%2BFM101%2B2024_T1`
- Database table: `h5p_scores` (phải có dữ liệu)
- `finished = 0` nghĩa là chưa hoàn thành

---

**Files đã tạo**:
- ✅ `backend/app.py` - 3 endpoints mới (dòng 574-932)
- ✅ `test_h5p_analytics.py` - Test script
- ✅ `docs/API_H5P_ANALYTICS.md` - API docs chi tiết
- ✅ `docs/H5P_ANALYTICS_SUMMARY.md` - Summary & insights
- ✅ `H5P_ANALYTICS_README.md` - Quick start (file này)
