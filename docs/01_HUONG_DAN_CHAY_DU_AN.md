# 🚀 HƯỚNG DẪN CHẠY DỰ ÁN - DROPOUT PREDICTION SYSTEM

## 📋 Tổng Quan Hệ Thống

Hệ thống dự đoán nguy cơ bỏ học/rớt môn cho sinh viên trên nền tảng Open edX, bao gồm:

- **Frontend**: React + TypeScript Dashboard cho giảng viên
- **Backend**: Flask REST API
- **Database**: MySQL lưu trữ dữ liệu học tập
- **ML Model**: CatBoost classifier để dự đoán risk

---

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────┐      HTTP/REST      ┌─────────────────┐      SQL      ┌──────────────┐
│                 │  ←───────────────→  │                 │  ←─────────→  │              │
│   FRONTEND      │                     │    BACKEND      │               │   DATABASE   │
│  (React + TS)   │                     │  (Flask + API)  │               │    (MySQL)   │
│  Port: 5173     │                     │  Port: 5000     │               │  Port: 4000  │
└─────────────────┘                     └─────────────────┘               └──────────────┘
         │                                       │                                 │
         │                                       │                                 │
         └──────────────────────────────────────┴─────────────────────────────────┘
                                    ML Pipeline (Python)
                                    - Feature Engineering
                                    - Model Training
                                    - Predictions
```

---

## ⚙️ Yêu Cầu Hệ Thống

### 1. Phần Mềm Cần Cài

- **Python 3.8+**
- **Node.js 18+** và npm
- **MySQL 8.0+**
- **Git** (optional)

### 2. Python Packages

```bash
pip install flask flask-cors mysql-connector-python pandas numpy catboost scikit-learn
```

### 3. Node.js Packages

```bash
cd frontend
npm install
```

---

## 🗄️ BƯỚC 1: Setup Database

### 1.1. Tạo Database

```bash
# Kết nối MySQL
mysql -h localhost -P 4000 -u root -p

# Tạo database và user
CREATE DATABASE dropout_prediction_db;
CREATE USER 'dropout_user'@'localhost' IDENTIFIED BY 'dropout_pass_123';
GRANT ALL PRIVILEGES ON dropout_prediction_db.* TO 'dropout_user'@'localhost';
FLUSH PRIVILEGES;
```

### 1.2. Tạo Schema

```bash
cd database
mysql -h localhost -P 4000 -u dropout_user -p dropout_prediction_db < schema.sql
```

### 1.3. Kiểm Tra

```bash
mysql -h localhost -P 4000 -u dropout_user -p dropout_prediction_db

# Kiểm tra bảng đã tạo
SHOW TABLES;
# Phải thấy: enrollments, raw_data, h5p_scores, video_progress, mooc_grades, etc.
```

---

## 📥 BƯỚC 2: Thu Thập Dữ Liệu

### 2.1. Lấy Session ID từ MOOC

1. Đăng nhập vào MOOC: `https://mooc.vnuhcm.edu.vn`
2. Mở Developer Tools (F12)
3. Application → Cookies → Copy `sessionid`

### 2.2. Fetch Data từ APIs

```bash
cd database

# Fetch tất cả data cho một course
python fetch_mooc_h5p_data.py \
    --course-id "course-v1:DHQG-HCM+FM101+2025_S2" \
    --sessionid "YOUR_SESSION_ID_HERE" \
    --delay 0.5

# Hoặc chỉ aggregate từ data đã có
python fetch_mooc_h5p_data.py \
    --aggregate-only \
    --course-id "course-v1:DHQG-HCM+FM101+2025_S2"
```

**Quá trình:**
1. Fetch enrollments (danh sách học viên)
2. Fetch MOOC Export data (grades, progress, discussions)
3. Fetch H5P data cho từng user (scores, video progress)
4. Aggregate vào bảng `raw_data`

### 2.3. Kiểm Tra Dữ Liệu

```bash
mysql -h localhost -P 4000 -u dropout_user -p dropout_prediction_db

# Kiểm tra số lượng records
SELECT COUNT(*) FROM raw_data;
SELECT COUNT(*) FROM enrollments;
SELECT DISTINCT course_id FROM raw_data;
```

---

## 🤖 BƯỚC 3: Feature Engineering & Training Model

### 3.1. Tạo Features

```bash
# Tạo derived features từ raw_data
python ml/feature_engineering.py \
    --course-id "course-v1:DHQG-HCM+FM101+2025_S2" \
    --output data/features.csv
```

### 3.2. Train Model

```bash
# Train CatBoost model
python ml/train_model.py \
    --input data/features.csv \
    --model-name dropout_prediction_model \
    --iterations 1000 \
    --learning-rate 0.05
```

**Output:**
- Model: `models/dropout_prediction_model.cbm`
- Metadata: `models/dropout_prediction_model_metadata.pkl`
- Metrics: `models/dropout_prediction_model_metrics.pkl`

### 3.3. Đánh Giá Model (K-Fold CV)

```bash
# Chạy K-Fold Cross-Validation
python ml/kfold_evaluation.py \
    --input data/features.csv \
    --n-folds 10 \
    --save-models
```

**Output:** `results/kfold/kfold_results_*.json`

---

## 🔮 BƯỚC 4: Tạo Predictions

### 4.1. Predict cho Tất Cả Sinh Viên

```bash
python ml/predict.py \
    --input data/features.csv \
    --course-id "course-v1:DHQG-HCM+FM101+2025_S2" \
    --model-name dropout_prediction_model \
    --output data/predictions.csv \
    --save-db
```

**Output:**
- CSV: `data/predictions.csv`
- Database: `raw_data.fail_risk_score` được update

---

## 🌐 BƯỚC 5: Khởi Động Backend

### 5.1. Cài Đặt Dependencies

```bash
cd backend
pip install flask flask-cors mysql-connector-python pandas
```

### 5.2. Chạy Backend

```bash
python app.py
```

**Kiểm tra:**
```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/courses
```

**Backend sẽ chạy tại:** `http://localhost:5000`

---

## 🎨 BƯỚC 6: Khởi Động Frontend

### 6.1. Cài Đặt Dependencies

```bash
cd frontend
npm install
```

### 6.2. Tạo File .env

```bash
# Tạo file frontend/.env
echo "VITE_API_URL=http://localhost:5000" > frontend/.env
```

### 6.3. Chạy Frontend

```bash
npm run dev
```

**Frontend sẽ chạy tại:** `http://localhost:5173`

---

## ✅ BƯỚC 7: Kiểm Tra Toàn Bộ Hệ Thống

### 7.1. Kiểm Tra Database

```bash
mysql -h localhost -P 4000 -u dropout_user -p dropout_prediction_db

SELECT 
    COUNT(*) as total_students,
    AVG(fail_risk_score) as avg_risk,
    SUM(CASE WHEN fail_risk_score >= 70 THEN 1 ELSE 0 END) as high_risk
FROM raw_data;
```

### 7.2. Kiểm Tra Backend

```bash
# Health check
curl http://localhost:5000/api/health

# Get courses
curl http://localhost:5000/api/courses

# Get students
curl "http://localhost:5000/api/students/course-v1:DHQG-HCM+FM101+2025_S2?risk_level=HIGH"
```

### 7.3. Kiểm Tra Frontend

1. Mở browser: `http://localhost:5173`
2. Mở Developer Tools (F12) → Console
3. Kiểm tra không có lỗi
4. Kiểm tra Network tab → Xem API requests

---

## 🔄 QUY TRÌNH HÀNG NGÀY (Automation)

### Daily Predictions

```bash
# Chạy script tự động mỗi ngày
python scripts/daily_prediction.py
```

**Script sẽ:**
1. Fetch data mới từ APIs
2. Aggregate vào raw_data
3. Tạo predictions
4. Update database

### Model Retraining

```bash
# Retrain model khi có đủ dữ liệu mới
python scripts/retrain_model.py
```

---

## 🐛 Troubleshooting

### Lỗi: "Database connection failed"

**Nguyên nhân:** MySQL không chạy hoặc config sai

**Giải pháp:**
```bash
# Kiểm tra MySQL
mysql -h localhost -P 4000 -u dropout_user -p

# Kiểm tra config trong backend/app.py
DB_CONFIG = {
    "host": "localhost",
    "port": 4000,
    "database": "dropout_prediction_db",
    "user": "dropout_user",
    "password": "dropout_pass_123"
}
```

### Lỗi: "No courses found"

**Nguyên nhân:** Database chưa có dữ liệu

**Giải pháp:**
```bash
cd database
python fetch_mooc_h5p_data.py --aggregate-only --course-id "course-v1:..."
```

### Lỗi: "Network Error" trong frontend

**Nguyên nhân:** Backend không chạy hoặc URL sai

**Giải pháp:**
```bash
# 1. Kiểm tra backend đang chạy
curl http://localhost:5000/api/health

# 2. Kiểm tra .env
cat frontend/.env
# Phải có: VITE_API_URL=http://localhost:5000

# 3. Restart frontend
cd frontend
npm run dev
```

### Lỗi: "Module not found"

**Giải pháp:**
```bash
# Cài đặt lại dependencies
pip install -r requirements.txt  # Backend
cd frontend && npm install        # Frontend
```

---

## 📊 Checklist Hoàn Chỉnh

### Database
- [ ] MySQL đang chạy (port 4000)
- [ ] Database `dropout_prediction_db` đã tạo
- [ ] User `dropout_user` có quyền truy cập
- [ ] Schema đã chạy (`schema.sql`)
- [ ] Bảng `raw_data` có dữ liệu

### Data Collection
- [ ] Đã fetch enrollments
- [ ] Đã fetch MOOC Export data
- [ ] Đã fetch H5P data
- [ ] Đã aggregate vào `raw_data`

### ML Pipeline
- [ ] Đã tạo features (`features.csv`)
- [ ] Đã train model
- [ ] Đã tạo predictions
- [ ] Predictions đã lưu vào database

### Backend
- [ ] Flask app chạy trên port 5000
- [ ] CORS enabled
- [ ] Database connection thành công
- [ ] Tất cả endpoints hoạt động

### Frontend
- [ ] React app chạy trên port 5173
- [ ] `.env` file với `VITE_API_URL`
- [ ] Dashboard hiển thị thống kê
- [ ] Student list hiển thị danh sách
- [ ] Student detail hiển thị chi tiết

---

## 🎯 Quick Start (Tóm Tắt)

```bash
# 1. Setup database
mysql -h localhost -P 4000 -u root -p < database/schema.sql

# 2. Fetch data
cd database
python fetch_mooc_h5p_data.py --course-id "course-v1:..." --sessionid "..."

# 3. Train model
python ml/feature_engineering.py --output data/features.csv
python ml/train_model.py --input data/features.csv

# 4. Predict
python ml/predict.py --input data/features.csv --course-id "course-v1:..." --save-db

# 5. Start backend
cd backend
python app.py

# 6. Start frontend (terminal khác)
cd frontend
npm run dev

# 7. Open browser
# http://localhost:5173
```

---

## 📚 Tài Liệu Chi Tiết

- **Database**: Xem `02_DATABASE_COMPLETE.md`
- **API**: Xem `03_API_COMPLETE.md`
- **Frontend**: Xem `04_FRONTEND_COMPLETE.md`
- **Backend**: Xem `05_BACKEND_COMPLETE.md`
- **ML Model**: Xem `06_ML_MODEL_COMPLETE.md`

---

## 🎉 Hoàn Thành!

Nếu tất cả các bước trên đều OK, hệ thống đã sẵn sàng sử dụng!

**Các tính năng chính:**
- ✅ Dashboard tổng quan với thống kê
- ✅ Danh sách học viên với filter và sort
- ✅ Chi tiết học viên với gợi ý can thiệp
- ✅ Export danh sách ra CSV
- ✅ Risk level classification (HIGH/MEDIUM/LOW)
- ✅ Real-time data từ database

