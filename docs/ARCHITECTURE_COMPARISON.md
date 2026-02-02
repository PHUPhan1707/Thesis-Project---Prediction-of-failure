# 🏗️ ARCHITECTURE COMPARISON: V1 vs V2

## 📊 OVERVIEW

| Version | Architecture | Status | Production Ready? |
|---------|--------------|--------|-------------------|
| **V1** | Single table (`raw_data`) | ⚠️ Current | ❌ Prototype only |
| **V2** | 3 tables + 2 support | ✅ Refactored | ✅ Production-ready |

---

## 🔍 DETAILED COMPARISON

### **1. DATA STORAGE**

#### **V1: Single Table (`raw_data`)**

```sql
raw_data (1 table overloaded)
├─ Features (36+ columns)        ← Training + Production data lẫn lộn
├─ Labels (is_dropout, is_passed) ← Chỉ cho training
└─ Predictions (fail_risk_score) ← Overwrite, no history
```

**Problems:**
- ❌ Training data lẫn với production data
- ❌ UPDATE predictions → Mất data cũ
- ❌ Không track được model nào predict
- ❌ Không có history

#### **V2: Separated Tables**

```sql
student_features (Production data)
├─ Real-time features
├─ Updated liên tục
└─ Không có predictions

predictions (Model outputs)
├─ Predictions từ các models
├─ History (không overwrite)
├─ Track model_name, version, timestamp
└─ is_latest flag

training_data (Historical labeled data)
├─ Completed courses có labels
├─ IMMUTABLE
└─ Dùng để train models mới
```

**Benefits:**
- ✅ Tách biệt rõ ràng
- ✅ Có history đầy đủ
- ✅ Track model versions
- ✅ Training data an toàn

---

### **2. MODEL SELECTION**

#### **V1: Hardcoded**

```python
# V1: Hardcode trong code
model_path = "./models/fm101_model_v4.cbm"  # ← Fixed!

# Môn mới?
# → Vẫn dùng FM101 model
# → Không thể config
```

**Problems:**
- ❌ Không tự động chọn model
- ❌ Không quản lý được nhiều models
- ❌ Phải sửa code để đổi model

#### **V2: Auto-selection**

```python
# V2: Tự động chọn từ database
service = get_model_for_course(course_id)
# ↓
# 1. Check course_model_mapping
# 2. Nếu có → Dùng model đã config
# 3. Nếu không → Dùng default model
```

**Configuration:**
```sql
-- Map course → model
INSERT INTO course_model_mapping (course_id, model_name)
VALUES ('course-v1:UEL+NLTT+2026', 'nltt_v1');

-- Môn mới tự động dùng model phù hợp!
```

**Benefits:**
- ✅ Tự động chọn model
- ✅ Config bằng database (không sửa code)
- ✅ Dễ thêm models mới

---

### **3. WORKFLOW MÔN HỌC MỚI**

#### **V1 Workflow:**

```
1. Fetch data
   python fetch_mooc_h5p_data.py --course-id "..."
   ↓
   raw_data created (with fail_risk_score = NULL)

2. ❌ Dashboard KHÔNG hiện môn học
   (Vì code cũ query từ raw_data WHERE fail_risk_score IS NOT NULL)

3. Manual predict
   python predict.py --course-id "..."
   ↓
   UPDATE raw_data SET fail_risk_score = ...

4. ✅ Dashboard hiện môn học

Timeline: 30-60 phút
Steps: 3 manual steps
```

#### **V2 Workflow:**

```
1. Fetch data
   python fetch_mooc_h5p_data.py --course-id "..."
   ↓
   student_features created

2. ✅ Dashboard NGAY LẬP TỨC hiện môn học!
   (Query từ student_features, không cần predictions)

3. Auto predict on-demand
   User click student detail
   ↓
   Backend tự động:
   - Select model phù hợp
   - Predict
   - Save to predictions

Timeline: 0 giây (instant)
Steps: 1 manual step, prediction tự động
```

---

### **4. QUERY PERFORMANCE**

#### **V1 Queries:**

```sql
-- Get students (V1)
SELECT * FROM raw_data
WHERE course_id = '...'
  AND fail_risk_score IS NOT NULL  -- ← Có thể miss records
ORDER BY fail_risk_score DESC;

-- Problems:
-- ❌ Nếu chưa predict → Không thấy student
-- ❌ Join với enrollments mỗi lần
```

#### **V2 Queries:**

```sql
-- Get students (V2)
SELECT 
    f.*,
    COALESCE(p.fail_risk_score, 50) AS fail_risk_score,
    p.model_name
FROM student_features f
LEFT JOIN predictions p ON f.user_id = p.user_id 
    AND f.course_id = p.course_id 
    AND p.is_latest = TRUE
WHERE f.course_id = '...';

-- Benefits:
-- ✅ Luôn thấy students (dù chưa predict)
-- ✅ Có placeholder risk = 50 nếu chưa predict
-- ✅ Track model_name
```

---

### **5. PREDICTIONS MANAGEMENT**

#### **V1: Overwrite**

```sql
-- V1: Update trực tiếp
UPDATE raw_data
SET fail_risk_score = 23.45
WHERE user_id = 123;

-- Problems:
-- ❌ Mất giá trị cũ
-- ❌ Không biết predict lúc nào
-- ❌ Không track model version
```

**Cannot answer:**
- Risk score đã thay đổi như thế nào qua thời gian?
- Prediction này từ model nào?
- Model A vs Model B, model nào tốt hơn?

#### **V2: History with versioning**

```sql
-- V2: Insert mới, mark old as not latest
INSERT INTO predictions (
    user_id, course_id, model_name, model_version,
    fail_risk_score, is_latest
) VALUES (123, '...', 'fm101_v4', 'v4.0.0', 23.45, TRUE);

UPDATE predictions
SET is_latest = FALSE
WHERE user_id = 123 AND is_latest = TRUE;
```

**Can answer:**
```sql
-- Risk timeline
SELECT predicted_at, fail_risk_score, model_name
FROM predictions
WHERE user_id = 123
ORDER BY predicted_at ASC;

-- Compare models
SELECT model_name, AVG(fail_risk_score)
FROM predictions
GROUP BY model_name;
```

---

### **6. CODE COMPLEXITY**

#### **V1: Mixed logic**

```python
# V1: Một service làm tất cả
class ModelV4Service:
    def predict_course(self, course_id, save_db=False):
        # Đọc raw_data
        df = fetch_all("SELECT * FROM raw_data WHERE ...")
        
        # Predict
        predictions = model.predict(df)
        
        # Save (OVERWRITE)
        if save_db:
            execute("UPDATE raw_data SET fail_risk_score = %s WHERE ...")
```

**Problems:**
- ❌ Không reusable (hardcode raw_data)
- ❌ Không support nhiều models
- ❌ Khó test

#### **V2: Clean separation**

```python
# V2: Tách biệt concerns
class ModelV4ServiceV2:
    def __init__(self, model_name='fm101_v4'):
        # Load model từ registry
        model_info = get_model_from_registry(model_name)
        
    def predict_course(self, course_id, save_to_db=True):
        # 1. Fetch features (từ student_features)
        df = self._fetch_student_features(course_id)
        
        # 2. Predict
        predictions = self.model.predict(df)
        
        # 3. Save (INSERT, keep history)
        if save_to_db:
            save_prediction(...)  # ← Generic helper
```

**Benefits:**
- ✅ Reusable
- ✅ Support nhiều models
- ✅ Dễ test
- ✅ Follow SOLID principles

---

## 📈 MIGRATION IMPACT

### **Database Changes:**

```
BEFORE Migration:
├─ enrollments
├─ mooc_grades
├─ raw_data (984 records)          ← Overloaded
└─ interventions

AFTER Migration:
├─ enrollments
├─ mooc_grades
├─ raw_data (984 records)          ← Keep as backup
├─ student_features (984 records)  ← NEW: Production features
├─ predictions (984 records)       ← NEW: Model outputs
├─ training_data (922 records)     ← NEW: Labeled historical data
├─ model_registry (1 model)        ← NEW: Model management
├─ course_model_mapping (2 mappings) ← NEW: Auto-selection
└─ interventions
```

### **Code Changes:**

```
Files changed:
├─ backend/db.py                    ← Added helpers
├─ backend/model_v4_service_v2.py   ← NEW: Refactored service
├─ backend/app_v2.py                ← NEW: Refactored API
├─ database/schema_refactor_v2.sql  ← NEW: Schema
├─ database/migrate_to_v2.py        ← NEW: Migration script
└─ predict_course_v2.py             ← NEW: Predict helper

Files kept (legacy):
├─ backend/model_v4_service.py      ← V1 (reference)
└─ backend/app.py                   ← V1 (fallback)
```

---

## 🎯 USE CASE SCENARIOS

### **Scenario 1: Môn học FM101 (đã có model riêng)**

**V1:**
```python
# Hardcode
model = ModelV4Service(model_path='./models/fm101_model_v4.cbm')
```

**V2:**
```sql
-- Config trong database
INSERT INTO course_model_mapping (course_id, model_name)
VALUES ('course-v1:DHQG-HCM+FM101+2025_S2', 'fm101_v4');

-- Code tự động chọn!
service = get_model_for_course('course-v1:DHQG-HCM+FM101+2025_S2')
# → Returns ModelV4ServiceV2 with fm101_v4 loaded
```

---

### **Scenario 2: Môn mới NLTT (dùng FM101 model tạm)**

**V1:**
```python
# Phải sửa code
model = ModelV4Service(model_path='./models/fm101_model_v4.cbm')
# ← Không linh hoạt
```

**V2:**
```sql
-- Config trong database
INSERT INTO course_model_mapping (course_id, model_name)
VALUES ('course-v1:UEL+NLTT241225+2025_12', 'fm101_v4');

-- Code không đổi, tự động chọn!
service = get_model_for_course('course-v1:UEL+NLTT241225+2025_12')
# → Returns ModelV4ServiceV2 with fm101_v4 loaded
```

---

### **Scenario 3: Train model mới cho NLTT**

**V1:**
```bash
# 1. Export raw_data (lẫn lộn training + production)
# 2. Manual filter completed courses
# 3. Train
# 4. Deploy → Sửa code để dùng model mới
```

**V2:**
```bash
# 1. Export training_data (đã clean, có labels)
SELECT * FROM training_data 
WHERE course_id LIKE '%NLTT%' 
  AND semester = '2025_S2';

# 2. Train
python train_model.py --data training_data --output nltt_v1.cbm

# 3. Register
python register_model.py --name nltt_v1 --path ./models/nltt_v1.cbm

# 4. Map to course
UPDATE course_model_mapping 
SET model_name = 'nltt_v1' 
WHERE course_id LIKE '%NLTT%';

# ✅ Done! Không sửa code!
```

---

## 📊 PERFORMANCE COMPARISON

| Operation | V1 | V2 | Winner |
|-----------|----|----|--------|
| **Thêm môn mới** | 30-60 phút | Instant | 🏆 V2 |
| **Query students** | Fast | Fast | 🤝 Tie |
| **Predict batch** | ~30s | ~30s | 🤝 Tie |
| **Track history** | ❌ Impossible | ✅ Easy | 🏆 V2 |
| **Compare models** | ❌ Impossible | ✅ Easy | 🏆 V2 |
| **Add new model** | Sửa code | Update DB | 🏆 V2 |
| **Rollback prediction** | ❌ Impossible | ✅ Easy | 🏆 V2 |

---

## 🎨 VISUAL COMPARISON

### **V1 Data Flow:**

```
MOOC API
   ↓
fetch_mooc_h5p_data.py
   ↓
raw_data (INSERT with fail_risk_score = NULL)
   ↓
Model V4 predict
   ↓
raw_data (UPDATE fail_risk_score = 23.45)  ← Overwrite!
   ↓
Dashboard query raw_data
```

**Issues:**
- 🔴 Môn mới không hiện cho đến khi predict xong
- 🔴 Không track được predictions history
- 🔴 Mất data cũ khi update

---

### **V2 Data Flow:**

```
MOOC API
   ↓
fetch_mooc_h5p_data.py
   ↓
student_features (INSERT/UPDATE)
   ↓ (Dashboard đã hiện môn học!)
   ↓
Model V4 predict (tự động chọn model!)
   ↓
predictions (INSERT new, mark old as not latest)
   ↓
Dashboard query: student_features JOIN predictions
```

**Benefits:**
- 🟢 Môn mới hiện NGAY LẬP TỨC
- 🟢 Predictions có history đầy đủ
- 🟢 Không mất data cũ
- 🟢 Tự động chọn model phù hợp

---

## 🔄 MIGRATION PATH

### **Option 1: Big Bang (Recommended)**

```bash
# 1. Backup
mysqldump mooc_database > backup.sql

# 2. Migrate
python database/migrate_to_v2.py

# 3. Switch code
mv backend/app.py backend/app_v1.py
mv backend/app_v2.py backend/app.py

# 4. Restart
python backend/app.py

# 5. Test & verify
```

**Timeline:** ~10-20 phút downtime

---

### **Option 2: Gradual (Zero downtime)**

```bash
# Week 1: Deploy V2 tables (keep V1 running)
python database/migrate_to_v2.py
# → V1 backend vẫn chạy (port 5000)

# Week 2: Test V2 backend song song
PORT=5001 python backend/app_v2.py
# → V2 backend test (port 5001)
# → Compare results

# Week 3: Switch production
# Stop V1, start V2 on port 5000

# Week 4: Cleanup
# DROP TABLE raw_data (nếu V2 stable)
```

**Timeline:** 4 tuần, zero downtime

---

## 📚 EXAMPLE QUERIES

### **V1 Queries:**

```sql
-- Get students with predictions
SELECT * FROM raw_data
WHERE course_id = '...' AND fail_risk_score IS NOT NULL;
-- ❌ Miss students chưa predict

-- Get statistics
SELECT AVG(fail_risk_score) FROM raw_data WHERE course_id = '...';
-- ❌ Không biết từ model nào

-- Cannot: Track prediction history
-- Cannot: Compare models
-- Cannot: Rollback predictions
```

---

### **V2 Queries:**

```sql
-- Get students (có prediction + chưa có)
SELECT 
    f.user_id,
    f.mooc_grade_percentage,
    COALESCE(p.fail_risk_score, 50) AS fail_risk_score,
    p.model_name,
    p.predicted_at
FROM student_features f
LEFT JOIN predictions p ON f.user_id = p.user_id 
    AND f.course_id = p.course_id 
    AND p.is_latest = TRUE
WHERE f.course_id = '...';
-- ✅ Always shows all students

-- Track prediction history
SELECT 
    predicted_at,
    model_name,
    fail_risk_score,
    risk_level
FROM predictions
WHERE user_id = 123 AND course_id = '...'
ORDER BY predicted_at ASC;
-- ✅ See how risk changed over time

-- Compare models
SELECT 
    model_name,
    AVG(fail_risk_score) as avg_risk,
    COUNT(CASE WHEN risk_level = 'HIGH' THEN 1 END) as high_risk_count
FROM predictions
WHERE course_id = '...'
GROUP BY model_name;
-- ✅ A/B test models

-- Rollback to previous prediction
UPDATE predictions SET is_latest = TRUE
WHERE id = 12345;  -- Previous prediction ID
-- ✅ Can restore old predictions
```

---

## 🎓 BEST PRACTICES

### **1. Training Data Collection**

```python
# End of semester: Move to training_data
def collect_training_data(course_id: str, semester: str):
    """
    Chuyển completed course vào training_data
    """
    execute("""
        INSERT INTO training_data (...)
        SELECT 
            f.*,
            -- Verified labels
            CASE WHEN f.days_since_last_activity > 30 THEN TRUE ELSE FALSE END as is_dropout,
            f.mooc_is_passed as is_passed,
            f.mooc_grade_percentage as final_grade,
            %s as semester,
            FALSE as used_in_training,
            NULL as training_model
        FROM student_features f
        WHERE f.course_id = %s
          AND f.mooc_is_passed IS NOT NULL  -- Đã có kết quả
    """, (semester, course_id))
```

### **2. Model Versioning**

```sql
-- Register new model version
INSERT INTO model_registry (
    model_name, model_version, model_path,
    accuracy, f1_score, trained_at
) VALUES (
    'fm101_v5',
    'v5.0.0',
    './models/fm101_model_v5.cbm',
    0.89,
    0.87,
    NOW()
);

-- Gradually rollout
UPDATE course_model_mapping
SET model_name = 'fm101_v5'
WHERE course_id = 'course-v1:DHQG-HCM+FM101+2025_S2';
```

### **3. Prediction Refresh**

```python
# Scheduled job: Refresh predictions daily
def refresh_predictions():
    """Cron job: Predict lại mỗi ngày cho active courses"""
    
    courses = fetch_all("""
        SELECT DISTINCT course_id 
        FROM student_features
        WHERE mooc_is_passed IS NULL  -- Chưa hoàn thành
    """)
    
    for course in courses:
        service = get_model_for_course(course['course_id'])
        service.predict_course(course['course_id'], save_to_db=True)
        logger.info(f"Refreshed predictions for {course['course_id']}")
```

---

## ✅ CHECKLIST

### **Before Migration:**
- [ ] Backup database đầy đủ
- [ ] Test migration script trên DB test trước
- [ ] Inform users về downtime (nếu big bang)
- [ ] Prepare rollback plan

### **During Migration:**
- [ ] Stop all backend services
- [ ] Run `migrate_to_v2.py`
- [ ] Verify với `verify_v2_migration.py`
- [ ] Check logs không có errors

### **After Migration:**
- [ ] Switch to V2 code (`app_v2.py` → `app.py`)
- [ ] Restart backend
- [ ] Test API với curl/Postman
- [ ] Test dashboard frontend
- [ ] Verify predictions hoạt động
- [ ] Monitor logs 24h đầu
- [ ] (Optional) Drop/rename raw_data sau 1 tuần

---

## 🚀 QUICK START

```bash
# Full migration trong 5 phút:

# 1. Backup
mysqldump -u root -p mooc_database > backup.sql

# 2. Migrate (Windows)
run_migration_v2.bat

# Hoặc Linux/Mac:
python database/migrate_to_v2.py

# 3. Verify
python verify_v2_migration.py

# 4. Switch code
cd backend
move app.py app_v1.py
move app_v2.py app.py

# 5. Restart
python app.py

# 6. Test
curl http://localhost:5000/api/courses

# Done! ✅
```

---

## 🎉 CONCLUSION

| Metric | V1 | V2 | Improvement |
|--------|----|----|-------------|
| **Tables** | 1 overloaded | 3 + 2 support | +400% clarity |
| **Time to show new course** | 30-60 min | Instant | ∞% faster |
| **Model flexibility** | Hardcode | Auto-select | +∞% |
| **Predictions history** | ❌ No | ✅ Yes | New feature |
| **Training data safety** | ❌ Risk | ✅ Safe | Critical |
| **Production ready** | ❌ No | ✅ Yes | Enterprise-grade |

**V2 = Production-ready ML system!** 🚀

---

## 📞 TROUBLESHOOTING

### **Issue: Migration fails**

```bash
# Check MySQL connection
python -c "from backend.db import get_db_connection; print(get_db_connection())"

# Check raw_data exists
mysql -u root -p -e "SELECT COUNT(*) FROM mooc_database.raw_data"
```

### **Issue: V2 backend errors**

```bash
# Check if tables created
python verify_v2_migration.py

# Check model registry
python -c "from backend.db import fetch_all; print(fetch_all('SELECT * FROM model_registry'))"
```

### **Issue: Predictions not showing**

```sql
-- Check predictions table
SELECT * FROM predictions WHERE course_id = '...' LIMIT 5;

-- Check is_latest flag
SELECT is_latest, COUNT(*) 
FROM predictions 
GROUP BY is_latest;
```

---

**Good luck with the migration!** 🎯
