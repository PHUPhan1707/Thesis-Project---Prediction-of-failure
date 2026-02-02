# 🚀 REFACTOR V2: Tách raw_data thành 3 Tables

## 📋 MỤC LỤC

1. [Vấn đề với thiết kế cũ](#vấn-đề)
2. [Kiến trúc mới](#kiến-trúc-mới)
3. [Migration workflow](#migration-workflow)
4. [Cách sử dụng](#cách-sử-dụng)
5. [Benefits](#benefits)

---

## 🐛 VẤN ĐỀ VỚI THIẾT KẾ CŨ

### **Problem: `raw_data` table bị "overload" 3 vai trò**

```
raw_data table (1 table cho tất cả)
├─ Vai trò 1: Training data (historical data có labels)
├─ Vai trò 2: Student features (real-time learning data)  
└─ Vai trò 3: Predictions (model outputs)
   └─ ❌ LẪN LỘN! Không tách biệt!
```

### **Hậu quả:**

| Vấn đề | Mô tả |
|--------|-------|
| ❌ **Data mixing** | Không phân biệt được training vs production data |
| ❌ **Data loss risk** | Update predictions → Mất training data gốc |
| ❌ **No audit trail** | Không track được lịch sử predictions |
| ❌ **No versioning** | Không biết prediction từ model nào, version nào |
| ❌ **Hard to scale** | Nhiều courses, nhiều models → Không quản lý được |
| ❌ **No auto-selection** | Không thể tự động chọn model cho course mới |

---

## ✅ KIẾN TRÚC MỚI

### **3 Tables + 2 Support Tables:**

```
┌────────────────────────────────────────────────────────────────┐
│                    NEW ARCHITECTURE V2                         │
└────────────────────────────────────────────────────────────────┘

1️⃣  STUDENT_FEATURES (Production features)
    ├─ Real-time student learning data
    ├─ Updated liên tục khi fetch data mới
    └─ Source: MOOC API, H5P API, etc.

2️⃣  PREDICTIONS (Model outputs)
    ├─ Kết quả predictions từ các models
    ├─ Có history (không overwrite)
    ├─ Track model_name, model_version, predicted_at
    └─ is_latest flag để query nhanh

3️⃣  TRAINING_DATA (Historical labeled data)
    ├─ Data đã có ground truth labels (is_passed, is_dropout)
    ├─ IMMUTABLE - chỉ INSERT, không UPDATE
    ├─ Dùng để train models mới
    └─ Track semester, snapshot_week

4️⃣  MODEL_REGISTRY (Model management)
    ├─ Danh sách các models available
    ├─ Metadata: path, version, accuracy, domain
    └─ is_default, is_active flags

5️⃣  COURSE_MODEL_MAPPING (Auto selection)
    ├─ Map course → model
    ├─ auto_predict, predict_frequency config
    └─ Tự động chọn model phù hợp
```

---

## 🔄 MIGRATION WORKFLOW

### **BƯỚC 1: Backup database**

```bash
# Export toàn bộ database
mysqldump -u root -p mooc_database > backup_before_v2_$(date +%Y%m%d).sql

# Hoặc chỉ backup raw_data
mysqldump -u root -p mooc_database raw_data > raw_data_backup_$(date +%Y%m%d).sql
```

### **BƯỚC 2: Chạy migration**

```bash
cd d:\ProjectThesis\dropout_prediction

# Chạy migration script
python database/migrate_to_v2.py
```

**Script sẽ:**
1. ✅ Tạo 5 tables mới (student_features, predictions, training_data, model_registry, course_model_mapping)
2. ✅ Migrate data từ raw_data:
   - Tất cả records → student_features
   - Records có fail_risk_score → predictions
   - Records có labels (is_passed NOT NULL) → training_data
3. ✅ Insert default model vào model_registry
4. ✅ Insert course mappings
5. ✅ Tạo views cho backward compatibility
6. ✅ Verify migration

**Output mẫu:**
```
================================================================================
🚀 DATABASE MIGRATION: raw_data → 3 Tables (V2)
================================================================================

STEP 1: CREATE NEW SCHEMA
   ✅ Schema created successfully

STEP 2: MIGRATE DATA
   ✅ Migrated 984 records to student_features
   ✅ Migrated 984 predictions
   ✅ Migrated 922 training records

STEP 3: VERIFY MIGRATION
📊 Record counts:
   - raw_data (legacy):        984
   - student_features:         984
   - predictions:              984
   - training_data:            922

✅ MIGRATION COMPLETED SUCCESSFULLY!
```

### **BƯỚC 3: Verify migration**

```bash
python verify_v2_migration.py
```

**Kiểm tra:**
- ✅ Tables đã tạo
- ✅ Data đã migrate đủ
- ✅ Model registry có config
- ✅ Course mappings hoạt động

### **BƯỚC 4: Update backend code**

**Option A: Chuyển hẳn sang V2** (Recommended)
```bash
# Rename files
mv backend/app.py backend/app_v1_legacy.py
mv backend/app_v2.py backend/app.py

mv backend/model_v4_service.py backend/model_v4_service_v1_legacy.py
mv backend/model_v4_service_v2.py backend/model_v4_service.py
```

**Option B: Chạy song song để test**
```bash
# Terminal 1: Backend V1 (port 5000)
python backend/app.py

# Terminal 2: Backend V2 (port 5001)
PORT=5001 python backend/app_v2.py

# Test cả 2, so sánh kết quả
```

### **BƯỚC 5: Test API**

```bash
# Test V2 API
curl http://localhost:5001/api/courses
curl http://localhost:5001/api/students/course-v1:DHQG-HCM+FM101+2025_S2
curl http://localhost:5001/api/statistics/course-v1:DHQG-HCM+FM101+2025_S2
```

### **BƯỚC 6: (Optional) Rename raw_data**

Sau khi verify V2 hoạt động tốt:

```sql
-- Rename raw_data thành legacy backup
RENAME TABLE raw_data TO raw_data_legacy_backup_20260129;

-- Hoặc DROP nếu đã backup đầy đủ
-- DROP TABLE raw_data;
```

---

## 🎯 CÁCH SỬ DỤNG SAU KHI MIGRATE

### **1. Thêm môn học mới**

```bash
# Fetch data từ MOOC/H5P
python database/fetch_mooc_h5p_data.py \
    --course-id "course-v1:UEL+NEWCOURSE+2026" \
    --sessionid "your_session_id"
```

**Kết quả:**
```
✅ enrollments ← Có ngay
✅ mooc_grades ← Có ngay  
✅ student_features ← Có ngay (script tự động INSERT)
❌ predictions ← Chưa có (chưa predict)
```

**Dashboard:**
```
✅ Môn học HIỆN NGAY trong dropdown
✅ Student list hiển thị được (với placeholder risk = 50)
⏳ Risk scores chưa chính xác (chưa predict)
```

---

### **2. Predict với Model V4**

**Auto prediction (khi user click student detail):**
```python
# backend/app_v2.py - Tự động predict on-demand
@app.get("/api/student/<user_id>/<course_id>")
def get_student_detail():
    # Nếu chưa có prediction
    if not has_prediction:
        service = get_model_for_course(course_id)  # ← Tự động chọn model!
        service.predict_student(user_id, course_id, save_to_db=True)
```

**Manual batch prediction:**
```bash
# Predict toàn bộ course
curl -X POST http://localhost:5001/api/predict-v4/course-v1:UEL+NEWCOURSE+2026

# Hoặc dùng Python
python predict_course_v2.py --course-id "course-v1:UEL+NEWCOURSE+2026"
```

**Kết quả:**
```sql
-- predictions table
user_id | course_id | model_name | fail_risk_score | predicted_at
--------|-----------|------------|-----------------|------------------
123     | NEWCOURSE | fm101_v4   | 23.45          | 2026-01-29 10:00
456     | NEWCOURSE | fm101_v4   | 67.89          | 2026-01-29 10:00
```

---

### **3. Query data cho Dashboard**

**Get students with latest predictions:**
```sql
SELECT 
    e.full_name,
    f.mooc_grade_percentage,
    COALESCE(p.fail_risk_score, 50) AS fail_risk_score,
    p.risk_level,
    p.model_name,
    p.predicted_at
FROM enrollments e
JOIN student_features f ON e.user_id = f.user_id AND e.course_id = f.course_id
LEFT JOIN predictions p ON f.user_id = p.user_id 
    AND f.course_id = p.course_id 
    AND p.is_latest = TRUE
WHERE f.course_id = 'course-v1:...'
```

**Get course statistics:**
```sql
SELECT
    COUNT(*) AS total_students,
    AVG(COALESCE(p.fail_risk_score, 50)) AS avg_risk_score,
    AVG(f.mooc_grade_percentage) AS avg_grade,
    SUM(CASE WHEN p.fail_risk_score >= 70 AND f.mooc_is_passed != 1 THEN 1 ELSE 0 END) AS high_risk_count
FROM student_features f
LEFT JOIN predictions p ON f.user_id = p.user_id 
    AND f.course_id = p.course_id 
    AND p.is_latest = TRUE
WHERE f.course_id = 'course-v1:...'
```

---

### **4. Quản lý Models**

**Thêm model mới:**
```sql
INSERT INTO model_registry (
    model_name, model_version, model_path, features_csv_path,
    model_type, domain, is_active, is_default
) VALUES (
    'nltt_v1',
    'v1.0.0',
    './models/nltt_model_v1.cbm',
    './models/nltt_model_v1_features.csv',
    'CatBoost',
    'linguistics',
    TRUE,
    FALSE
);
```

**Map model cho course:**
```sql
INSERT INTO course_model_mapping (
    course_id, model_name, auto_predict, predict_frequency
) VALUES (
    'course-v1:UEL+NLTT241225+2025_12',
    'nltt_v1',
    TRUE,
    'daily'
);
```

**Kết quả:**
```
✅ Course NLTT tự động dùng model nltt_v1
✅ Course FM101 tự động dùng model fm101_v4
✅ Courses khác dùng default model
```

---

### **5. Prepare Training Data (cho model mới)**

Sau khi semester kết thúc:

```sql
-- Chuyển completed courses vào training_data
INSERT INTO training_data (
    user_id, course_id, 
    -- ... all features ...
    is_dropout, is_passed, final_grade,
    semester, used_in_training, training_model
)
SELECT 
    f.*,
    CASE WHEN f.days_since_last_activity > 30 THEN TRUE ELSE FALSE END as is_dropout,
    f.mooc_is_passed as is_passed,
    f.mooc_grade_percentage as final_grade,
    '2026_S1' as semester,
    FALSE as used_in_training,
    NULL as training_model
FROM student_features f
WHERE f.course_id = 'course-v1:COMPLETED_COURSE'
  AND f.mooc_is_passed IS NOT NULL;  -- Đã có kết quả cuối kỳ
```

Sau đó train model mới:
```bash
python train_new_model.py \
    --data-source training_data \
    --where "semester='2026_S1'" \
    --output nltt_model_v1.cbm
```

---

## 📊 SO SÁNH V1 vs V2

| Aspect | V1 (raw_data) | V2 (3 tables) |
|--------|---------------|---------------|
| **Training data** | ❌ Lẫn với production | ✅ Riêng (training_data) |
| **Student features** | ❌ Cùng table | ✅ Riêng (student_features) |
| **Predictions** | ❌ Overwrite | ✅ History, versioning |
| **Model selection** | ❌ Hardcode | ✅ Auto (model_registry + mapping) |
| **Audit trail** | ❌ Không có | ✅ Có (predictions history) |
| **Multiple models** | ❌ Không support | ✅ Support đầy đủ |
| **Data integrity** | ❌ Dễ mất data | ✅ An toàn (immutable training_data) |
| **Scalability** | ❌ Khó scale | ✅ Dễ scale |

---

## 🎯 BENEFITS

### **1. Tách biệt rõ ràng**
```
Training data    ← IMMUTABLE (chỉ INSERT, không UPDATE)
Student features ← MUTABLE (update liên tục)
Predictions      ← APPEND-ONLY (có history)
```

### **2. Auto model selection**
```python
# Code tự động chọn model!
service = get_model_for_course('course-v1:UEL+NLTT+2026')
# ↓
# Kiểm tra course_model_mapping
# → Nếu có: Dùng model đã map
# → Nếu không: Dùng default model
```

### **3. Predictions history**
```sql
-- Xem tất cả predictions cho 1 student (track over time)
SELECT predicted_at, model_name, fail_risk_score, risk_level
FROM predictions
WHERE user_id = 123 AND course_id = 'course-v1:...'
ORDER BY predicted_at DESC;

-- So sánh models
SELECT 
    model_name,
    AVG(fail_risk_score) as avg_risk,
    COUNT(*) as predictions
FROM predictions
WHERE course_id = 'course-v1:...'
GROUP BY model_name;
```

### **4. On-demand prediction**
```
User click student detail
    ↓
Backend check: Có prediction chưa?
    ├─ Có: Trả về ngay
    └─ Chưa: 
        ├─ Auto-select model
        ├─ Predict on-the-fly
        └─ Save to predictions
```

### **5. Clean training pipeline**
```bash
# 1. Collect training data (end of semester)
python collect_training_data.py --semester 2026_S1

# 2. Train new model
python train_model.py --source training_data --semester 2026_S1

# 3. Register model
python register_model.py --name nltt_v2 --path ./models/nltt_v2.cbm

# 4. Map to courses
python map_model.py --course NLTT --model nltt_v2

# ✅ Done! Auto prediction works!
```

---

## 📝 WORKFLOW CHO MÔN HỌC MỚI

### **Scenario: Thêm môn "Python Programming 2026"**

**TRƯỚC (V1):**
```bash
1. python fetch_mooc_h5p_data.py --course-id "..."
   → Data vào raw_data
   
2. ❌ Dashboard KHÔNG hiện môn học (vì chưa có raw_data đầy đủ)

3. Phải manual predict:
   python predict.py --course-id "..."
   
4. Môn học mới hiện

Timeline: ~30-60 phút
```

**SAU (V2):**
```bash
1. python fetch_mooc_h5p_data.py --course-id "..."
   → Data vào student_features
   
2. ✅ Dashboard NGAY LẬP TỨC hiện môn học!

3. User click student → Auto predict on-demand
   → Tự động chọn model phù hợp
   → Save to predictions
   
4. Done!

Timeline: ~0 giây (instant)
```

---

## 🔧 CODE CHANGES

### **1. fetch_mooc_h5p_data.py**

**Cần update để INSERT vào `student_features` thay vì `raw_data`:**

```python
# TRƯỚC:
INSERT INTO raw_data (user_id, course_id, ...) VALUES (...)

# SAU:
INSERT INTO student_features (user_id, course_id, ...) VALUES (...)
ON DUPLICATE KEY UPDATE
    mooc_grade_percentage = VALUES(mooc_grade_percentage),
    mooc_completion_rate = VALUES(mooc_completion_rate),
    updated_at = CURRENT_TIMESTAMP
```

### **2. model_v4_service_v2.py**

**Đọc từ student_features, ghi vào predictions:**

```python
def predict_course(self, course_id: str, save_to_db: bool = True):
    # 1. Fetch từ student_features (thay vì raw_data)
    df = self._fetch_student_features(course_id)
    
    # 2. Feature engineering
    features_df = self._feature_engineer(df)
    
    # 3. Predict
    predictions = self.model.predict_proba(X)
    
    # 4. Save vào predictions table (thay vì UPDATE raw_data)
    if save_to_db:
        self._save_predictions_to_db(results_df)
```

### **3. app_v2.py**

**Query từ student_features + predictions:**

```python
@app.get("/api/students/<course_id>")
def get_students(course_id: str):
    rows = fetch_all(f"""
        SELECT
            f.user_id,
            f.mooc_grade_percentage,
            COALESCE(p.fail_risk_score, 50) AS fail_risk_score,
            p.model_name
        FROM student_features f
        LEFT JOIN predictions p ON f.user_id = p.user_id 
            AND f.course_id = p.course_id 
            AND p.is_latest = TRUE
        WHERE f.course_id = %s
    """, (course_id,))
```

---

## 🎨 USE CASES

### **Use Case 1: Compare models**

```python
# Predict cùng course với 2 models khác nhau
service_v4 = ModelV4ServiceV2(model_name='fm101_v4')
service_v4.predict_course('course-v1:FM101', save_to_db=True)

service_v5 = ModelV4ServiceV2(model_name='fm101_v5')
service_v5.predict_course('course-v1:FM101', save_to_db=True)

# Query để so sánh
SELECT 
    model_name,
    AVG(fail_risk_score) as avg_risk,
    COUNT(*) as total
FROM predictions
WHERE course_id = 'course-v1:FM101'
GROUP BY model_name;
```

### **Use Case 2: Track prediction drift over time**

```sql
-- Xem risk score thay đổi như thế nào qua thời gian
SELECT 
    user_id,
    predicted_at,
    fail_risk_score,
    snapshot_grade,
    snapshot_completion_rate
FROM predictions
WHERE user_id = 123 AND course_id = 'course-v1:...'
ORDER BY predicted_at ASC;

-- Chart: Risk score timeline
-- Week 2: 75% (HIGH)
-- Week 4: 60% (MEDIUM)
-- Week 6: 45% (MEDIUM)
-- Week 8: 30% (LOW)  ← Intervention thành công!
```

### **Use Case 3: A/B testing models**

```python
# Assign 50% students to model A, 50% to model B
for student in students[:len(students)//2]:
    service_a.predict_student(student, save_to_db=True)

for student in students[len(students)//2:]:
    service_b.predict_student(student, save_to_db=True)

# Compare results
# Xem model nào predict chính xác hơn
```

---

## 📚 FILES CREATED

```
dropout_prediction/
├─ database/
│  ├─ schema_refactor_v2.sql          ← New schema (5 tables)
│  └─ migrate_to_v2.py                ← Migration script
│
├─ backend/
│  ├─ db.py                           ← Updated (new helpers)
│  ├─ model_v4_service_v2.py          ← Refactored service
│  ├─ app_v2.py                       ← Refactored API
│  ├─ app.py (legacy)                 ← Keep for reference
│  └─ model_v4_service.py (legacy)    ← Keep for reference
│
├─ verify_v2_migration.py             ← Verification script
└─ REFACTOR_V2_GUIDE.md               ← This file
```

---

## ⚠️ MIGRATION CHECKLIST

**Trước khi migrate:**
- [ ] Backup database đầy đủ
- [ ] Stop tất cả backend services
- [ ] Inform users (downtime ~5-10 phút)

**Trong quá trình migrate:**
- [ ] Chạy `migrate_to_v2.py`
- [ ] Verify với `verify_v2_migration.py`
- [ ] Check log không có errors

**Sau khi migrate:**
- [ ] Test API V2 với curl/Postman
- [ ] Test dashboard frontend
- [ ] Verify predictions hoạt động
- [ ] Monitor logs
- [ ] (Optional) Rename/drop raw_data cũ

---

## 🚀 QUICK START

```bash
# 1. Backup
mysqldump -u root -p mooc_database > backup_v1.sql

# 2. Migrate
cd d:\ProjectThesis\dropout_prediction
python database/migrate_to_v2.py

# 3. Verify
python verify_v2_migration.py

# 4. Switch to V2 backend
mv backend/app.py backend/app_v1.py
mv backend/app_v2.py backend/app.py

# 5. Restart backend
# Ctrl+C (stop old backend)
python backend/app.py

# 6. Test
curl http://localhost:5000/
curl http://localhost:5000/api/courses
curl http://localhost:5000/api/students/course-v1:DHQG-HCM+FM101+2025_S2

# 7. Refresh frontend
# Ctrl+Shift+R in browser
```

---

## 💡 ROLLBACK PLAN

Nếu V2 có vấn đề:

```bash
# 1. Stop V2 backend
Ctrl+C

# 2. Restore V1 code
mv backend/app_v1.py backend/app.py

# 3. (Optional) Restore database
mysql -u root -p mooc_database < backup_v1.sql

# 4. Start V1 backend
python backend/app.py
```

---

## ✅ SUCCESS CRITERIA

Migration thành công khi:

- ✅ All 5 tables created (student_features, predictions, training_data, model_registry, course_model_mapping)
- ✅ Data migrated completely (counts match)
- ✅ API V2 returns correct data
- ✅ Dashboard displays correctly
- ✅ Predictions work (both batch and on-demand)
- ✅ Auto model selection works
- ✅ No errors in logs

---

## 🎉 CONCLUSION

**V2 Architecture cung cấp:**
- ✅ Clean separation of concerns
- ✅ Production-ready ML system
- ✅ Auto model selection
- ✅ Predictions history & auditing
- ✅ Easy to scale & maintain
- ✅ Support multiple models
- ✅ Better UX (instant course visibility)

**Từ prototype → Production-grade system!** 🚀

---

## 📞 SUPPORT

Nếu gặp vấn đề:
1. Check logs: Backend có errors không?
2. Verify migration: `python verify_v2_migration.py`
3. Test queries: Chạy SQL trực tiếp trong MySQL
4. Rollback nếu cần: Restore từ backup

**Good luck!** 🎯
