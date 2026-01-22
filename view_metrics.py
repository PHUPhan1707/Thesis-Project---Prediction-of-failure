import pickle
import sys

# Load metrics
with open('models/fm101_model_v3_metrics.pkl', 'rb') as f:
    metrics = pickle.load(f)

print('=' * 50)
print('MODEL V2 METRICS (WITHOUT GRADE LEAKAGE)')
print('=' * 50)
print(f'\nPerformance Metrics:')
print(f'  AUC-ROC: {metrics["auc_roc"]:.4f}')
print(f'  Precision: {metrics["precision"]:.4f}')
print(f'  Recall: {metrics["recall"]:.4f}')
print(f'  F1-Score: {metrics["f1_score"]:.4f}')

print(f'\nConfusion Matrix:')
cm = metrics['confusion_matrix']
print(f'  TN: {cm[0][0]}, FP: {cm[0][1]}')
print(f'  FN: {cm[1][0]}, TP: {cm[1][1]}')

print(f'\nTop 10 Important Features:')
for i, f in enumerate(metrics['top_features'][:10], 1):
    print(f"  {i}. {f['feature']}: {f['importance']:.2f}")

print('\n' + '=' * 50)
