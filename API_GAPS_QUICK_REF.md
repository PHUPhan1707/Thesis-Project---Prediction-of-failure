# 📊 API Gap Analysis - Quick Reference

## Hiện Trạng

**APIs hiện có:** 24 endpoints  
**Đang dùng:** 7 endpoints (per-user current data)  
**Vấn đề:** Thiếu **behavioral history** và **time-series data**

---

## APIs Còn Thiếu (Top 3 Critical)

### **1. Activity Stats per User** ⭐⭐⭐ CRITICAL
```http
GET /users/{user_id}/activity-stats/{course_id}/
```
**Return:**
- problem_improvement_rate (% cải thiện qua thời gian)
- activity_consistency (0-1, học đều hay không)
- longest_streak (chuỗi ngày học liên tục)
- late_night_ratio (học ban đêm = stress)

**Impact:** +3-4% recall = **30-40 students** thêm được cứu

---

### **2. Progress Weekly** ⭐⭐⭐ CRITICAL
```http
GET /users/{user_id}/progress-weekly/{course_id}/
```
**Return:**
- weekly_progress array (tiến độ từng tuần)
- velocity (blocks/week)
- velocity_trend ("declining" = warning!)
- is_on_track (có kịp deadline không)

**Impact:** +4-5% recall = **40-50 students** thêm

**Would be #1 most important feature!**

---

### **3. Assessment Details** ⭐⭐⭐ CRITICAL
```http
GET /users/{user_id}/assessments/{course_id}/
```
**Return:**
- avg_attempts_to_pass (>3 = struggling)
- first_attempt_avg vs best_attempt_avg
- improvement_gap
- pass_rate

**Impact:** +2-3% recall = **20-30 students** thêm

---

## ROI Calculation

**Investment:** ~$30,000 (4 devs × 6 weeks)

**Return:**
- Phase 1 (2 APIs): +63-88 students saved
- Tuition value: $10,000/student
- **Total value: $630,000 - $880,000**

**ROI: 21-29x** 🚀

---

## Implementation Priority

| Phase | APIs | Duration | Impact | Students Saved |
|-------|------|----------|--------|----------------|
| **Phase 1** | Activity + Progress | 4 weeks | +7-9% recall | **+65-83** |
| **Phase 2** | Assessments + Video | 3 weeks | +3-5% recall | **+28-46** |
| **Phase 3** | Enhancements | 2 weeks | +1-2% recall | **+10-20** |

**Total:** 9 weeks → **+103-149 students saved!**

---

## Database Changes Needed

```sql
-- Track activity history
CREATE TABLE user_activity_history (
    user_id INT,
    course_id VARCHAR(255),
    week_number INT,
    activity_count INT,
    avg_score DECIMAL(5,2),
    INDEX (user_id, course_id, week_number)
);

-- Weekly progress snapshots
CREATE TABLE progress_snapshots (
    user_id INT,
    course_id VARCHAR(255),
    week_number INT,
    completion_percentage DECIMAL(5,2),
    velocity DECIMAL(5,2),
    INDEX (user_id, course_id, week_number)
);
```

---

## Expected Model Performance

| Metric | Current (V4) | Phase 1 (V5) | All Phases (V6) |
|--------|-------------|--------------|-----------------|
| **Recall** | 83.64% | **90-93%** | **92-95%** |
| **Students Caught** | 197/235 | **260-285** | **280-295** |
| **Improvement** | - | **+63-88** | **+83-98** |

---

## Quick Wins (No Code Needed)

Có thể improve ngay bằng cách **add timestamps** vào existing responses:

1. `/mooc-export/discussions/` → Add `activity_timestamp`
2. `/mooc-export/progress/` → Add `last_updated_at`
3. H5P `/scores/` → Add `submitted_at` per score

**Impact:** +1-2% recall immediately

---

## Documents

- **Full Analysis:** `api_gap_analysis.md` (artifact)
- **API Requirements:** `api_requirements.md` (artifact)
- **Sample Responses:** `api_sample_responses.json`

---

## Next Steps

1. ✅ Review gap analysis với backend team
2. ✅ Estimate effort cho Phase 1 (4 weeks?)
3. ✅ Design database schema cho activity tracking
4. ✅ Implement Phase 1 APIs
5. ✅ Train Model V5
6. ✅ Measure improvement

**Timeline:** Start Feb 2026 → Production Mar 2026
