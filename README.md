# Dropout Prediction System

Hệ thống phân tích dữ liệu và hỗ trợ quyết định cho giảng viên trên nền tảng Open edX.

## Features

- 🤖 **ML Model**: CatBoost 1.2.5 classifier để dự đoán fail risk
- 📊 **Feature Engineering**: 15+ derived features từ raw data
- 🎯 **Risk Classification**: HIGH/MEDIUM/LOW risk levels
- 💡 **Intervention Suggestions**: Gợi ý can thiệp tự động
- ⚙️ **Automation**: Daily predictions và model retraining

## Project Structure

```
dropout_prediction/
├── database/               # Data collection & storage
│   ├── schema.sql
│   ├── migrations/
│   ├── fetch_mooc_h5p_data.py
│   └── storage_manager.py
├── ml/                    # ML pipeline
│   ├── feature_engineering.py
│   ├── train_model.py
│   └── predict.py
├── scripts/               # Automation scripts
│   ├── daily_prediction.py
│   └── retrain_model.py
├── models/                # Trained models
├── data/                  # Features & predictions
├── logs/                  # Log files
└── requirements.txt
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database (see database/README.md)
cd database
# Run migrations...
```

## Usage

### 1. Collect Data

```bash
cd database
python fetch_mooc_h5p_data.py --course-id "course-v1:..."
```

### 2. Feature Engineering

```bash
python ml/feature_engineering.py --output data/features.csv
```

### 3. Train Model

```bash
python ml/train_model.py --input data/features.csv
```

### 4. Make Predictions

```bash
python ml/predict.py \
    --input data/features.csv \
    --course-id "course-v1:..." \
    --save-db
```

### 5. Automation

```bash
# Daily predictions
python scripts/daily_prediction.py

# Model retraining
python scripts/retrain_model.py
```
 
## License

MIT
