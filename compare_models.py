import pickle

print("=" * 60)
print("MODEL COMPARISON: V3 vs V4 (Option 2)")
print("=" * 60)

v3 = pickle.load(open('models/fm101_model_v3_metrics.pkl', 'rb'))
v4 = pickle.load(open('models/fm101_model_v4_metrics.pkl', 'rb'))

print("\nModel V3 (No Grade, No Option 2):")
print(f"  AUC-ROC:   {v3['auc_roc']:.4f}")
print(f"  Precision: {v3['precision']:.4f}")
print(f"  Recall:    {v3['recall']:.4f}")
print(f"  F1-Score:  {v3['f1_score']:.4f}")

print("\nModel V4 (No Grade, WITH Option 2):")
print(f"  AUC-ROC:   {v4['auc_roc']:.4f}")
print(f"  Precision: {v4['precision']:.4f}")
print(f"  Recall:    {v4['recall']:.4f}")
print(f"  F1-Score:  {v4['f1_score']:.4f}")

print("\nImprovement:")
print(f"  AUC-ROC:   {(v4['auc_roc']-v3['auc_roc'])*100:+.2f}%")
print(f"  Precision: {(v4['precision']-v3['precision'])*100:+.2f}%")
print(f"  Recall:    {(v4['recall']-v3['recall'])*100:+.2f}%")
print(f"  F1-Score:  {(v4['f1_score']-v3['f1_score'])*100:+.2f}%")

print("\n" + "=" * 60)
print("TOP 10 FEATURES - Model V4:")
print("=" * 60)
for i, f in enumerate(v4['top_features'][:10], 1):
    marker = " <-- NEW!" if any(x in f['feature'] for x in ['percentile', 'relative', 'below', 'top_performer', 'bottom']) else ""
    print(f"{i:2d}. {f['feature']:40s} {f['importance']:6.2f}{marker}")

print("\n" + "=" * 60)
print("PREDICTION DISTRIBUTION:")
print("=" * 60)
print("V3: HIGH=219 (23.8%), MEDIUM=89 (9.7%), LOW=613 (66.6%)")
print("V4: HIGH=235 (25.5%), MEDIUM=60 (6.5%), LOW=626 (68.0%)")
print("\nNote: V4 identifies more at-risk students (16 more in HIGH)")
