# ⭐ START HERE - MIGRATION V2

## 🎯 BẠN CẦN BIẾT

Tôi đã refactor toàn bộ hệ thống từ **V1** (1 table lẫn lộn) → **V2** (3 tables tách biệt)

**Vấn đề bạn phát hiện:**
> "raw_data vừa để training, vừa để production, có kỳ không?"

**→ ĐÚNG! Đó là anti-pattern. Tôi đã FIX!**

---

## ✅ ĐÃ TẠO CHO BẠN

### **📦 15 files:**
- 5 files code backend (refactored)
- 3 scripts migration/verify
- 7 files documentation

### **🏗️ Architecture mới:**
```
V1: raw_data (1 table lẫn lộn) ❌

V2: 3 tables tách biệt ✅
    ├─ student_features (production features)
    ├─ predictions (model outputs + history)
    └─ training_data (historical labeled data)
```

---

## 🚀 BẠN CẦN LÀM GÌ?

### **⚡ CÁCH NHANH NHẤT (15 phút):**

```bash
# 1. Đảm bảo Docker chạy
cd d:\ProjectThesis\dropout_prediction
docker-compose up -d

# 2. Chạy migration
run_migration_v2.bat

# 3. Follow instructions trong script
```

**→ XONG!**

---

### **📚 HOẶC ĐỌC TRƯỚC (25 phút):**

**Đọc theo thứ tự:**
```
1. REFACTOR_V2_SUMMARY.md         (5 phút) ← Hiểu V2 là gì
2. RUN_MIGRATION_V2_GUIDE.md      (5 phút) ← Cách chạy chi tiết
3. Chạy migration                 (15 phút)
```

---

## 🎯 QUICK COMMANDS

```bash
# START: Vào folder project
cd d:\ProjectThesis\dropout_prediction

# STEP 1: Docker up
docker-compose up -d
timeout /t 30

# STEP 2: Activate venv
venv\Scripts\activate

# STEP 3: Run migration
run_migration_v2.bat

# (Follow prompts, chọn Y để backup)

# STEP 4: Verify
python verify_v2_migration.py

# STEP 5: Switch code
cd backend
move app.py app_v1_legacy.py
move app_v2.py app.py
move model_v4_service.py model_v4_service_v1_legacy.py  
move model_v4_service_v2.py model_v4_service.py
cd ..

# STEP 6: Restart backend
# (Terminal backend: Ctrl+C)
python backend\app.py

# STEP 7: Test
curl http://localhost:5000/api/courses

# STEP 8: Open dashboard
# Browser: http://localhost:5173
# Ctrl+Shift+R
```

---

## ✅ CHECKLIST

- [ ] Docker Desktop đang chạy
- [ ] `docker-compose up -d` đã chạy
- [ ] MySQL container healthy
- [ ] File `.env` đã có (với thông tin đúng)
- [ ] Backup database (recommended)
- [ ] Run migration script
- [ ] Verify thành công
- [ ] Switch code V1 → V2
- [ ] Restart backend
- [ ] Test API
- [ ] Test dashboard

---

## 📖 DOCS

| File | Dùng khi nào |
|------|--------------|
| **START_HERE_V2.md** | ⭐ **Bạn đang đọc** |
| `REFACTOR_V2_SUMMARY.md` | Muốn hiểu tổng quan V2 |
| `RUN_MIGRATION_V2_GUIDE.md` | Cần hướng dẫn chi tiết |
| `MIGRATION_V2_QUICKSTART.md` | Quick reference |
| `REFACTOR_V2_GUIDE.md` | Full documentation |

---

## ⚠️ LƯU Ý

### **Docker-compose config:**
```
Port: 4000 (không phải 3306!)
Database: dropout_prediction_db (không phải mooc_database!)
User: dropout_user (không phải root!)
```

**→ Tôi đã update tất cả scripts cho khớp với config này!**

---

### **raw_data vẫn còn:**

Migration **KHÔNG XÓA** `raw_data` (giữ as backup)

Sau 1-2 tuần verify V2 stable:
```sql
-- phpMyAdmin hoặc MySQL CLI
RENAME TABLE raw_data TO raw_data_legacy_backup_20260129;
```

---

## 🎉 SAU KHI MIGRATE

### **Lợi ích ngay lập tức:**

✅ **Môn mới hiện instant** (không đợi predict)
✅ **Auto-select model** (config từ database)
✅ **Predictions history** (track changes)
✅ **Production-ready** (follow best practices)

### **Workflow mới:**

```
Thêm môn học mới:
1. Fetch data → student_features created
2. ✅ Dashboard NGAY LẬP TỨC hiện môn!
3. Click student → Auto predict on-demand
4. Done!

Timeline: Instant (không đợi 30-60 phút như trước)
```

---

## 🚦 BẮT ĐẦU NGAY

**Copy & paste commands này:**

```bash
cd d:\ProjectThesis\dropout_prediction
docker-compose up -d
timeout /t 30
venv\Scripts\activate
run_migration_v2.bat
```

**Hoặc đọc trước:**
```
→ REFACTOR_V2_SUMMARY.md (5 phút)
→ RUN_MIGRATION_V2_GUIDE.md (5 phút)
```

---

## 📞 CẦN GIÚP?

- **Error?** → Xem `RUN_MIGRATION_V2_GUIDE.md` → Troubleshooting
- **Muốn hiểu thêm?** → Đọc `REFACTOR_V2_SUMMARY.md`
- **Rollback?** → Xem `RUN_MIGRATION_V2_GUIDE.md` → Rollback section

---

**Sẵn sàng chạy migration?** 🚀

```cmd
run_migration_v2.bat
```
