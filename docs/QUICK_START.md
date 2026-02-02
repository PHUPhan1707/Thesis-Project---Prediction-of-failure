# ⚡ QUICK START GUIDE

Hướng dẫn nhanh để chạy toàn bộ hệ thống Teacher Dashboard.

---

## 🔥 Start trong 3 bước:

### Bước 1: Start Backend
```bash
# Terminal 1
cd D:\ProjectThesis\dropout_prediction
venv\Scripts\activate
python -m backend.app
```
✅ Backend chạy tại: `http://localhost:5000`

### Bước 2: Start Frontend
```bash
# Terminal 2 (mở terminal mới)
cd D:\ProjectThesis\dropout_prediction\frontend
npm run dev
```
✅ Frontend chạy tại: `http://localhost:5173`

### Bước 3: Open Browser
```
http://localhost:5173
```

🎉 **DONE!** Dashboard đã sẵn sàng!

---

## 🧪 Quick Test:

### Test Backend:
```bash
curl http://localhost:5000/api/health
```
Expected: `{"status":"ok",...}`

### Test Frontend:
Mở browser → `http://localhost:5173` → Xem danh sách sinh viên có tên

---

## 📊 System Status:

| Component | Status | Port | Notes |
|-----------|--------|------|-------|
| MySQL | ✅ Running | 4000 | dropout_prediction_db |
| Backend | ✅ Ready | 5000 | Flask API |
| Frontend | ✅ Ready | 5173 | React + Vite |
| Model V4 | ✅ Loaded | - | AUC=0.9759 |

---

## 🔍 Troubleshooting:

### Backend không start:
```bash
# Check Python packages
pip install flask flask-cors mysql-connector-python pandas catboost

# Check database connection
mysql -h localhost -P 4000 -u dropout_user -p
```

### Frontend không start:
```bash
# Reinstall dependencies
cd frontend
npm install

# Clear cache
npm run build
```

### Student names = null:
```bash
# Run diagnostic
python test_query_names.py
```

---

## 📚 Tài liệu chi tiết:

- 📖 `01_HUONG_DAN_CHAY_DU_AN.md` - Hướng dẫn tổng quan
- 📖 `TEST_BACKEND.md` - Test API endpoints
- 📖 `BACKEND_REBUILD_SUMMARY.md` - Backend rebuild summary
- 📖 `test_model_v4.py` - Test model v4
- 📖 `test_query_names.py` - Test database queries

---

## 🎯 Features Available:

- ✅ Xem danh sách sinh viên theo khóa học
- ✅ Filter theo risk level (HIGH/MEDIUM/LOW)
- ✅ Sắp xếp theo risk score, tên, điểm, last activity
- ✅ Xem chi tiết sinh viên
- ✅ Gợi ý can thiệp tự động
- ✅ Thống kê tổng quan khóa học
- ✅ Ghi nhận hành động can thiệp
- ✅ Dự đoán risk với Model V4

**Chúc mừng! Hệ thống đã sẵn sàng! 🚀**

