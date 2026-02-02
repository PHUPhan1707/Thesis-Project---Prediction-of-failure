# 🏗️ V2 ARCHITECTURE - VISUAL DIAGRAM

## 📊 ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                      REFACTOR V2 ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────┐
                    │   MOOC/H5P APIs      │
                    └──────────┬───────────┘
                               │
                               ↓
                ┌──────────────────────────────┐
                │  fetch_mooc_h5p_data.py      │
                │  (ETL Script)                │
                └──────────────┬───────────────┘
                               │
                               ↓
        ┌──────────────────────────────────────────────┐
        │         DATABASE LAYER (MySQL)                │
        ├──────────────────────────────────────────────┤
        │                                               │
        │  ┌────────────────────────────────────┐      │
        │  │  1. STUDENT_FEATURES              │      │
        │  │  (Production real-time data)      │      │
        │  │  - user_id, course_id             │      │
        │  │  - 36+ feature columns            │      │
        │  │  - updated_at                     │      │
        │  └───────────┬────────────────────────┘      │
        │              │                                │
        │              ↓                                │
        │  ┌────────────────────────────────────┐      │
        │  │  2. PREDICTIONS                   │      │
        │  │  (Model outputs + history)        │      │
        │  │  - user_id, course_id             │      │
        │  │  - model_name, model_version      │      │
        │  │  - fail_risk_score, risk_level    │      │
        │  │  - predicted_at, is_latest        │      │
        │  └────────────────────────────────────┘      │
        │                                               │
        │  ┌────────────────────────────────────┐      │
        │  │  3. TRAINING_DATA                 │      │
        │  │  (Historical labeled data)        │      │
        │  │  - Same as student_features       │      │
        │  │  - is_dropout, is_passed (labels) │      │
        │  │  - semester, snapshot_week        │      │
        │  │  - IMMUTABLE                      │      │
        │  └────────────────────────────────────┘      │
        │                                               │
        │  ┌────────────────────────────────────┐      │
        │  │  4. MODEL_REGISTRY                │      │
        │  │  (Available models)               │      │
        │  │  - model_name, version, path      │      │
        │  │  - accuracy, domain               │      │
        │  │  - is_active, is_default          │      │
        │  └────────────────────────────────────┘      │
        │                                               │
        │  ┌────────────────────────────────────┐      │
        │  │  5. COURSE_MODEL_MAPPING          │      │
        │  │  (Auto-selection config)          │      │
        │  │  - course_id → model_name         │      │
        │  │  - auto_predict, frequency        │      │
        │  └────────────────────────────────────┘      │
        └──────────────────────────────────────────────┘
                               │
                               ↓
        ┌──────────────────────────────────────────────┐
        │         BACKEND API (Flask)                   │
        ├──────────────────────────────────────────────┤
        │                                               │
        │  model_v4_service_v2.py                      │
        │  ├─ Auto-select model (from mapping)         │
        │  ├─ Fetch from student_features              │
        │  ├─ Predict                                   │
        │  └─ Save to predictions (with history)       │
        │                                               │
        │  app_v2.py                                   │
        │  ├─ GET /api/courses (from enrollments)      │
        │  ├─ GET /api/students (JOIN student_features │
        │  │                       + predictions)       │
        │  ├─ GET /api/statistics                      │
        │  └─ POST /api/predict-v4 (trigger predict)   │
        └──────────────────┬───────────────────────────┘
                           │
                           ↓
        ┌──────────────────────────────────────────────┐
        │         FRONTEND (React Dashboard)            │
        └──────────────────────────────────────────────┘
```

---

## 🔄 DATA FLOW COMPARISON

### **V1: Overloaded `raw_data`**

```
┌─────────────┐
│  MOOC API   │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────┐
│         raw_data                    │
│  ┌───────────────────────────────┐ │
│  │ Features (36 cols)            │ │
│  │ Labels (is_dropout, is_passed)│ │  ← Training
│  │ Predictions (fail_risk_score) │ │  ← Production
│  └───────────────────────────────┘ │
│        ❌ MIXED! OVERLOADED!        │
└─────────────┬───────────────────────┘
              │
              ↓
        Dashboard query
        (Miss students if not predicted)
```

---

### **V2: Separated Tables**

```
┌─────────────┐
│  MOOC API   │
└──────┬──────┘
       │
       ↓
┌──────────────────────┐
│ student_features     │  ← Production features
│ (Real-time data)     │
└──────────┬───────────┘
           │
           ↓
    ┌──────────────┐
    │   Model V4   │  ← Auto-selected
    │   Predict    │
    └──────┬───────┘
           │
           ↓
┌──────────────────────┐
│    predictions       │  ← Model outputs
│ (History + version)  │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────┐
│  training_data       │  ← Historical (end of semester)
│  (IMMUTABLE)         │
└──────────────────────┘
           │
           ↓
     Train new model
```

---

## 🎯 WORKFLOW COMPARISON

### **V1 Workflow: Môn học mới**

```
Step 1: Fetch data
   python fetch_mooc_h5p_data.py --course-id "..."
   ↓
   raw_data created (fail_risk_score = NULL)

Step 2: ❌ Dashboard KHÔNG hiện môn
   (API query: WHERE fail_risk_score IS NOT NULL)

Step 3: Manual predict
   python predict.py --course-id "..."
   ↓
   UPDATE raw_data SET fail_risk_score = ...

Step 4: ✅ Dashboard hiện môn

Timeline: 30-60 phút | Steps: 3 manual | UX: ❌ Poor
```

---

### **V2 Workflow: Môn học mới**

```
Step 1: Fetch data
   python fetch_mooc_h5p_data.py --course-id "..."
   ↓
   student_features created

Step 2: ✅ Dashboard NGAY LẬP TỨC hiện môn!
   (API query: FROM student_features, không cần predictions)

Step 3: Auto predict (on-demand)
   User click student
   ↓
   Backend auto: get_model_for_course()
   ↓
   Predict + Save to predictions

Step 4: ✅ Risk scores chính xác

Timeline: Instant | Steps: 1 manual | UX: ✅ Excellent
```

---

## 🎨 QUERY PATTERNS

### **Pattern 1: Get students with latest predictions**

```sql
-- V2 Query
SELECT 
    e.full_name,
    e.email,
    f.mooc_grade_percentage,
    f.mooc_completion_rate,
    COALESCE(p.fail_risk_score, 50) AS fail_risk_score,
    COALESCE(p.risk_level, 'MEDIUM') AS risk_level,
    p.model_name,
    p.predicted_at
FROM enrollments e
JOIN student_features f 
    ON e.user_id = f.user_id AND e.course_id = f.course_id
LEFT JOIN predictions p 
    ON f.user_id = p.user_id 
    AND f.course_id = p.course_id 
    AND p.is_latest = TRUE
WHERE f.course_id = %s
ORDER BY fail_risk_score DESC;
```

**Benefits:**
- ✅ Always shows all students (dù chưa predict)
- ✅ Placeholder risk = 50 nếu chưa có prediction
- ✅ Track model_name và predicted_at

---

### **Pattern 2: Track prediction history**

```sql
-- V2 Query
SELECT 
    p.predicted_at,
    p.model_name,
    p.model_version,
    p.fail_risk_score,
    p.risk_level,
    p.snapshot_grade,
    p.snapshot_completion_rate
FROM predictions p
WHERE p.user_id = %s AND p.course_id = %s
ORDER BY p.predicted_at ASC;
```

**Use case:** Chart risk score timeline

---

### **Pattern 3: Compare models**

```sql
-- V2 Query
SELECT 
    p.model_name,
    COUNT(*) as total_predictions,
    AVG(p.fail_risk_score) as avg_risk,
    COUNT(CASE WHEN p.risk_level = 'HIGH' THEN 1 END) as high_risk_count,
    MIN(p.predicted_at) as first_prediction,
    MAX(p.predicted_at) as last_prediction
FROM predictions p
WHERE p.course_id = %s
GROUP BY p.model_name;
```

**Use case:** A/B test models, chọn model tốt nhất

---

## 🔮 FUTURE ENHANCEMENTS

### **Phase 3: Real-time predictions**

```python
# Celery background worker
@celery.task
def auto_predict_courses():
    """Chạy mỗi giờ, tự động predict courses active"""
    
    courses = fetch_all("""
        SELECT DISTINCT f.course_id
        FROM student_features f
        LEFT JOIN predictions p ON f.course_id = p.course_id 
            AND p.predicted_at > NOW() - INTERVAL 1 DAY
        WHERE f.mooc_is_passed IS NULL
          AND p.id IS NULL  -- Chưa predict trong 24h
    """)
    
    for course in courses:
        service = get_model_for_course(course['course_id'])
        service.predict_course(course['course_id'], save_to_db=True)
```

### **Phase 4: Multi-model ensemble**

```python
# Combine predictions từ nhiều models
def ensemble_predict(course_id: str):
    services = [
        ModelV4ServiceV2(model_name='fm101_v4'),
        ModelV4ServiceV2(model_name='fm101_v5'),
        ModelV4ServiceV2(model_name='nltt_v1'),
    ]
    
    predictions = []
    for service in services:
        pred = service.predict_course(course_id, save_to_db=True)
        predictions.append(pred)
    
    # Average or weighted average
    ensemble_score = weighted_average(predictions)
```

### **Phase 5: Model performance tracking**

```sql
CREATE TABLE model_performance (
    model_name VARCHAR(100),
    course_id VARCHAR(255),
    accuracy DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    evaluated_at DATETIME
);

-- Track which model performs best per course
```

---

## 📝 SUMMARY

**V1 (Old):**
```
raw_data
└─ Everything mixed together ❌
```

**V2 (New):**
```
student_features    ← Production features
predictions         ← Model outputs (history)
training_data       ← Historical labeled data
model_registry      ← Model management
course_model_mapping ← Auto-selection
```

**Result:** Production-ready ML system! ✅

---

**START HERE:** `REFACTOR_V2_SUMMARY.md` 🚀
