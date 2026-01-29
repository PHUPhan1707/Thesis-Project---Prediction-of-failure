# 📚 TÀI LIỆU TỔNG HỢP - DROPOUT PREDICTION SYSTEM

## 🎯 Giới Thiệu

Hệ thống dự đoán nguy cơ bỏ học/rớt môn cho sinh viên trên nền tảng Open edX, bao gồm:
- **Frontend**: React + TypeScript Dashboard
- **Backend**: Flask REST API
- **Database**: MySQL
- **ML Model**: CatBoost Classifier

---

## 📖 Tài Liệu Theo Mảng

### 1. 🚀 Hướng Dẫn Chạy Dự Án
**File:** `01_HUONG_DAN_CHAY_DU_AN.md`

**Nội dung:**
- Setup database
- Thu thập dữ liệu
- Feature engineering & training
- Khởi động backend & frontend
- Troubleshooting

**👉 Bắt đầu từ đây nếu bạn mới!**

---

### 2. 📊 Database
**File:** `02_DATABASE_COMPLETE.md`

**Nội dung:**
- Schema & ERD
- Thu thập dữ liệu từ APIs
- API Data Mapping
- Migrations
- Queries thường dùng

**👉 Xem khi cần hiểu về database structure**

---

### 3. 🔌 API
**File:** `03_API_COMPLETE.md`

**Nội dung:**
- Backend REST API endpoints
- MOOC APIs
- H5P APIs
- API Requirements (future)
- Authentication & Testing

**👉 Xem khi cần hiểu về API integration**

---

### 4. 🎨 Frontend
**File:** `04_FRONTEND_COMPLETE.md`

**Nội dung:**
- Setup & Installation
- Project Structure
- Components & Pages
- API Integration
- Deployment

**👉 Xem khi cần hiểu về frontend**

---

### 5. ⚙️ Backend
**File:** `05_BACKEND_COMPLETE.md`

**Nội dung:**
- API Endpoints
- Database Integration
- Error Handling
- Deployment
- Helper Functions

**👉 Xem khi cần hiểu về backend**

---

### 6. 🤖 ML Model
**File:** `06_ML_MODEL_COMPLETE.md`

**Nội dung:**
- Feature Engineering
- Model Training
- K-Fold Evaluation
- Prediction
- Model Performance

**👉 Xem khi cần hiểu về ML pipeline**

---

## 🗺️ Sơ Đồ Hệ Thống

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

## 🚀 Quick Start

### 1. Setup Database
```bash
mysql -h localhost -P 4000 -u root -p < database/schema.sql
```

### 2. Fetch Data
```bash
cd database
python fetch_mooc_h5p_data.py --course-id "course-v1:..." --sessionid "..."
```

### 3. Train Model
```bash
python ml/feature_engineering.py --output data/features.csv
python ml/train_model.py --input data/features.csv
```

### 4. Start Backend
```bash
cd backend
python app.py
```

### 5. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

**👉 Xem chi tiết:** `01_HUONG_DAN_CHAY_DU_AN.md`

---

## 📁 Cấu Trúc Project

```
dropout_prediction/
├── 01_HUONG_DAN_CHAY_DU_AN.md      # ⭐ Bắt đầu từ đây
├── 02_DATABASE_COMPLETE.md         # Database
├── 03_API_COMPLETE.md              # API
├── 04_FRONTEND_COMPLETE.md         # Frontend
├── 05_BACKEND_COMPLETE.md          # Backend
├── 06_ML_MODEL_COMPLETE.md         # ML Model
├── README_TONG_HOP.md              # File này
│
├── database/                        # Database & Data Collection
│   ├── schema.sql
│   ├── fetch_mooc_h5p_data.py
│   └── migrations/
│
├── ml/                              # ML Pipeline
│   ├── feature_engineering.py
│   ├── train_model.py
│   ├── predict.py
│   └── kfold_evaluation.py
│
├── backend/                         # Backend API
│   └── app.py
│
├── frontend/                        # Frontend Dashboard
│   └── src/
│
└── models/                          # Trained Models
```

---

## 🎯 Workflow

### Development Workflow

1. **Data Collection** → `database/fetch_mooc_h5p_data.py`
2. **Feature Engineering** → `ml/feature_engineering.py`
3. **Model Training** → `ml/train_model.py`
4. **Prediction** → `ml/predict.py`
5. **Backend API** → `backend/app.py`
6. **Frontend Dashboard** → `frontend/`

### Daily Workflow

1. **Fetch new data** → Update database
2. **Generate predictions** → Update risk scores
3. **View dashboard** → Check at-risk students
4. **Interventions** → Record actions

---

## 📊 Model Performance

### Current Model (V4)

- **Precision:** 86.79%
- **Recall:** 83.64%
- **F1-Score:** 85.19%
- **AUC-ROC:** ~0.85

**Risk Distribution:**
- HIGH: 235 students (25.5%)
- MEDIUM: 60 students (6.5%)
- LOW: 626 students (68.0%)

---

## 🔗 Liên Kết Nhanh

### Setup & Installation
- [Hướng Dẫn Chạy Dự Án](01_HUONG_DAN_CHAY_DU_AN.md)

### Database
- [Database Complete](02_DATABASE_COMPLETE.md)
- [Schema SQL](database/schema.sql)
- [Fetch Data Guide](database/GIAI_THICH_FETCH_DATA.md)

### API
- [API Complete](03_API_COMPLETE.md)
- [Backend API](backend/app.py)
- [API Requirements](API_REQUIREMENTS_SUMMARY.md)

### Frontend
- [Frontend Complete](04_FRONTEND_COMPLETE.md)
- [Frontend README](frontend/README.md)
- [Connection Guide](FRONTEND_BACKEND_CONNECTION_GUIDE.md)

### Backend
- [Backend Complete](05_BACKEND_COMPLETE.md)
- [Backend Code](backend/app.py)

### ML Model
- [ML Model Complete](06_ML_MODEL_COMPLETE.md)
- [K-Fold Guide](KFOLD_CV_GUIDE.md)
- [Prediction Results](PREDICTION_RESULTS.md)

---

## 🆘 Troubleshooting

### Database Issues
👉 Xem: `02_DATABASE_COMPLETE.md` → Troubleshooting

### API Issues
👉 Xem: `03_API_COMPLETE.md` → Testing

### Frontend Issues
👉 Xem: `04_FRONTEND_COMPLETE.md` → Troubleshooting

### Backend Issues
👉 Xem: `05_BACKEND_COMPLETE.md` → Troubleshooting

### ML Issues
👉 Xem: `06_ML_MODEL_COMPLETE.md` → Testing

---

## 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. File tài liệu tương ứng (theo mảng)
2. Code comments trong source files
3. Log files trong `logs/`

---

## ✅ Checklist

### Setup
- [ ] Database đã tạo và có schema
- [ ] Đã fetch data từ APIs
- [ ] Model đã được train
- [ ] Backend đang chạy
- [ ] Frontend đang chạy

### Development
- [ ] Đã đọc tài liệu tương ứng
- [ ] Đã hiểu workflow
- [ ] Đã test các chức năng

---

## 🎉 Hoàn Thành!

Bạn đã có đầy đủ tài liệu để:
- ✅ Hiểu toàn bộ hệ thống
- ✅ Setup và chạy dự án
- ✅ Phát triển tính năng mới
- ✅ Troubleshoot các vấn đề

**Chúc bạn thành công! 🚀**

