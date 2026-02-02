# 🚀 HƯỚNG DẪN CHẠY MIGRATION V2 ĐẦY ĐỦ

## ✅ YÊU CẦU TRƯỚC KHI CHẠY

### **1. Docker MySQL đang chạy**

```bash
# Kiểm tra Docker đang chạy
docker ps

# Kết quả mong đợi:
# CONTAINER ID   IMAGE          PORTS                    NAMES
# ...            mysql:8.0      0.0.0.0:4000->3306/tcp   dropout_prediction_mysql
# ...            phpmyadmin     0.0.0.0:8081->80/tcp     dropout_prediction_phpmyadmin
```

**Nếu chưa chạy:**
```bash
cd d:\ProjectThesis\dropout_prediction
docker-compose up -d
```

**Đợi MySQL khởi động (30 giây):**
```bash
# Check health
docker-compose ps

# Hoặc xem logs
docker-compose logs mysql
```

---

### **2. File .env đã có**

```bash
# Kiểm tra
cat .env

# Nếu chưa có, copy từ example
copy .env.v2.example .env
```

**Nội dung .env phải match với docker-compose.yml:**
```env
DB_HOST=localhost
DB_PORT=4000              ← Port từ docker-compose
DB_NAME=dropout_prediction_db
DB_USER=dropout_user
DB_PASSWORD=dropout_pass_123
```

---

### **3. Python dependencies đã cài**

```bash
# Activate venv
cd d:\ProjectThesis\dropout_prediction
venv\Scripts\activate

# Cài dependencies
pip install mysql-connector-python python-dotenv pandas
```

---

## 🎯 CHẠY MIGRATION

### **Option 1: Quick Run (Windows)**

```cmd
run_migration_v2.bat
```

**Script sẽ:**
1. Hỏi có backup không (Y/N)
2. Chạy migration
3. Verify kết quả
4. Hiển thị summary

---

### **Option 2: Manual Steps**

#### **Step 1: Backup Database (Recommended)**

**Via mysqldump:**
```bash
mysqldump -h localhost -P 4000 -u dropout_user -pdropout_pass_123 dropout_prediction_db > backup_v1_%date%.sql
```

**Via phpMyAdmin:**
```
1. Mở: http://localhost:8081
2. Login: dropout_user / dropout_pass_123
3. Select database: dropout_prediction_db
4. Tab "Export" → Click "Go"
5. Save file
```

---

#### **Step 2: Run Migration**

```bash
cd d:\ProjectThesis\dropout_prediction

# Activate venv
venv\Scripts\activate

# Run migration
python database\migrate_to_v2.py
```

**Output mong đợi:**
```
================================================================================
🚀 DATABASE MIGRATION: raw_data → 3 Tables (V2)
================================================================================

STEP 1: CREATE NEW SCHEMA
   ✅ Executed: CREATE TABLE IF NOT EXISTS student_features...
   ✅ Executed: CREATE TABLE IF NOT EXISTS predictions...
   ✅ Executed: CREATE TABLE IF NOT EXISTS training_data...
   ✅ Executed: CREATE TABLE IF NOT EXISTS model_registry...
   ✅ Executed: CREATE TABLE IF NOT EXISTS course_model_mapping...
   ✅ Schema created successfully

STEP 2: MIGRATE DATA
📊 Total records in raw_data: 984

1️⃣  Migrating to student_features...
   ✅ Migrated 984 records to student_features

2️⃣  Migrating to predictions...
   ✅ Migrated 984 predictions

3️⃣  Migrating to training_data...
   ✅ Migrated 922 training records

   ✅ Data migration completed
      - Features: 984 records
      - Predictions: 984 records
      - Training: 922 records

STEP 4: CREATE VIEWS
   ✅ Created raw_data_view
   ✅ Created latest_predictions view

STEP 3: VERIFY MIGRATION
📊 Record counts:
   - raw_data (legacy):        984
   - student_features:         984
   - predictions:              984
   - training_data:            922

📚 Courses in student_features: 2
   - course-v1:DHQG-HCM+FM101+2025_S2: 922 students
   - course-v1:UEL+NLTT241225+2025_12: 62 students

🤖 Predictions by model:
   - fm101_v4: 984 predictions, avg risk = 50.00%

✅ Validation:
   ✅ student_features count OK (984 >= 984)
   ✅ predictions count OK (984 >= 984 raw_data with scores)

================================================================================
✅ MIGRATION COMPLETED SUCCESSFULLY!
================================================================================
```

---

#### **Step 3: Verify Migration**

```bash
python verify_v2_migration.py
```

**Output mong đợi:**
```
================================================================================
VERIFICATION: Schema V2 Migration
================================================================================

1. Checking tables exist...
   ✅ student_features
   ✅ predictions
   ✅ training_data
   ✅ model_registry
   ✅ course_model_mapping

2. Record counts:
   - raw_data          :    984 records
   - student_features  :    984 records
   - predictions       :    984 records
   - training_data     :    922 records

3. Courses in student_features:
   - course-v1:DHQG-HCM+FM101+2025_S2: 922 students
   - course-v1:UEL+NLTT241225+2025_12: 62 students

5. Model Registry:
   - fm101_v4 v4.0.0: ✅ ACTIVE (DEFAULT)

6. Course Model Mappings:
   ✅ course-v1:DHQG-HCM+FM101+2025_S2
      → Model: fm101_v4 (🤖 AUTO)
   ✅ course-v1:UEL+NLTT241225+2025_12
      → Model: fm101_v4 (🤖 AUTO)

================================================================================
✅ MIGRATION SUCCESSFUL!
================================================================================
```

---

#### **Step 4: Switch Backend Code**

```bash
cd backend

# Backup V1
move app.py app_v1_legacy.py
move model_v4_service.py model_v4_service_v1_legacy.py

# Activate V2
move app_v2.py app.py
move model_v4_service_v2.py model_v4_service.py

cd ..
```

---

#### **Step 5: Restart Backend**

```bash
# Stop backend cũ (nếu đang chạy)
# Terminal backend: Ctrl+C

# Start backend V2
python backend\app.py
```

**Output mong đợi:**
```
INFO - Model v4 loaded successfully from .\models\fm101_model_v4.cbm
INFO - Loaded model config from registry: fm101_v4 v4.0.0
INFO - Default Model V4 Service initialized successfully
 * Running on http://0.0.0.0:5000
```

---

#### **Step 6: Test API**

**Terminal mới:**
```bash
# Test health
curl http://localhost:5000/

# Test courses
curl http://localhost:5000/api/courses

# Test students
curl http://localhost:5000/api/students/course-v1:DHQG-HCM+FM101+2025_S2
```

**Kết quả mong đợi:**
```json
// GET /api/courses
{
  "courses": [
    {
      "course_id": "course-v1:DHQG-HCM+FM101+2025_S2",
      "student_count": 922
    },
    {
      "course_id": "course-v1:UEL+NLTT241225+2025_12",
      "student_count": 62
    }
  ],
  "total": 2
}
```

---

#### **Step 7: Test Dashboard**

```
1. Browser: http://localhost:5173
2. Hard reload: Ctrl+Shift+R
3. Click "Chọn khóa học" dropdown
4. Verify: Thấy 2 courses
5. Click course → Verify: Students hiển thị với risk scores
6. Click student → Verify: Detail modal hiển thị
7. F12 Console → Verify: No errors
```

---

## 🔍 KIỂM TRA DATABASE BẰNG PHPMYADMIN

### **Access phpMyAdmin:**

```
URL: http://localhost:8081
User: dropout_user
Password: dropout_pass_123
```

### **Verify tables:**

```sql
-- 1. Check tables exist
SHOW TABLES;

-- Should see:
-- student_features
-- predictions
-- training_data
-- model_registry
-- course_model_mapping
-- raw_data (legacy)

-- 2. Check student_features
SELECT COUNT(*) FROM student_features;
-- Expected: 984

-- 3. Check predictions
SELECT 
    model_name, 
    COUNT(*) as total, 
    AVG(fail_risk_score) as avg_risk
FROM predictions
GROUP BY model_name;
-- Expected: fm101_v4, 984, ~50.00

-- 4. Check model_registry
SELECT * FROM model_registry;
-- Expected: 1 row (fm101_v4)

-- 5. Check course mappings
SELECT * FROM course_model_mapping;
-- Expected: 2 rows (FM101, NLTT)
```

---

## ❌ TROUBLESHOOTING

### **Error: "Can't connect to MySQL server"**

**Nguyên nhân:** Docker MySQL chưa chạy hoặc port sai

**Fix:**
```bash
# Check Docker
docker ps | findstr mysql

# Nếu không thấy, start Docker
docker-compose up -d

# Đợi 30 giây cho MySQL khởi động
timeout /t 30

# Test connection
mysql -h localhost -P 4000 -u dropout_user -pdropout_pass_123 -e "SELECT 1"
```

---

### **Error: "Access denied for user"**

**Nguyên nhân:** Username/password sai hoặc .env không đúng

**Fix:**
```bash
# Check .env file
type .env

# Verify docker-compose config
type docker-compose.yml | findstr MYSQL

# Should match:
# DB_USER=dropout_user
# DB_PASSWORD=dropout_pass_123
```

---

### **Error: "Database 'mooc_database' doesn't exist"**

**Nguyên nhân:** Database name trong script khác với docker-compose

**Fix:** Already fixed! Script giờ dùng `dropout_prediction_db`

---

### **Error: "Table 'raw_data' doesn't exist"**

**Nguyên nhân:** Database mới, chưa có data

**Fix:**
```bash
# Option 1: Import schema cũ trước
mysql -h localhost -P 4000 -u dropout_user -pdropout_pass_123 dropout_prediction_db < database/schema.sql

# Option 2: Fetch data mới
python database/fetch_mooc_h5p_data.py --course-id "..." --sessionid "..."
```

---

### **Migration chạy nhưng count = 0**

**Nguyên nhân:** raw_data table empty

**Verify:**
```bash
python -c "from backend.db import fetch_one; print(fetch_one('SELECT COUNT(*) FROM raw_data'))"
```

**Fix:** Cần có data trong raw_data trước. Nếu chưa có:
```bash
# Aggregate existing data
python aggregate_course.py
```

---

## 📋 CHECKLIST ĐẦY ĐỦ

### **Pre-migration:**
- [ ] Docker Desktop đang chạy
- [ ] `docker-compose up -d` đã chạy
- [ ] MySQL container healthy (`docker-compose ps`)
- [ ] File `.env` đã tạo và config đúng
- [ ] Python venv activated
- [ ] Dependencies installed (`mysql-connector-python`, `python-dotenv`)
- [ ] Có data trong `raw_data` table (nếu không, chạy fetch/aggregate trước)

### **Migration:**
- [ ] Backup database (recommended)
- [ ] Run `python database/migrate_to_v2.py`
- [ ] Check output không có errors
- [ ] All 5 tables created
- [ ] Data migrated (counts match)

### **Post-migration:**
- [ ] Run `python verify_v2_migration.py`
- [ ] Verify: All checks pass ✅
- [ ] Switch backend code (V1 → V2)
- [ ] Restart backend
- [ ] Test API endpoints (curl)
- [ ] Test dashboard (browser)
- [ ] Check logs no errors
- [ ] Monitor 24h

---

## 🎯 TOÀN BỘ LỆNH CẦN CHẠY

```bash
# ============================================================================
# FULL MIGRATION COMMANDS
# ============================================================================

# 1. Đảm bảo Docker đang chạy
cd d:\ProjectThesis\dropout_prediction
docker-compose up -d
timeout /t 30

# 2. Activate Python venv
venv\Scripts\activate

# 3. Backup database
mysqldump -h localhost -P 4000 -u dropout_user -pdropout_pass_123 dropout_prediction_db > backup_v1.sql

# 4. Run migration
python database\migrate_to_v2.py

# 5. Verify
python verify_v2_migration.py

# 6. Switch code
cd backend
move app.py app_v1_legacy.py
move model_v4_service.py model_v4_service_v1_legacy.py
move app_v2.py app.py
move model_v4_service_v2.py model_v4_service.py
cd ..

# 7. Restart backend (in terminal backend)
# Ctrl+C (stop old)
python backend\app.py

# 8. Test API (terminal mới)
curl http://localhost:5000/
curl http://localhost:5000/api/courses

# 9. Test dashboard
# Browser: http://localhost:5173
# Ctrl+Shift+R

# ============================================================================
# DONE! ✅
# ============================================================================
```

**Copy & paste từng block, chạy tuần tự!**

---

## 📊 DATABASE INFO

### **Docker-compose Config:**

```yaml
mysql:
  ports: "4000:3306"           # Host port 4000 → Container port 3306
  environment:
    MYSQL_DATABASE: dropout_prediction_db
    MYSQL_USER: dropout_user
    MYSQL_PASSWORD: dropout_pass_123
```

### **Connection String:**

```
Host: localhost
Port: 4000
Database: dropout_prediction_db
User: dropout_user
Password: dropout_pass_123
```

### **phpMyAdmin Access:**

```
URL: http://localhost:8081
Login: dropout_user / dropout_pass_123
```

---

## 🎉 SUCCESS INDICATORS

Migration thành công khi thấy:

```
✅ MIGRATION COMPLETED SUCCESSFULLY!
   📊 Summary:
   - student_features:  984 records
   - predictions:       984 records
   - training_data:     922 records

✅ MIGRATION SUCCESSFUL! (từ verify script)

✅ Backend starts: "Default Model V4 Service initialized successfully"

✅ API works: curl returns JSON với 2 courses

✅ Dashboard works: Hiển thị students và risk scores
```

---

## 🔄 ROLLBACK (Nếu cần)

```bash
# 1. Stop V2 backend
Ctrl+C

# 2. Restore V1 code
cd backend
move app_v1_legacy.py app.py
move model_v4_service_v1_legacy.py model_v4_service.py
cd ..

# 3. Restart V1
python backend\app.py

# 4. (Optional) Restore database
mysql -h localhost -P 4000 -u dropout_user -pdropout_pass_123 dropout_prediction_db < backup_v1.sql
```

---

## 📞 NEED HELP?

### **Check Docker:**
```bash
docker-compose ps
docker-compose logs mysql
```

### **Check Database:**
```bash
mysql -h localhost -P 4000 -u dropout_user -pdropout_pass_123 dropout_prediction_db -e "SHOW TABLES"
```

### **Check .env:**
```bash
type .env
```

### **Test connection:**
```bash
python -c "from backend.db import get_db_connection; conn = get_db_connection(); print('✅ Connected!' if conn else '❌ Failed')"
```

---

## 🚀 READY TO START?

**Chạy ngay:**
```cmd
run_migration_v2.bat
```

**Hoặc manual:**
```bash
docker-compose up -d
python database\migrate_to_v2.py
python verify_v2_migration.py
```

**Good luck!** 🎯
