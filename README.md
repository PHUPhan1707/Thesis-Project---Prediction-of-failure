# 🎓 Dropout Prediction System

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![React](https://img.shields.io/badge/React-19.2.0-61dafb.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9+-3178c6.svg)
![Flask](https://img.shields.io/badge/Flask-Latest-black.svg)
![CatBoost](https://img.shields.io/badge/CatBoost-1.2.5-yellow.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479a1.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Hệ thống phân tích dữ liệu và dự đoán nguy cơ học vụ cho giảng viên trên nền tảng Open edX - Teacher Dashboard with AI-powered student risk analytics.

---

## 📋 Table of Contents

- [Recent Updates](#-recent-updates-feb-2026)
- [Key Features](#-key-features)
- [Tech Stack](#️-tech-stack)
- [System Architecture](#️-system-architecture)
- [Performance Metrics](#-performance-metrics)
- [Quick Start](#-quick-start)
- [API Endpoints](#-api-endpoints)
- [UI Components](#-ui-components)
- [Development](#-development)
- [Documentation](#-documentation)
- [Troubleshooting](#-troubleshooting)

## 🔗 Quick Links

- 📖 [Hướng dẫn chạy dự án](docs/01_HUONG_DAN_CHAY_DU_AN.md)
- 🗄️ [Database Schema](database/ERD_DIAGRAM.md)
- 🎨 [UX Improvements Guide](docs/UX_IMPROVEMENTS_LOADING_SKELETON_DARK_MODE.md)
- 🧪 [Testing Strategy](docs/) (Coming soon)
- 🚀 [Deployment Guide](docs/) (Coming soon)

---

## 🆕 Recent Updates (Feb 2026)

### v2.1.0 - UX & Navigation Improvements

- ✅ **Loading Skeleton System**: 8 variants với shimmer animation cho smooth loading experience
- ✅ **Dark Mode**: Full theme switching với localStorage persistence và system preference detection
- ✅ **CSS Variables Architecture**: 20+ variables cho maintainable theming
- ✅ **Smart Course Navigation**: Auto-redirect về dashboard khi đổi môn học từ student detail page
- ✅ **Header Layout Fix**: Tối ưu spacing và integration của theme toggle

**Tech Highlights**: React Context API, CSS custom properties, React Router navigation guards

## ✨ Key Features

### 🤖 Machine Learning

- **ML Model**: CatBoost 1.2.5 classifier với độ chính xác cao
- **Feature Engineering**: 80+ engineered features từ dữ liệu thô
- **Risk Classification**: HIGH/MEDIUM/LOW risk levels với confidence score
- **SHAP Explainability**: Giải thích từng dự đoán với SHAP values
- **Auto Retraining**: Tự động cập nhật model định kỳ

### 📊 Analytics Dashboard

- **Course Overview**: Thống kê tổng quan theo môn học
- **Student List**: Danh sách sinh viên với risk scores
- **Risk Distribution**: Biểu đồ phân bố rủi ro
- **H5P Analytics**: Phân tích chi tiết tương tác H5P
- **Real-time Filtering**: Lọc, tìm kiếm, sắp xếp theo nhiều tiêu chí

### 🎨 UX/UI Improvements

- **Loading Skeleton**: 8 variants với shimmer animation cho better UX
- **Dark Mode**: Theme switching với localStorage persistence
- **Responsive Design**: Tối ưu cho mọi kích thước màn hình
- **Smart Navigation**: Auto-redirect khi đổi môn học tránh 404 errors
- **CSS Variables**: Hệ thống theme linh hoạt với 20+ biến

### 🔧 System Features

- **Intervention Suggestions**: Gợi ý can thiệp tự động dựa trên risk factors
- **Daily Automation**: Predictions và data sync tự động
- **RESTful API**: Backend API đầy đủ với error handling
- **Database Migrations**: Version control cho schema changes

## 🛠️ Tech Stack

### Frontend

- **Framework**: React 19.2.0 + TypeScript
- **Build Tool**: Vite 7.2.4
- **Routing**: React Router 7.12.0
- **Charts**: Recharts 3.7.0
- **Icons**: Lucide React 0.562.0
- **HTTP Client**: Axios 1.13.2

### Backend

- **Framework**: Flask (Python 3.9+)
- **API**: RESTful with Blueprint architecture
- **Database**: MySQL 8.0 (Docker)
- **ORM**: mysql-connector-python

### Machine Learning

- **Model**: CatBoost 1.2.5
- **Explainability**: SHAP
- **Data Processing**: pandas, numpy
- **Validation**: scikit-learn

### DevOps

- **Containerization**: Docker Compose
- **Database Admin**: phpMyAdmin
- **Version Control**: Git

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  React + TypeScript + Vite (http://localhost:5173)         │
│  - Dashboard UI                                             │
│  - Loading Skeletons                                        │
│  - Dark Mode Theme                                          │
│  - React Router                                             │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API (HTTP/JSON)
┌────────────────────▼────────────────────────────────────────┐
│                        Backend Layer                         │
│  Flask API Server (http://localhost:5000)                   │
│  - Route Blueprints                                         │
│  - ML Inference Service                                     │
│  - SHAP Explainability                                      │
└────────────────────┬────────────────────────────────────────┘
                     │ SQL Queries
┌────────────────────▼────────────────────────────────────────┐
│                        Data Layer                            │
│  MySQL 8.0 (Docker port 4000)                               │
│  - student_features (80+ columns)                           │
│  - student_predictions_v2                                   │
│  - course_info, h5p_interactions                            │
└──────────────────────────────────────────────────────────────┘
```

## ⚡ Performance Metrics

- **Page Load**: < 2s (with skeleton loading)
- **API Response**: < 500ms (average)
- **Model Inference**: < 100ms per student
- **Feature Engineering**: ~50ms per student
- **Dark Mode Toggle**: Instant (CSS variables)
- **Theme Persistence**: localStorage (no flicker)

## 📁 Project Structure

```
dropout_prediction/
├── frontend/                   # React TypeScript frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   │   ├── Dashboard/     # Dashboard specific components
│   │   │   ├── LoadingSkeleton.tsx  # 8 skeleton variants
│   │   │   └── ThemeToggle.tsx      # Dark mode toggle
│   │   ├── context/           # React Context providers
│   │   │   ├── DashboardContext.tsx
│   │   │   └── ThemeContext.tsx
│   │   ├── pages/             # Page components
│   │   ├── layout/            # Layout components
│   │   ├── services/          # API services
│   │   └── types/             # TypeScript types
│   └── package.json
│
├── backend/                    # Flask backend
│   ├── app.py                 # Main application entry
│   ├── db.py                  # Database connection
│   ├── inference_service.py   # ML inference service (DataFetcher, FeaturePreparator, RiskPredictor)
│   ├── model_v4_service.py    # [shim] backward-compat re-export → inference_service.py
│   ├── routes/                # API route blueprints
│   └── utils/                 # Helper functions
│
├── database/                   # Data layer
│   ├── schema.sql             # Database schema
│   ├── migrations/            # Schema version control
│   ├── fetch_mooc_h5p_data.py # Data collector
│   └── ERD_DIAGRAM.md         # Database design
│
├── ml/                         # ML pipeline
│   ├── feature_engineering.py # Feature creation
│   ├── train_model.py         # Model training
│   └── predict.py             # Inference
│
├── models/                     # Trained models (.cbm)
├── data/                       # Features & predictions
├── scripts/                    # Automation scripts
├── docs/                       # Documentation
└── docker-compose.yml          # Docker setup
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- MySQL 8.0
- Docker & Docker Compose (optional)

### Installation

#### 1. Clone Repository

```bash
git clone <repository-url>
cd dropout_prediction
```

#### 2. Setup Database

```bash
# Option A: Using Docker (Recommended)
docker-compose up -d

# Option B: Manual MySQL setup
mysql -u root -p < database/schema.sql
```

#### 3. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure database connection
# Edit backend/db.py with your MySQL credentials

# Run backend server
cd backend
python app.py
# Server runs on http://localhost:5000
```

#### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Frontend runs on http://localhost:5173
```

### First Time Setup

#### Collect Data

```bash
cd database
python fetch_mooc_h5p_data.py --course-id "course-v1:DHQG-HCM+FM101+2025_S2"
```

#### Train Model

```bash
# Generate features
python populate_student_features.py

# Train model
cd ml
python train_model.py --input ../data/features_v5.csv

# Make predictions
python run_prediction_nltt.py
```

## 📡 API Endpoints

### Courses

- `GET /api/courses` - Lấy danh sách khóa học
- `GET /api/courses/<course_id>/statistics` - Thống kê khóa học

### Students

- `GET /api/courses/<course_id>/students` - Danh sách sinh viên
- `GET /api/students/<user_id>/detail` - Chi tiết sinh viên
- `GET /api/students/<user_id>/shap` - SHAP explanation

### H5P Analytics

- `GET /api/courses/<course_id>/h5p/overview` - Tổng quan H5P
- `GET /api/students/<user_id>/h5p/interactions` - Tương tác H5P

### Dashboard

- `GET /api/dashboard/summary` - Tổng quan dashboard

📖 **Full API Documentation**: See `docs/03_API_COMPLETE.md`

## 🎨 UI Components

### Loading Skeletons

- `Skeleton` - Base skeleton component
- `CardSkeleton` - Generic card loading
- `StatsCardSkeleton` - Statistics card loading
- `StudentListSkeleton` - Student table loading
- `ChartSkeleton` - Chart placeholder
- `TableSkeleton` - Data table loading
- `DashboardSkeleton` - Full dashboard loading
- `StudentDetailSkeleton` - Student detail page loading
- `H5PAnalyticsSkeleton` - H5P analytics loading

### Theme System

- **Light Mode**: Default clean white theme
- **Dark Mode**: Eye-friendly dark theme with reduced contrast
- **Auto Detection**: System preference detection
- **Persistence**: localStorage for user preference
- **Smooth Transitions**: 0.3s ease transitions between themes

## 🔧 Development

### Run Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Run Frontend Tests

```bash
cd frontend
npm run test
```

### Build for Production

```bash
# Frontend
cd frontend
npm run build

# Backend (using gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

### Database Migrations

```bash
cd database
python run_migration_08.py
```

## 📚 Documentation

- `docs/01_HUONG_DAN_CHAY_DU_AN.md` - Complete project guide
- `docs/02_DATABASE_COMPLETE.md` - Database architecture
- `docs/03_API_COMPLETE.md` - API documentation
- `docs/04_FRONTEND_COMPLETE.md` - Frontend structure
- `docs/05_BACKEND_COMPLETE.md` - Backend architecture
- `docs/06_ML_MODEL_COMPLETE.md` - ML pipeline guide
- `docs/UX_IMPROVEMENTS_LOADING_SKELETON_DARK_MODE.md` - UX features

## 🐛 Troubleshooting

### Frontend won't start

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend connection error

- Check MySQL is running: `docker ps` or `systemctl status mysql`
- Verify credentials in `backend/db.py`
- Check port 4000 is not in use

### Model prediction error

- Ensure model file exists: `models/catboost_model_v5.cbm`
- Check feature names match training data
- Verify all required features are populated

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Open Pull Request

## � Screenshots

### Dashboard Overview (Light Mode)

- Statistics cards with real-time data
- Risk distribution chart
- Student list with filtering
- H5P analytics

### Dashboard Overview (Dark Mode)

- Eye-friendly dark theme
- Smooth theme transitions
- Consistent color scheme across all components

### Student Detail Page

- Risk score with SHAP explanation
- Feature importance visualization
- H5P interaction timeline
- Intervention suggestions

### Loading States

- Skeleton screens for smooth UX
- Shimmer animation effect
- Consistent loading experience

## �️ Roadmap

### Completed ✅

- [x] CatBoost ML model with 80+ features
- [x] RESTful API with Flask
- [x] React dashboard with TypeScript
- [x] SHAP explainability integration
- [x] H5P analytics tracking
- [x] Loading skeleton system
- [x] Dark mode theme
- [x] Smart navigation guards

### In Progress 🚧

- [ ] Comprehensive test coverage (pytest + vitest)
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Performance optimization
- [ ] Mobile responsive improvements

### Planned 📅

- [ ] Real-time notifications for high-risk students
- [ ] Email alerts to instructors
- [ ] Advanced filtering and search
- [ ] Export reports (PDF/Excel)
- [ ] Multi-language support (EN/VI)
- [ ] Student engagement predictions
- [ ] Intervention tracking system
- [ ] A/B testing for interventions

## �👨‍💻 Author

**Thesis Project** - Student Dropout Prediction System  
University of Science, VNU-HCM  
Open edX Analytics Platform

## 🙏 Acknowledgments

- **Open edX Platform** - Data source and inspiration
- **CatBoost Team** - Excellent ML library
- **React Community** - Frontend ecosystem
- **SHAP** - Model explainability framework

## �📄 License

MIT
