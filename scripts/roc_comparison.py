"""
ROC Curve Comparison — CatBoost vs LightGBM vs XGBoost vs Random Forest vs Logistic Regression
Generates:
  - Figure: ROC overlay (all 5 models, FM101 hold-out test set)
  - Figure: Precision-Recall overlay
  - Figure: Bar chart comparison (all metrics)
  - Console: summary table with actual numbers
"""
import sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_curve, auc, precision_recall_curve,
    average_precision_score,
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from catboost import CatBoostClassifier, Pool
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

# ── CONFIG ──────────────────────────────────────────────────────────────
LEAKAGE = ['mooc_grade_percentage','mooc_letter_grade','mooc_is_passed',
           'current_chapter','current_section','current_unit']
META    = ['id','user_id','course_id','username','email','full_name',
           'enrollment_id','mssv','faculty','mode','is_active','created',
           'last_activity','enrollment_date','fetched_at','extracted_at',
           'extraction_batch_id','updated_at','is_passed']
CAT     = ['enrollment_mode','enrollment_phase']
OUT     = 'results/model_comparison'

DATA_PATH = 'data/features_fm101_eval.csv'
COURSE_NAME = 'FM101 — Nguyên lý Thị trường Tài chính'

COLORS = {
    'CatBoost'           : '#E53935',
    'LightGBM'           : '#FB8C00',
    'XGBoost'            : '#43A047',
    'Random Forest'      : '#1E88E5',
    'Logistic Regression': '#8E24AA',
}

# ── DATA PREP ────────────────────────────────────────────────────────────
def prepare(df):
    drop = [c for c in META + LEAKAGE if c in df.columns]
    X = df.drop(columns=drop, errors='ignore')
    y = (~df['is_passed'].astype(bool)).astype(int)
    # Encode categoricals for sklearn models
    X_enc = X.copy()
    for c in X_enc.columns:
        if c in CAT:
            X_enc[c] = X_enc[c].fillna('missing').astype(str)
        else:
            X_enc[c] = pd.to_numeric(X_enc[c], errors='coerce').fillna(0)
    cat_idx = [i for i, c in enumerate(X_enc.columns) if c in CAT]
    return X_enc, y, cat_idx

def encode_for_sklearn(X):
    """Label-encode categoricals for sklearn-compatible models."""
    X2 = X.copy()
    for c in CAT:
        if c in X2.columns:
            le = LabelEncoder()
            X2[c] = le.fit_transform(X2[c].fillna('missing').astype(str))
    return X2.astype(float)

# ── LOAD & SPLIT ─────────────────────────────────────────────────────────
print(f"Loading {DATA_PATH} ...")
df = pd.read_csv(DATA_PATH)
X, y, cat_idx = prepare(df)
X_sk = encode_for_sklearn(X)

X_tr,  X_te,  y_tr,  y_te  = train_test_split(X,    y, test_size=0.2, random_state=42, stratify=y)
Xsk_tr, Xsk_te, _, _        = train_test_split(X_sk, y, test_size=0.2, random_state=42, stratify=y)

n_test  = len(y_te)
n_fail  = int(y_te.sum())
pos_weight = float((y_tr == 0).sum()) / float((y_tr == 1).sum())

print(f"Test set: {n_test} samples | fail={n_fail} ({n_fail/n_test*100:.1f}%) | pass={n_test-n_fail}")

# ── MODEL DEFINITIONS ─────────────────────────────────────────────────────
models_cfg = {
    'CatBoost': {
        'model': CatBoostClassifier(
            iterations=1000, learning_rate=0.05, depth=6, l2_leaf_reg=3,
            loss_function='Logloss', eval_metric='F1',
            auto_class_weights='Balanced', random_seed=42,
            early_stopping_rounds=50, use_best_model=True, verbose=0),
        'catboost': True,
    },
    'LightGBM': {
        'model': LGBMClassifier(
            n_estimators=1000, learning_rate=0.05, max_depth=6,
            class_weight='balanced', random_state=42,
            n_jobs=-1, verbose=-1,
            callbacks=[]),
        'catboost': False,
    },
    'XGBoost': {
        'model': XGBClassifier(
            n_estimators=1000, learning_rate=0.05, max_depth=6,
            scale_pos_weight=pos_weight, random_state=42,
            eval_metric='logloss', early_stopping_rounds=50,
            verbosity=0, use_label_encoder=False),
        'catboost': False,
    },
    'Random Forest': {
        'model': RandomForestClassifier(
            n_estimators=500, max_depth=10,
            class_weight='balanced', random_state=42, n_jobs=-1),
        'catboost': False,
    },
    'Logistic Regression': {
        'model': LogisticRegression(
            C=1.0, class_weight='balanced', max_iter=1000,
            random_state=42, n_jobs=-1),
        'catboost': False,
    },
}

# ── TRAIN & EVALUATE ──────────────────────────────────────────────────────
results = {}
print("\nTraining models...")

for name, cfg in models_cfg.items():
    print(f"  Training {name} ...", end=' ', flush=True)
    m = cfg['model']

    if cfg['catboost']:
        m.fit(Pool(X_tr, y_tr, cat_features=cat_idx),
              eval_set=Pool(X_te, y_te, cat_features=cat_idx))
        probs = m.predict_proba(X_te)[:, 1]
    elif name == 'XGBoost':
        m.fit(Xsk_tr, y_tr,
              eval_set=[(Xsk_te, y_te)],
              verbose=False)
        probs = m.predict_proba(Xsk_te)[:, 1]
    else:
        m.fit(Xsk_tr, y_tr)
        probs = m.predict_proba(Xsk_te)[:, 1]

    preds = (probs >= 0.5).astype(int)

    acc  = accuracy_score(y_te, preds)
    prec = precision_score(y_te, preds, zero_division=0)
    rec  = recall_score(y_te, preds, zero_division=0)
    f1   = f1_score(y_te, preds, zero_division=0)
    rauc = roc_auc_score(y_te, probs)
    prauc= average_precision_score(y_te, probs)

    fpr, tpr, _ = roc_curve(y_te, probs)
    p_curve, r_curve, _ = precision_recall_curve(y_te, probs)

    results[name] = {
        'probs': probs, 'preds': preds,
        'accuracy': acc, 'precision': prec, 'recall': rec,
        'f1': f1, 'roc_auc': rauc, 'pr_auc': prauc,
        'fpr': fpr, 'tpr': tpr,
        'p_curve': p_curve, 'r_curve': r_curve,
    }
    print(f"F1={f1:.4f} | AUC={rauc:.4f} | Recall={rec:.4f}")

# ── CONSOLE TABLE ─────────────────────────────────────────────────────────
print(f"\n{'='*80}")
print(f"MODEL COMPARISON — {COURSE_NAME} — Hold-out Test Set (n={n_test})")
print(f"{'='*80}")
print(f"  {'Model':<22} | {'Accuracy':>9} | {'Precision':>9} | {'Recall':>9} | {'F1':>9} | {'AUC-ROC':>9} | {'PR-AUC':>9}")
print(f"  {'-'*90}")
for name, r in results.items():
    print(f"  {name:<22} | {r['accuracy']:>9.4f} | {r['precision']:>9.4f} | "
          f"{r['recall']:>9.4f} | {r['f1']:>9.4f} | {r['roc_auc']:>9.4f} | {r['pr_auc']:>9.4f}")
print(f"{'='*80}")

# ── FIGURE A: ROC CURVE OVERLAY ───────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle(f'Model Comparison — {COURSE_NAME}\nHold-out Test Set (n = {n_test}, fail rate = {n_fail/n_test*100:.1f}%)',
             fontsize=12, fontweight='bold', y=1.01)

# (a) ROC
ax = axes[0]
for name, r in results.items():
    color = COLORS[name]
    lw = 3 if name == 'CatBoost' else 1.8
    ls = '-' if name == 'CatBoost' else '--'
    ax.plot(r['fpr'], r['tpr'], color=color, lw=lw, linestyle=ls,
            label=f"{name} (AUC = {r['roc_auc']:.4f})")

ax.plot([0, 1], [0, 1], 'k--', lw=1.2, alpha=0.6, label='Random Classifier (AUC = 0.5000)')
ax.fill_between(results['CatBoost']['fpr'], results['CatBoost']['tpr'],
                alpha=0.06, color=COLORS['CatBoost'])
ax.set_xlabel('False Positive Rate', fontsize=11)
ax.set_ylabel('True Positive Rate', fontsize=11)
ax.set_title('(a) ROC Curve Comparison', fontsize=11, fontweight='bold')
ax.legend(fontsize=9, loc='lower right')
ax.grid(alpha=0.3)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1.02)

# (b) Precision-Recall
ax2 = axes[1]
baseline = n_fail / n_test
for name, r in results.items():
    color = COLORS[name]
    lw = 3 if name == 'CatBoost' else 1.8
    ls = '-' if name == 'CatBoost' else '--'
    ax2.plot(r['r_curve'], r['p_curve'], color=color, lw=lw, linestyle=ls,
             label=f"{name} (PR-AUC = {r['pr_auc']:.4f})")

ax2.axhline(baseline, color='k', linestyle='--', lw=1.2, alpha=0.6,
            label=f'Random Classifier (PR-AUC = {baseline:.4f})')
ax2.set_xlabel('Recall', fontsize=11)
ax2.set_ylabel('Precision', fontsize=11)
ax2.set_title('(b) Precision–Recall Curve Comparison', fontsize=11, fontweight='bold')
ax2.legend(fontsize=9, loc='upper right')
ax2.grid(alpha=0.3)
ax2.set_xlim(0, 1)
ax2.set_ylim(0, 1.02)

plt.tight_layout()
path_roc = f'{OUT}/figure_roc_pr_comparison_fm101.png'
plt.savefig(path_roc, dpi=150, bbox_inches='tight')
plt.close()
print(f"\nFigure saved: {path_roc}")

# ── FIGURE B: METRIC BAR CHART ────────────────────────────────────────────
metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'ROC-AUC', 'PR-AUC']
keys    = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'pr_auc']
model_names = list(results.keys())

fig, ax = plt.subplots(figsize=(13, 6))
x  = np.arange(len(metrics))
w  = 0.15
n  = len(model_names)
offsets = np.linspace(-(n-1)/2 * w, (n-1)/2 * w, n)

for i, name in enumerate(model_names):
    vals = [results[name][k] for k in keys]
    bars = ax.bar(x + offsets[i], vals, w,
                  label=name, color=COLORS[name],
                  alpha=0.85, edgecolor='white', linewidth=0.5)
    for bar, v in zip(bars, vals):
        if v > 0.5:
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 0.005,
                    f'{v:.3f}', ha='center', va='bottom',
                    fontsize=6.5, fontweight='bold', rotation=90)

ax.set_xticks(x)
ax.set_xticklabels(metrics, fontsize=10)
ax.set_ylabel('Score', fontsize=11)
ax.set_ylim(0.6, 1.06)
ax.set_title(f'Model Performance Comparison — {COURSE_NAME}\nHold-out Test Set (n = {n_test})',
             fontsize=11, fontweight='bold')
ax.legend(fontsize=9, ncol=2)
ax.grid(axis='y', alpha=0.3)

# Highlight best per metric
for xi, k in enumerate(keys):
    best_val = max(results[name][k] for name in model_names)
    best_name = max(model_names, key=lambda n: results[n][k])
    bi = model_names.index(best_name)
    ax.bar(xi + offsets[bi], results[best_name][k], w,
           color=COLORS[best_name], alpha=1.0,
           edgecolor='black', linewidth=1.5)

plt.tight_layout()
path_bar = f'{OUT}/figure_bar_comparison_fm101.png'
plt.savefig(path_bar, dpi=150, bbox_inches='tight')
plt.close()
print(f"Figure saved: {path_bar}")

print("\nAll done!")
