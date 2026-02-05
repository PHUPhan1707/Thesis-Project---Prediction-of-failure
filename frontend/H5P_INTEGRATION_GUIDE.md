# H5P Performance Integration Guide

## ✅ Đã hoàn thành

Đã tích hợp **H5P Performance Widget** vào trang Overview của Dashboard để hiển thị các bài H5P làm tốt/kém nhất.

---

## 📁 Files đã tạo/sửa

### Frontend Files

1. **`src/services/api.ts`** ✅
   - Thêm 3 API functions:
     - `getH5PLowPerformance()` - Lấy danh sách bài H5P khó
     - `getH5PContentDetail()` - Chi tiết một bài H5P
     - `getH5PStudentPerformance()` - Performance H5P của sinh viên

2. **`src/components/Dashboard/H5PPerformance.tsx`** ✅ (MỚI)
   - Component hiển thị H5P performance
   - 2 chế độ xem: "Khó nhất" và "Dễ nhất"
   - Statistics summary
   - Danh sách top 10 bài

3. **`src/components/Dashboard/H5PPerformance.css`** ✅ (MỚI)
   - Styling cho H5P Performance widget
   - Responsive design
   - Color coding cho điểm số

4. **`src/components/Dashboard/index.ts`** ✅
   - Export H5PPerformance component

5. **`src/pages/Overview.tsx`** ✅
   - Import và thêm H5PPerformance vào page
   - Thêm section mới dưới dashboard grid

6. **`src/pages/Overview.css`** ✅
   - Thêm styling cho h5p-section

---

## 🎨 UI Features

### H5P Performance Widget bao gồm:

1. **Header với 2 chế độ xem**:
   - 📉 **Khó nhất**: Top 10 bài có điểm TB thấp nhất
   - ⭐ **Dễ nhất**: Top 10 bài có điểm TB cao nhất

2. **Statistics Summary** (4 metrics):
   - Tổng bài phân tích
   - Điểm TB (với color coding)
   - Tỉ lệ hoàn thành TB (với color coding)
   - Bài cần chú ý (highlighted)

3. **Content List** (Mỗi item hiển thị):
   - Rank number
   - Difficulty icon (🔴/🟡/🟢)
   - Tên bài và folder
   - 3 metrics: Điểm TB, Hoàn thành, Số SV
   - Badge "⚠️ Cần chú ý" (nếu có)

4. **Footer**:
   - Button "🔄 Làm mới" để reload data

### Color Coding

**Điểm số**:
- 🟢 Excellent: >= 80% (xanh lá)
- 🔵 Good: >= 70% (xanh dương)
- 🟡 Average: >= 50% (vàng)
- 🔴 Poor: < 50% (đỏ)

**Tỉ lệ hoàn thành**:
- 🟢 High: >= 80%
- 🟡 Medium: >= 60%
- 🔴 Low: < 60%

**Difficulty Level**:
- 🔴 HIGH: avg_score < 50 hoặc completion < 50
- 🟡 MEDIUM: avg_score < 70 hoặc completion < 70
- 🟢 LOW: avg_score >= 70 và completion >= 70

---

## 🚀 Cách sử dụng

### 1. Đảm bảo Backend đang chạy

```bash
cd d:/ProjectThesis/dropout_prediction/backend
python app.py
```

Backend phải có endpoint: `/api/h5p-analytics/{course_id}/low-performance`

### 2. Chạy Frontend

```bash
cd d:/ProjectThesis/dropout_prediction/frontend
npm run dev
```

### 3. Xem kết quả

1. Mở browser: `http://localhost:5173`
2. Chọn một khóa học
3. Vào trang **Overview**
4. Scroll xuống dưới → Thấy widget **"H5P Performance"**

---

## 🎯 Use Cases

### Cho Giáo viên:

1. **Xem bài khó nhất**:
   - Click tab "📉 Khó nhất"
   - Xem top 10 bài có điểm TB thấp
   - Nhận biết bài nào cần giải thích lại

2. **Xem bài dễ nhất**:
   - Click tab "⭐ Dễ nhất"
   - Xem top 10 bài sinh viên làm tốt
   - Hiểu nội dung nào sinh viên đã nắm vững

3. **Theo dõi metrics**:
   - Điểm TB toàn khóa
   - Tỉ lệ hoàn thành
   - Số bài cần chú ý

4. **Làm mới data**:
   - Click button "🔄 Làm mới"
   - Reload dữ liệu mới nhất

---

## 📊 Data Flow

```
Frontend (Overview.tsx)
    ↓
H5PPerformance Component
    ↓
api.getH5PLowPerformance(courseId, limit=20, minStudents=3)
    ↓
Backend API: /api/h5p-analytics/{course_id}/low-performance
    ↓
Database: h5p_scores table
    ↓
Response: { success, statistics, contents[] }
    ↓
Display in Widget
```

---

## ⚙️ Configuration

Có thể tùy chỉnh trong `H5PPerformance.tsx`:

```typescript
// Line 43: Số lượng bài lấy từ API
const data = await getH5PLowPerformance(selectedCourse, 20, 3);
//                                                      ^^  ^ min_students
//                                                      limit

// Line 99: Số bài hiển thị trong mỗi tab
return h5pData.contents.slice(0, 10);
//                               ^^ hiển thị top 10
```

---

## 🎨 Styling Customization

### Thay đổi màu sắc

Sửa trong `H5PPerformance.css`:

```css
/* Line 1-8: Background gradient */
.h5p-performance-card {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
  /* Thay đổi màu gradient ở đây */
}

/* Line 143-162: Score colors */
.score-excellent { color: #10b981 !important; } /* Xanh lá */
.score-good { color: #3b82f6 !important; }      /* Xanh dương */
.score-average { color: #f59e0b !important; }   /* Vàng */
.score-poor { color: #ef4444 !important; }      /* Đỏ */
```

### Thay đổi kích thước

```css
/* Line 259: Max height của content list */
.h5p-content-list {
  max-height: 500px; /* Tăng/giảm chiều cao */
}

/* Line 296: Item padding */
.h5p-content-item {
  padding: 0.875rem; /* Tăng/giảm padding */
}
```

---

## 🐛 Troubleshooting

### 1. Widget không hiển thị

**Nguyên nhân**: Backend chưa chạy hoặc API endpoint không tồn tại

**Giải pháp**:
```bash
# Check backend
curl http://localhost:5000/api/health

# Test H5P endpoint
curl "http://localhost:5000/api/h5p-analytics/course-v1%3AVNUHCM%2BFM101%2B2024_T1/low-performance?limit=5&min_students=3"
```

### 2. Hiển thị "Chưa có dữ liệu H5P"

**Nguyên nhân**: Database không có dữ liệu H5P cho khóa học này

**Giải pháp**:
```sql
-- Kiểm tra trong database
SELECT COUNT(*) FROM h5p_scores WHERE course_id = 'YOUR_COURSE_ID';
```

### 3. Lỗi "Cannot read property 'contents'"

**Nguyên nhân**: API response format không đúng

**Giải pháp**:
- Check console log để xem response
- Đảm bảo backend trả về đúng format: `{ success, statistics, contents }`

### 4. Loading mãi không xong

**Nguyên nhân**: API call bị timeout hoặc lỗi

**Giải pháp**:
- Mở DevTools → Network tab
- Xem request có failed không
- Check backend logs

---

## 🔄 Updates & Enhancements

### Đã có:
- ✅ View mode toggle (Khó/Dễ)
- ✅ Statistics summary
- ✅ Color coding
- ✅ Responsive design
- ✅ Loading/Error states
- ✅ Refresh button

### Có thể thêm:
- [ ] Click vào item → Xem chi tiết bài (modal)
- [ ] Export CSV
- [ ] Filter theo folder
- [ ] Search bar
- [ ] Sort options
- [ ] Chart visualization
- [ ] Time range selector

---

## 📝 Notes

1. **Performance**: Component tự động load khi chọn course
2. **Caching**: Không có cache, mỗi lần vào page sẽ load lại
3. **Real-time**: Cần click "Làm mới" để update data
4. **Min Students**: Mặc định yêu cầu ít nhất 3 SV làm bài để tính vào kết quả

---

## 🎉 Kết quả

Giờ trang **Overview** có widget **H5P Performance** hiển thị:

```
┌────────────────────────────────────────┐
│ 📊 H5P Performance                     │
│    Bài tập nào làm tốt/kém nhất       │
│                                        │
│ [📉 Khó nhất] [⭐ Dễ nhất]            │
│                                        │
│ ┌──────────────────────────────────┐  │
│ │ Tổng bài: 45 | Điểm TB: 65.3%   │  │
│ │ Hoàn thành: 70.2% | Cần chú ý: 12│ │
│ └──────────────────────────────────┘  │
│                                        │
│ 1. 🔴 Bài tập về hàm số               │
│    Chương 3 - Hàm số                  │
│    Điểm: 45.5% | Hoàn thành: 62%     │
│    ⚠️ Cần chú ý                       │
│                                        │
│ 2. 🟡 Bài tập về tích phân            │
│    ...                                 │
│                                        │
│ [🔄 Làm mới]                          │
└────────────────────────────────────────┘
```

**Giáo viên có thể:**
- ✅ Biết bài nào khó → Giải thích lại
- ✅ Biết bài nào dễ → Sinh viên đã hiểu
- ✅ Track metrics → Theo dõi progress
- ✅ Nhanh chóng nhận biết bài cần attention

---

**Happy coding! 🚀**
