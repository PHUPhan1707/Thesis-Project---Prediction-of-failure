# 📚 REFACTOR V2 - FILES OVERVIEW

## 🎯 MỤC ĐÍCH

Refactor hệ thống từ **1 table overloaded** (`raw_data`) → **3 tables tách biệt** (`student_features`, `predictions`, `training_data`) để:

✅ Tách biệt training vs production data
✅ Có predictions history & versioning
✅ Auto-select model cho courses
✅ Môn mới hiện instant (không đợi predict)
✅ Production-ready architecture

---

## 📁 FILES ĐÃ TẠO

### **1. Database Schema & Migration**

| File | Mô tả | Khi nào dùng |
|------|-------|--------------|
| `database/schema_refactor_v2.sql` | Schema definition cho 5 tables mới | Review schema trước khi migrate |
| `database/migrate_to_v2.py` | Script tự động migrate data | Chạy migration |
| `run_migration_v2.bat` | Windows batch script (wrapper) | Quick run trên Windows |

---

### **2. Backend Code Refactored**

| File | Mô tả | Thay đổi gì |
|------|-------|------------|
| `backend/db.py` | Database helpers (updated) | Thêm 4 functions: `get_student_features`, `get_latest_prediction`, `save_prediction`, `get_course_model_mapping`, `get_default_model` |
| `backend/model_v4_service_v2.py` | Model service V2 | Đọc từ `student_features`, ghi vào `predictions`, auto-select model |
| `backend/app_v2.py` | Flask API V2 | Query từ `student_features + predictions` thay vì `raw_data` |

**Legacy files (keep as reference):**
- `backend/app.py` (V1)
- `backend/model_v4_service.py` (V1)

---

### **3. Helper Scripts**

| File | Mô tả | Cách dùng |
|------|-------|----------|
| `verify_v2_migration.py` | Verify migration thành công | `python verify_v2_migration.py` |
| `predict_course_v2.py` | Predict course với V2 | `python predict_course_v2.py --course-id "..."` |

---

### **4. Documentation**

| File | Mô tả | Dành cho ai |
|------|-------|------------|
| `REFACTOR_V2_SUMMARY.md` | **⭐ BẮT ĐẦU TỪ ĐÂY** - Tóm tắt ngắn gọn | Everyone |
| `MIGRATION_V2_QUICKSTART.md` | Quick start 5 bước | Developers running migration |
| `REFACTOR_V2_GUIDE.md` | Full documentation (workflow, examples, best practices) | Developers, architects |
| `ARCHITECTURE_COMPARISON.md` | So sánh chi tiết V1 vs V2 | Technical review, learning |
| `REFACTOR_V2_README.md` | **File này** - Overview tất cả files | Navigation |

---

## 🚀 CÁCH SỬ DỤNG

### **Step 1: Đọc docs (5 phút)**

```
Đọc theo thứ tự:
1. REFACTOR_V2_SUMMARY.md      ← Hiểu overview
2. MIGRATION_V2_QUICKSTART.md  ← Biết cách chạy
3. (Optional) REFACTOR_V2_GUIDE.md ← Chi tiết đầy đủ
```

---

### **Step 2: Chạy migration (10 phút)**

**Windows:**
```cmd
run_migration_v2.bat
```

**Linux/Mac:**
```bash
python database/migrate_to_v2.py
python verify_v2_migration.py
```

---

### **Step 3: Switch code (2 phút)**

```bash
cd backend

# Backup V1
move app.py app_v1.py
move model_v4_service.py model_v4_service_v1.py

# Activate V2
move app_v2.py app.py
move model_v4_service_v2.py model_v4_service.py
```

---

### **Step 4: Restart & Test (3 phút)**

```bash
# Restart backend
python backend/app.py

# Test API
curl http://localhost:5000/api/courses

# Test dashboard
# Browser: http://localhost:5173
# Ctrl+Shift+R
```

---

## 📊 SCHEMA DETAILS

### **Table: student_features**

**Purpose:** Real-time student learning data (Production)

**Columns:**
- `user_id`, `course_id` (PK)
- 36+ feature columns (video, quiz, discussion, etc.)
- `updated_at` (auto update timestamp)

**Update frequency:** Mỗi khi fetch data mới từ MOOC/H5P

---

### **Table: predictions**

**Purpose:** Model prediction outputs với history

**Columns:**
- `user_id`, `course_id`
- `model_name`, `model_version`, `model_path`
- `fail_risk_score`, `risk_level`, `confidence_score`
- `snapshot_*` (features snapshot tại thời điểm predict)
- `predicted_at`, `is_latest`

**Insert frequency:** Mỗi khi chạy prediction (on-demand hoặc batch)

---

### **Table: training_data**

**Purpose:** Historical data có verified labels (Training)

**Columns:**
- Same as student_features
- `is_dropout`, `is_passed`, `final_grade` (verified labels)
- `semester`, `snapshot_week`
- `used_in_training`, `training_model`

**Insert frequency:** End of semester (khi courses hoàn thành)

**IMMUTABLE:** Chỉ INSERT, không UPDATE

---

### **Table: model_registry**

**Purpose:** Quản lý available models

**Columns:**
- `model_name`, `model_version`, `model_path`
- `accuracy`, `precision_score`, `recall_score`, `f1_score`
- `domain`, `required_features`
- `is_active`, `is_default`

**Example:**
```sql
INSERT INTO model_registry (model_name, model_version, model_path, is_default)
VALUES ('fm101_v4', 'v4.0.0', './models/fm101_model_v4.cbm', TRUE);
```

---

### **Table: course_model_mapping**

**Purpose:** Map course → model (auto-selection)

**Columns:**
- `course_id`, `model_name`
- `auto_predict`, `predict_frequency`
- `is_active`

**Example:**
```sql
INSERT INTO course_model_mapping (course_id, model_name, auto_predict)
VALUES ('course-v1:DHQG-HCM+FM101+2025_S2', 'fm101_v4', TRUE);
```

---

## 🔧 CODE CHANGES SUMMARY

### **backend/db.py**

**Added functions:**
```python
get_student_features(user_id, course_id)
get_latest_prediction(user_id, course_id, model_name=None)
save_prediction(user_id, course_id, model_name, fail_risk_score, ...)
get_course_model_mapping(course_id)
get_default_model()
```

---

### **backend/model_v4_service_v2.py**

**Key changes:**
```python
# TRƯỚC (V1):
def _fetch_raw_data_for_course(course_id):
    return fetch_all("SELECT * FROM raw_data WHERE ...")

def _save_predictions_to_db(df):
    execute("UPDATE raw_data SET fail_risk_score = ...")

# SAU (V2):
def _fetch_student_features(course_id):
    return fetch_all("SELECT * FROM student_features WHERE ...")

def _save_predictions_to_db(df):
    for row in df:
        save_prediction(...)  # INSERT to predictions, keep history
```

**New function:**
```python
get_model_for_course(course_id) → ModelV4ServiceV2
# Auto-select model từ course_model_mapping
```

---

### **backend/app_v2.py**

**Key changes:**
```python
# TRƯỚC (V1):
@app.get("/api/students/<course_id>")
def get_students():
    rows = fetch_all("SELECT * FROM raw_data WHERE ...")

# SAU (V2):
@app.get("/api/students/<course_id>")
def get_students():
    rows = fetch_all("""
        SELECT f.*, COALESCE(p.fail_risk_score, 50) as fail_risk_score
        FROM student_features f
        LEFT JOIN predictions p ON ... AND p.is_latest = TRUE
        WHERE f.course_id = ...
    """)
    
    # On-demand prediction if needed
    if not has_prediction:
        service = get_model_for_course(course_id)
        service.predict_student(user_id, course_id, save_to_db=True)
```

---

## 📚 DOCUMENTATION GUIDE

### **Bắt đầu từ đâu?**

```
1. REFACTOR_V2_SUMMARY.md         ← START HERE (overview)
   ↓
2. MIGRATION_V2_QUICKSTART.md     ← How to migrate (5 steps)
   ↓
3. Run migration
   ↓
4. REFACTOR_V2_GUIDE.md           ← Detailed guide (use cases, examples)
   ↓
5. ARCHITECTURE_COMPARISON.md     ← Deep dive (V1 vs V2 comparison)
```

### **Quick Reference:**

| Tôi muốn... | Đọc file... |
|-------------|-------------|
| Hiểu tổng quan V2 là gì | `REFACTOR_V2_SUMMARY.md` |
| Chạy migration ngay | `MIGRATION_V2_QUICKSTART.md` |
| Hiểu chi tiết workflow | `REFACTOR_V2_GUIDE.md` |
| So sánh V1 vs V2 | `ARCHITECTURE_COMPARISON.md` |
| Xem schema SQL | `database/schema_refactor_v2.sql` |
| Xem code changes | Diff `app.py` vs `app_v2.py` |

---

## 🎯 MIGRATION CHECKLIST

### **Pre-migration:**
- [ ] Đọc `REFACTOR_V2_SUMMARY.md`
- [ ] Đọc `MIGRATION_V2_QUICKSTART.md`
- [ ] Backup database
- [ ] Stop backend services

### **Migration:**
- [ ] Run `run_migration_v2.bat` (Windows) hoặc `migrate_to_v2.py`
- [ ] Check output không có errors
- [ ] Run `verify_v2_migration.py`
- [ ] Verify tables created và data migrated

### **Post-migration:**
- [ ] Switch backend code (V1 → V2)
- [ ] Restart backend
- [ ] Test API endpoints
- [ ] Test dashboard
- [ ] Verify predictions work
- [ ] Monitor logs 24h

### **Cleanup (sau 1-2 tuần):**
- [ ] Verify V2 stable
- [ ] (Optional) Rename/drop `raw_data`
- [ ] Update `fetch_mooc_h5p_data.py` để INSERT vào `student_features`

---

## 💡 TIPS

### **Tip 1: Test trước trên database test**

```bash
# Create test database
CREATE DATABASE mooc_database_test;

# Copy schema và sample data
mysqldump mooc_database | mysql mooc_database_test

# Test migration
DB_NAME=mooc_database_test python database/migrate_to_v2.py
```

### **Tip 2: Run V1 và V2 song song**

```bash
# Terminal 1: V1 backend (port 5000)
python backend/app.py

# Terminal 2: V2 backend (port 5001)  
PORT=5001 python backend/app_v2.py

# Compare responses
curl http://localhost:5000/api/courses
curl http://localhost:5001/api/courses
```

### **Tip 3: Monitor SQL queries**

```sql
-- Enable query log
SET GLOBAL general_log = 'ON';
SET GLOBAL log_output = 'TABLE';

-- Check queries
SELECT * FROM mysql.general_log
WHERE command_type = 'Query'
ORDER BY event_time DESC
LIMIT 20;
```

---

## 🎉 SUCCESS!

Bạn đã có:
- ✅ 5 new tables (student_features, predictions, training_data, model_registry, course_model_mapping)
- ✅ Refactored backend code (V2)
- ✅ Migration scripts
- ✅ Verification scripts
- ✅ Full documentation

**Sẵn sàng migrate!** 🚀

**Next:** Chạy `run_migration_v2.bat` hoặc xem `MIGRATION_V2_QUICKSTART.md`
