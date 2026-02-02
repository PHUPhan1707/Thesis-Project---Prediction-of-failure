# ⚡ MIGRATION V2 - QUICK START

## 🎯 TL;DR

**Vấn đề:** `raw_data` lẫn lộn training + production + predictions
**Giải pháp:** Tách thành 3 tables riêng biệt
**Timeline:** 10-20 phút migration + testing

---

## 🚀 5 BƯỚC CHẠY MIGRATION

### **BƯỚC 1: Backup** (2 phút)

```bash
cd d:\ProjectThesis\dropout_prediction
mysqldump -u root -p mooc_database > backup_before_v2.sql
```

---

### **BƯỚC 2: Migrate** (3-5 phút)

**Windows:**
```cmd
run_migration_v2.bat
```

**Linux/Mac:**
```bash
python database/migrate_to_v2.py
```

**Kết quả mong đợi:**
```
✅ Schema created
✅ Migrated 984 to student_features
✅ Migrated 984 to predictions  
✅ Migrated 922 to training_data
✅ MIGRATION COMPLETED!
```

---

### **BƯỚC 3: Verify** (1 phút)

```bash
python verify_v2_migration.py
```

**Kết quả mong đợi:**
```
✅ student_features: 984 records
✅ predictions: 984 records
✅ model_registry: 1 model
✅ MIGRATION SUCCESSFUL!
```

---

### **BƯỚC 4: Switch Backend Code** (1 phút)

```bash
cd backend

# Backup V1
move app.py app_v1_legacy.py
move model_v4_service.py model_v4_service_v1_legacy.py

# Activate V2
move app_v2.py app.py
move model_v4_service_v2.py model_v4_service.py
```

---

### **BƯỚC 5: Restart & Test** (2-5 phút)

**Terminal backend:**
```bash
# Stop old backend (Ctrl+C)
cd d:\ProjectThesis\dropout_prediction
python backend\app.py
```

**Test API:**
```bash
# Terminal mới
curl http://localhost:5000/
curl http://localhost:5000/api/courses
curl http://localhost:5000/api/students/course-v1:DHQG-HCM+FM101+2025_S2
```

**Test Dashboard:**
```
1. Browser: http://localhost:5173
2. Ctrl+Shift+R (hard reload)
3. Chọn khóa học
4. Verify: Hiển thị đúng students và risk scores
```

---

## ✅ SUCCESS CHECKLIST

Sau migration, verify:

- [ ] API `/api/courses` trả về đúng courses
- [ ] API `/api/students` trả về students với risk scores
- [ ] API `/api/statistics` trả về stats chính xác
- [ ] Dashboard hiển thị đúng
- [ ] Môn mới hiện ngay trong dropdown (không cần predict trước)
- [ ] Click student detail → Thấy predictions
- [ ] No errors trong backend logs
- [ ] No errors trong browser console

---

## 🔧 TROUBLESHOOTING

### **Error: "Table already exists"**

```bash
# Tables đã tồn tại từ lần chạy trước
# → OK, script sẽ skip CREATE TABLE (IF NOT EXISTS)
# → Migration vẫn chạy được
```

### **Error: "Access denied"**

```bash
# Check .env file
cat .env | grep DB_

# Test connection
python -c "from backend.db import get_db_connection; print(get_db_connection())"
```

### **Error: "No data migrated"**

```bash
# Check raw_data có data không
python -c "from backend.db import fetch_one; print(fetch_one('SELECT COUNT(*) as cnt FROM raw_data'))"
```

### **Dashboard không hiển thị sau migration**

```bash
# 1. Check backend logs
# 2. Check API response
curl http://localhost:5000/api/courses

# 3. Check browser console (F12)
# 4. Hard reload (Ctrl+Shift+R)
```

---

## 🔄 ROLLBACK

Nếu có vấn đề:

```bash
# 1. Stop V2 backend
Ctrl+C

# 2. Restore V1 code
cd backend
move app_v1_legacy.py app.py

# 3. Restart V1
python app.py

# 4. (Optional) Restore database
mysql -u root -p mooc_database < backup_before_v2.sql
```

---

## 📊 WHAT CHANGED?

| Component | Before | After |
|-----------|--------|-------|
| **Tables** | `raw_data` (1) | `student_features`, `predictions`, `training_data` (3) |
| **Backend** | `app.py` | `app_v2.py` → `app.py` |
| **Model Service** | `model_v4_service.py` | `model_v4_service_v2.py` → `model_v4_service.py` |
| **Query logic** | `FROM raw_data` | `FROM student_features JOIN predictions` |
| **Model selection** | Hardcode | Auto (from `model_registry`) |

---

## 🎯 NEXT STEPS (After Migration)

### **1. Update fetch script** (Optional - sau này)

Nếu muốn `fetch_mooc_h5p_data.py` INSERT trực tiếp vào `student_features`:

```python
# In fetch_mooc_h5p_data.py
# Change:
INSERT INTO raw_data (...)  # ← Old

# To:
INSERT INTO student_features (...)  # ← New
```

**Lưu ý:** V2 backend vẫn hoạt động dù fetch script chưa update (vì có fallback logic)

---

### **2. Train model mới cho NLTT**

```bash
# 1. Collect training data
python collect_training_data.py --course NLTT --semester 2025_S2

# 2. Train
python train_nltt_model.py

# 3. Register
INSERT INTO model_registry (model_name, ...) VALUES ('nltt_v1', ...);

# 4. Map
INSERT INTO course_model_mapping (course_id, model_name)
VALUES ('course-v1:UEL+NLTT...', 'nltt_v1');
```

---

### **3. Monitor predictions**

```sql
-- Daily: Check prediction freshness
SELECT 
    course_id,
    COUNT(*) as students,
    MAX(predicted_at) as last_prediction
FROM predictions
WHERE is_latest = TRUE
GROUP BY course_id;

-- Alert if predictions too old (>7 days)
```

---

## 🎉 DONE!

Sau khi chạy xong 5 bước:

✅ **Architecture chuẩn Production**
✅ **Auto model selection**
✅ **Predictions history**
✅ **Môn mới hiện instant**
✅ **Scalable & maintainable**

**Hệ thống đã lên đời từ Prototype → Production!** 🚀

---

## 📄 CHI TIẾT

Xem thêm:
- `REFACTOR_V2_GUIDE.md` - Full documentation
- `ARCHITECTURE_COMPARISON.md` - So sánh chi tiết V1 vs V2
- `database/schema_refactor_v2.sql` - Schema definition

**Questions?** Check documentation hoặc run:
```bash
python verify_v2_migration.py  # Verify status
```
