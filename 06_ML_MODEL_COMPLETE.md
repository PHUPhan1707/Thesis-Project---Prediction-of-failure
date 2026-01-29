# 🤖 ML MODEL - TÀI LIỆU TỔNG HỢP

## 📋 Mục Lục

1. [Overview](#overview)
2. [Feature Engineering](#feature-engineering)
3. [Model Training](#model-training)
4. [K-Fold Evaluation](#k-fold-evaluation)
5. [Prediction](#prediction)
6. [Model Performance](#model-performance)

---

## 🎯 OVERVIEW

### Technology Stack

- **ML Framework:** CatBoost 1.2.5
- **Feature Engineering:** pandas, numpy
- **Evaluation:** scikit-learn
- **Data:** MySQL → pandas DataFrame

### Pipeline

```
Raw Data (MySQL) 
    ↓
Feature Engineering
    ↓
Training Data (CSV)
    ↓
Model Training (CatBoost)
    ↓
Trained Model (.cbm)
    ↓
Predictions → Database
```

---

## 🔧 FEATURE ENGINEERING

### File: `ml/feature_engineering.py`

### Features Created

#### 1. Engagement Score
```python
engagement_score = (
    discussion_score * 0.25 +
    video_score * 0.25 +
    h5p_score * 0.25 +
    quiz_score * 0.25
)
```

#### 2. Activity Features
- `activity_recency` - Inverse of days_since_last_activity
- `activity_consistency` - Based on engagement and recency
- `is_inactive` - Không hoạt động > 7 ngày
- `is_highly_inactive` - Không hoạt động > 14 ngày

#### 3. Performance Features
- `relative_completion` - So với trung bình lớp
- `is_struggling` - Completion < 50%
- `is_at_risk` - Completion < 40%
- `completion_consistency` - Std deviation của completion rates

#### 4. Interaction Features
- `discussion_engagement_rate`
- `has_no_discussion`
- `video_engagement_rate`
- `h5p_engagement_rate`
- `interaction_score`

#### 5. Time Features
- `enrollment_phase` - very_early, early, mid, late, very_late
- `weeks_remaining` - Weeks còn lại
- `progress_rate` - Completion per week

### Usage

```bash
python ml/feature_engineering.py \
    --course-id "course-v1:..." \
    --output data/features.csv
```

**Output:** `data/features.csv` với 80+ features

---

## 🎓 MODEL TRAINING

### File: `ml/train_model.py`

### Model: CatBoostClassifier

**Parameters:**
```python
CatBoostClassifier(
    iterations=1000,
    learning_rate=0.05,
    depth=6,
    l2_leaf_reg=3,
    loss_function='Logloss',
    eval_metric='AUC',
    early_stopping_rounds=50
)
```

### Target Variable

- **Label:** `is_passed` (False → 1 = fail, True → 0 = pass)
- **Excluded:** `mooc_grade_percentage`, `mooc_letter_grade` (data leakage)

### Usage

```bash
python ml/train_model.py \
    --input data/features.csv \
    --model-name dropout_prediction_model \
    --iterations 1000 \
    --learning-rate 0.05 \
    --depth 6
```

**Output:**
- Model: `models/dropout_prediction_model.cbm`
- Metadata: `models/dropout_prediction_model_metadata.pkl`
- Metrics: `models/dropout_prediction_model_metrics.pkl`

### Evaluation Metrics

- **AUC-ROC**
- **Precision**
- **Recall**
- **F1-Score**
- **Confusion Matrix**

---

## 📊 K-FOLD EVALUATION

### File: `ml/kfold_evaluation.py`

### Purpose

Đánh giá model một cách ổn định với K-Fold Cross-Validation

### Usage

```bash
# 10-fold CV (default)
python ml/kfold_evaluation.py --input data/features.csv

# Custom số folds
python ml/kfold_evaluation.py --input data/features.csv --n-folds 5

# Save models
python ml/kfold_evaluation.py --input data/features.csv --save-models
```

### Output

**Files:**
- `results/kfold/kfold_results_YYYYMMDD_HHMMSS.json` - Chi tiết từng fold
- `results/kfold/kfold_results_YYYYMMDD_HHMMSS.csv` - Bảng kết quả
- `results/kfold/kfold_summary_YYYYMMDD_HHMMSS.json` - Tổng hợp (mean ± std)
- `results/kfold/kfold_results_YYYYMMDD_HHMMSS.png` - Biểu đồ

**Metrics:**
- Accuracy
- AUC-ROC
- Precision
- Recall
- F1-Score

**Stability Assessment:**
- std < 0.02: Very Stable ✓
- std < 0.05: Stable
- std < 0.10: Moderately Stable
- std ≥ 0.10: Unstable ⚠

**Xem chi tiết:** `KFOLD_CV_GUIDE.md`

---

## 🔮 PREDICTION

### File: `ml/predict.py`

### Usage

```bash
python ml/predict.py \
    --input data/features.csv \
    --course-id "course-v1:..." \
    --model-name dropout_prediction_model \
    --output data/predictions.csv \
    --save-db
```

### Output

**CSV File:**
- `user_id`, `course_id`
- `fail_risk_score` (0-100%)
- `risk_level` (HIGH/MEDIUM/LOW)
- `suggestions` (intervention recommendations)

**Database:**
- Update `raw_data.fail_risk_score`
- Update `raw_data.dropout_risk_score`

### Risk Classification

```python
if risk_score >= 70:
    return 'HIGH'
elif risk_score >= 40:
    return 'MEDIUM'
else:
    return 'LOW'
```

---

## 📈 MODEL PERFORMANCE

### Model V4 (Current)

**Metrics:**
- **Precision:** 86.79%
- **Recall:** 83.64%
- **F1-Score:** 85.19%
- **AUC-ROC:** ~0.85

**Risk Distribution:**
- HIGH risk (>70%): 235 students (25.5%)
- MEDIUM risk (40-70%): 60 students (6.5%)
- LOW risk (<40%): 626 students (68.0%)

**Top Features:**
1. `current_chapter` (19.42)
2. `mooc_completion_rate` (15.23)
3. `days_since_last_activity` (12.18)
4. `video_completion_rate` (10.45)
5. `quiz_avg_score` (8.92)

**Xem chi tiết:** `PREDICTION_RESULTS.md`

---

## 🔄 AUTOMATION

### Daily Predictions

**File:** `scripts/daily_prediction.py`

```bash
python scripts/daily_prediction.py
```

**Workflow:**
1. Fetch new data from APIs
2. Aggregate into raw_data
3. Generate features
4. Make predictions
5. Update database

### Model Retraining

**File:** `scripts/retrain_model.py`

```bash
python scripts/retrain_model.py
```

**Workflow:**
1. Load latest features
2. Train new model
3. Evaluate performance
4. Save if better than current

---

## 📊 FEATURE IMPORTANCE

### Top 10 Features (Model V4)

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | current_chapter | 19.42 |
| 2 | mooc_completion_rate | 15.23 |
| 3 | days_since_last_activity | 12.18 |
| 4 | video_completion_rate | 10.45 |
| 5 | quiz_avg_score | 8.92 |
| 6 | h5p_completion_rate | 7.65 |
| 7 | discussion_total_interactions | 6.34 |
| 8 | weeks_since_enrollment | 5.87 |
| 9 | engagement_score | 5.12 |
| 10 | activity_recency | 4.78 |

---

## 🎯 FUTURE IMPROVEMENTS

### Model V5 (Planned)

**New Features:**
- `problem_improvement_rate` - Tỷ lệ cải thiện điểm số
- `activity_consistency` - Độ nhất quán hoạt động
- `velocity_trend` - Xu hướng tốc độ học
- `longest_streak` - Chuỗi ngày học liên tục dài nhất
- `avg_attempts_to_pass` - Số lần thử trung bình để pass

**Expected Performance:**
- **Recall:** 89-92% (tăng từ 83.64%)
- **Students Caught:** 252-280/280 (tăng từ 197/235)
- **False Negatives:** 3-8 (giảm từ 38)

**Xem chi tiết:** `API_REQUIREMENTS_SUMMARY.md`, `API_VISUAL_GUIDE.md`

---

## 🧪 TESTING

### Test Feature Engineering

```bash
python ml/feature_engineering.py --output data/test_features.csv
# Kiểm tra file có đủ features
```

### Test Model Training

```bash
python ml/train_model.py --input data/features.csv --iterations 100
# Kiểm tra model được tạo
```

### Test Predictions

```bash
python ml/predict.py --input data/features.csv --course-id "course-v1:..." --output test_predictions.csv
# Kiểm tra predictions file
```

---

## 📚 Tài Liệu Liên Quan

- **Feature Engineering:** `ml/feature_engineering.py`
- **Training:** `ml/train_model.py`
- **K-Fold CV:** `ml/kfold_evaluation.py`, `KFOLD_CV_GUIDE.md`
- **Prediction:** `ml/predict.py`
- **Results:** `PREDICTION_RESULTS.md`
- **API Requirements:** `API_REQUIREMENTS_SUMMARY.md`

