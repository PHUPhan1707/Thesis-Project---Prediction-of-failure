# 📊 Prediction Results Summary

## File Output

**File:** `data/predictions_v4.csv`  
**Size:** 153 KB  
**Records:** 921 students  

## Columns

1. `user_id` - ID của sinh viên
2. `course_id` - ID khóa học
3. `mooc_grade_percentage` - Điểm số hiện tại (%)
4. `fail_risk_score` - Điểm rủi ro fail (0-100%)
5. `risk_level` - Mức độ rủi ro (HIGH/MEDIUM/LOW)
6. `suggestions` - Gợi ý can thiệp

## Risk Distribution

- **HIGH risk (>70%):** 235 students (25.5%)
- **MEDIUM risk (40-70%):** 60 students (6.5%)
- **LOW risk (<40%):** 626 students (68.0%)

## Top At-Risk Students

| User ID | Fail Risk | Risk Level | Current Grade |
|---------|-----------|------------|---------------|
| 18      | 98.2%     | HIGH       | 0.0%          |
| 65      | 98.2%     | HIGH       | 0.0%          |
| 102     | 98.2%     | HIGH       | 0.0%          |
| 113     | 98.2%     | HIGH       | 0.0%          |
| 114     | 98.2%     | HIGH       | 0.0%          |

## Model Used

**Model V4** - With Option 2 Comparative Features
- Precision: 86.79%
- Recall: 83.64%
- F1-Score: 85.19%

## How to Use

1. Open `data/predictions_v4.csv` in Excel/Google Sheets
2. Sort by `fail_risk_score` descending to see highest risk students first
3. Filter by `risk_level = 'HIGH'` to focus on urgent cases
4. Use `suggestions` column for intervention recommendations

## Files Available

- CSV: `data/predictions_v4.csv`
- Model: `models/fm101_model_v4.cbm`
- Metrics: `models/fm101_model_v4_metrics.pkl`
- Comparison: Run `python compare_models.py`
