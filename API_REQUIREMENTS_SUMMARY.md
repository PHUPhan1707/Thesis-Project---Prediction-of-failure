# 🎯 API Requirements - Quick Summary for Backend Team

## Vấn Đề Hiện Tại

**Current APIs chỉ trả về course-level data:**
```json
{
  "avg_score": 75.5,  // Toàn khóa học
  "total_activities": 8500  // Tổng của tất cả students
}
```

**Cần:** Per-user data để ML dự đoán chính xác hơn!

---

## 3 Endpoints Cần Implement

### **1. Activity Stats per Student**
```
GET /api/courses/{course_id}/students/{user_id}/activity-stats/?days=90
```

**Trả về:**
- Problem attempts, scores, improvement rate
- Activity consistency (học đều hay không)
- Time patterns (học ban đêm, cuối tuần)
- Streaks (chuỗi ngày học liên tục)

### **2. Assessment Details per Student**
```
GET /api/courses/{course_id}/students/{user_id}/assessments/
```

**Trả về:**
- Average attempts to pass (thử mấy lần mới đạt)
- First attempt vs best score (cải thiện như thế nào)
- Time spent per assessment
- Pass/fail rate

### **3. Progress Tracking per Student**
```
GET /api/courses/{course_id}/students/{user_id}/progress-weekly/
```

**Trả về:**
- Weekly completion rate
- Velocity (tốc độ học, blocks/week)
- Trend (đang nhanh lên hay chậm lại)
- On track status (có kịp deadline không)

---
