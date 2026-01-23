# K-Fold Cross-Validation Guide

## Overview
K-Fold Cross-Validation script để đánh giá model CatBoost một cách ổn định và đáng tin cậy hơn.

## Cách sử dụng

### 1. Basic Usage (10-fold CV)

```bash
cd d:\ProjectThesis\dropout_prediction

# Chạy với features đã có
python ml/kfold_evaluation.py --input data/features_v3.csv
```

### 2. Custom số folds

```bash
# Chạy với 5 folds
python ml/kfold_evaluation.py --input data/features_v3.csv --n-folds 5

# Chạy với 20 folds
python ml/kfold_evaluation.py --input data/features_v3.csv --n-folds 20
```

### 3. Custom hyperparameters

```bash
python ml/kfold_evaluation.py \
  --input data/features_v3.csv \
  --n-folds 10 \
  --iterations 1500 \
  --learning-rate 0.03 \
  --depth 8
```

### 4. Save tất cả models

```bash
# Lưu lại 10 models từ 10 folds
python ml/kfold_evaluation.py \
  --input data/features_v3.csv \
  --save-models
```

## Output Files

Sau khi chạy xong, sẽ tạo ra các files trong thư mục `results/`:

1. **kfold_results_YYYYMMDD_HHMMSS.json** - Chi tiết kết quả từng fold
2. **kfold_results_YYYYMMDD_HHMMSS.csv** - Bảng kết quả dạng CSV
3. **kfold_summary_YYYYMMDD_HHMMSS.json** - Tổng hợp metrics (mean ± std)
4. **kfold_results_YYYYMMDD_HHMMSS.png** - Biểu đồ trực quan

## Metrics được đánh giá

Mỗi fold sẽ được đánh giá với các metrics sau:

- **Accuracy** - Độ chính xác tổng thể
- **AUC-ROC** - Area Under ROC Curve
- **Precision** - Precision của class Fail
- **Recall** - Recall của class Fail  
- **F1-Score** - F1-Score của class Fail
- **Confusion Matrix** - TN, FP, FN, TP

## Kết quả mong đợi

### Ví dụ output:

```
==========================================================
K-FOLD CROSS-VALIDATION SUMMARY (10 folds)
==========================================================

Total samples: 1000
Avg train/test split: 900 / 100

Model Performance (Mean ± Std):
  Accuracy:  0.8234 ± 0.0156
  AUC-ROC:   0.8567 ± 0.0234
  Precision: 0.7845 ± 0.0298
  Recall:    0.7123 ± 0.0345
  F1-Score:  0.7467 ± 0.0287

Model Stability Assessment:
  ACCURACY: Very Stable ✓ (std=0.0156)
  AUC_ROC: Very Stable ✓ (std=0.0234)
  PRECISION: Stable (std=0.0298)
  RECALL: Stable (std=0.0345)
  F1_SCORE: Stable (std=0.0287)
```

### Đánh giá stability:

- **std < 0.02**: Very Stable ✓ (rất ổn định)
- **std < 0.05**: Stable (ổn định)
- **std < 0.10**: Moderately Stable (tạm ổn)
- **std ≥ 0.10**: Unstable ⚠ (không ổn định)

## So sánh với single train-test split

### Single split (hiện tại):
```
AUC-ROC: 0.8567
→ Không biết con số này có may mắn không
```

### K-Fold CV (10 folds):
```
AUC-ROC: 0.8567 ± 0.0234
→ Model ổn định trong khoảng [0.8333, 0.8801]
→ Tin tưởng hơn vào performance thực tế
```

## Biểu đồ visualization

Script sẽ tạo ra 6 biểu đồ:

1. **Metrics Across Folds** - Line plot cho mỗi fold
2. **Metrics Distribution** - Box plot
3. **Mean ± Std** - Bar chart với error bars
4. **Average Confusion Matrix** - Heatmap
5. **Train/Test Fail Rate** - So sánh tỷ lệ fail
6. **Metric Stability** - Horizontal bar chart của std

## Best Practices

1. **Số folds phù hợp**:
   - Data < 1,000: dùng 5 folds
   - Data 1,000-10,000: dùng 10 folds
   - Data > 10,000: dùng 5-10 folds

2. **Khi nào dùng K-Fold CV**:
   - ✅ Đánh giá model trước khi deploy
   - ✅ So sánh nhiều models với nhau
   - ✅ Kiểm tra hyperparameters
   - ❌ KHÔNG dùng để train final model

3. **Sau khi hài lòng với K-Fold results**:
   - Train lại model trên 100% data
   - Deploy model đó

## Example Workflow

```bash
# Bước 1: Đánh giá model với K-Fold CV
python ml/kfold_evaluation.py --input data/features_v3.csv --n-folds 10

# Bước 2: Xem kết quả và quyết định
# Nếu metrics ổn (std thấp), tiếp tục

# Bước 3: Train final model trên 100% data
python ml/train_model.py --input data/features_v3.csv --model-name final_model

# Bước 4: Deploy final_model
python scripts/daily_prediction.py
```

## Troubleshooting

### Error: "Not enough samples for N folds"
→ Giảm số folds hoặc tăng data

### Error: "Imbalanced classes in some folds"
→ Dùng `StratifiedKFold` (đã tự động sử dụng)

### Model quá lâu để train
→ Giảm `--iterations` hoặc số folds
