# 🎯 Option 2 Quick Implementation - Next Steps

## ✅ Đã Hoàn Thành

1. **Database Schema:**
   - ✅ Migration 06: activity_stats, assessment_details, progress_tracking tables
   - ✅ Migration 07: course_stats_benchmarks table + 8 comparative columns
   - ✅ All migrations applied to Docker MySQL

2. **Code Templates:**
   - ✅ `option2_implementation.py` - Complete functions
   - ✅ Implementation guide - Step-by-step instructions

---

## 📝 Bước Tiếp Theo (User phải làm)

### **Bước 1: Integrate Code** ⏳

Mở `database/fetch_mooc_h5p_data.py` và:

1. **Copy methods** từ `database/option2_implementation.py` vào class `MOOCH5PDataFetcher` (trước method `aggregate_raw_data`)

2. **Update `fetch_all_mooc_export_data()`** - Add sau line 921:
   ```python
   # After discussions:
   logger.info("Fetching course-level benchmarks...")
   self.fetch_and_store_course_benchmarks(course_id)
   ```

3. **Update `aggregate_raw_data()`** - Xem chi tiết trong implementation_plan.md, cần:
   - Add comparative features calculation
   - Update INSERT query với 8 columns mới
   - Update values tuple
   - Update ON DUPLICATE KEY UPDATE

### **Bước 2: Test Collection** ⏳

```bash
python database/fetch_mooc_h5p_data.py --course-id "course-v1:DHQG-HCM+FM101+2025_S2"
```

**Verify:**
```bash
# Check benchmarks
docker exec -it dropout_prediction_mysql mysql -u dropout_user -pdropout_pass_123 dropout_prediction_db -e "SELECT * FROM course_stats_benchmarks\G"

# Check comparative features
docker exec -it dropout_prediction_mysql mysql -u dropout_user -pdropout_pass_123 dropout_prediction_db -e "SELECT user_id, performance_percentile, is_below_course_average FROM raw_data LIMIT 10;"
```

### **Bước 3: Retrain Model** ⏳

```bash
python ml/feature_engineering.py --course-id "course-v1:DHQG-HCM+FM101+2025_S2" --output data/features_v3.csv
python ml/train_model.py --input data/features_v3.csv --model-name fm101_model_v4
```

---

## 📊 Expected Results

**Current (Model v3):**
- AUC-ROC: 0.9766
- Top feature: current_chapter (21.96)

**Expected (Model v4 with Option 2):**
- AUC-ROC: **0.98-0.99** ✨
- Top features:
  1. **performance_percentile** (new!)
  2. **relative_to_course_completion** (new!)
  3. current_chapter
  4. **is_below_course_average** (new!)

---

## 📁 Files Created

- `database/migrations/07_add_course_benchmarks.sql` - Schema
- `database/option2_implementation.py` - Code template
- `implementation_plan.md` - Detailed guide

---

## 🆘 Need Help?

Xem file `implementation_plan.md` để biết:
- Detailed integration steps
- Code snippets to copy-paste
- Troubleshooting guide
