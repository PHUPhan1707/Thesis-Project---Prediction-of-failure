"""
Threshold Analysis & Risk Tier Distribution
Section 4.2.3 - generates Table 10 + Figure 26
"""
import sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from catboost import CatBoostClassifier, Pool

# === CONFIG ===
LEAKAGE = ['mooc_grade_percentage','mooc_letter_grade','mooc_is_passed',
           'current_chapter','current_section','current_unit']
META    = ['id','user_id','course_id','username','email','full_name',
           'enrollment_id','mssv','faculty','mode','is_active','created',
           'last_activity','enrollment_date','fetched_at','extracted_at',
           'extraction_batch_id','updated_at','is_passed']
CAT     = ['enrollment_mode','enrollment_phase']
OUT     = 'results/evaluation_4_2_2'

COURSES = {
    'FM101' : 'data/features_fm101_eval.csv',
    'ST101' : 'data/features_st101_eval.csv',
    'QTH101': 'data/features_qth101_eval.csv',
    'KTVM'  : 'data/features_ktvm_eval.csv',
}
LABELS = {
    'FM101' : 'Nguyen ly TTTC\n(FM101)',
    'ST101' : 'Thong ke KD\n(ST101)',
    'QTH101': 'Quan tri hoc\n(QTH101)',
    'KTVM'  : 'Kinh te vi mo\n(KTVM)',
}

THRESHOLDS   = [0.20, 0.30, 0.40, 0.50, 0.55, 0.60, 0.70]
T_HIGH = 0.55
T_LOW  = 0.30


def prepare(df):
    drop = [c for c in META + LEAKAGE if c in df.columns]
    X = df.drop(columns=drop, errors='ignore')
    y = (~df['is_passed'].astype(bool)).astype(int)
    for c in X.columns:
        if c in CAT:
            X[c] = X[c].fillna('missing').astype(str)
        else:
            X[c] = pd.to_numeric(X[c], errors='coerce').fillna(0)
    cat_idx = [i for i, c in enumerate(X.columns) if c in CAT]
    return X, y, cat_idx


def train_model(X_tr, y_tr, X_te, y_te, cat_idx):
    model = CatBoostClassifier(
        iterations=1000, learning_rate=0.05, depth=6,
        l2_leaf_reg=3, loss_function='Logloss', eval_metric='F1',
        auto_class_weights='Balanced', random_seed=42,
        early_stopping_rounds=50, use_best_model=True, verbose=0)
    model.fit(Pool(X_tr, y_tr, cat_features=cat_idx),
              eval_set=Pool(X_te, y_te, cat_features=cat_idx))
    return model.predict_proba(X_te)[:, 1]


# ── Train all courses & collect probabilities ─────────────────────────────────
print("Training models for all courses...")
all_probs, all_ys = {}, {}
for key, path in COURSES.items():
    df = pd.read_csv(path)
    X, y, cat_idx = prepare(df)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    probs = train_model(X_tr, y_tr, X_te, y_te, cat_idx)
    all_probs[key] = probs
    all_ys[key]    = y_te.values
    print(f"  {key}: test={len(y_te)} | fail={y_te.sum()}")


# ── TABLE 10: Threshold Analysis (FM101) ─────────────────────────────────────
print("\n=== TABLE 10: THRESHOLD ANALYSIS (FM101 representative) ===")
header = f"  {'Threshold':>10} | {'Precision':>10} | {'Recall':>10} | {'F1':>10} | {'TP':>5} | {'FP':>5} | {'FN':>5} | {'TN':>5}"
print(header)
print("  " + "-" * 75)

probs_fm = all_probs['FM101']
y_fm     = all_ys['FM101']

for t in THRESHOLDS:
    pred = (probs_fm >= t).astype(int)
    p  = precision_score(y_fm, pred, zero_division=0)
    r  = recall_score(y_fm, pred, zero_division=0)
    f  = f1_score(y_fm, pred, zero_division=0)
    cm = confusion_matrix(y_fm, pred)
    tn, fp, fn, tp = cm.ravel()
    note = ""
    if t == T_LOW:
        note = " <-- T_low (Low/Medium boundary)"
    elif t == T_HIGH:
        note = " <-- T_high (Medium/High boundary)"
    print(f"  {t:>10.2f} | {p:>10.4f} | {r:>10.4f} | {f:>10.4f} | {tp:>5} | {fp:>5} | {fn:>5} | {tn:>5}{note}")


# ── Risk Tier Distribution ────────────────────────────────────────────────────
print("\n=== RISK TIER DISTRIBUTION (T_low=0.30, T_high=0.55) ===")
tier_data = {}
for key in COURSES:
    probs  = all_probs[key]
    high   = int((probs >= T_HIGH).sum())
    medium = int(((probs >= T_LOW) & (probs < T_HIGH)).sum())
    low    = int((probs < T_LOW).sum())
    total  = len(probs)
    tier_data[key] = {'HIGH': high, 'MEDIUM': medium, 'LOW': low, 'total': total}
    print(f"  {key}: LOW={low}({low/total*100:.1f}%) "
          f"MED={medium}({medium/total*100:.1f}%) "
          f"HIGH={high}({high/total*100:.1f}%) | total={total}")


# ── FIGURE 26: Risk Tier Distribution (grouped bar + stacked %) ───────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Figure 26: Risk Tier Distribution — Hold-out Test Set (20%)',
             fontsize=13, fontweight='bold', y=1.01)

colors = {'LOW': '#4CAF50', 'MEDIUM': '#FF9800', 'HIGH': '#F44336'}
keys   = list(COURSES.keys())
x      = np.arange(len(keys))
w      = 0.25

# (a) Absolute count
ax = axes[0]
for i, (tier, color) in enumerate(colors.items()):
    vals = [tier_data[k][tier] for k in keys]
    bars = ax.bar(x + (i - 1) * w, vals, w,
                  label=tier, color=color, alpha=0.85, edgecolor='white', linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                str(v), ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels([LABELS[k] for k in keys], fontsize=9)
ax.set_ylabel('Number of Students', fontsize=11)
ax.set_title('(a) Absolute Count by Risk Tier', fontsize=11)
ax.legend(title='Risk Level', fontsize=9)
ax.grid(axis='y', alpha=0.3)
ax.set_ylim(0, max(tier_data[k]['LOW'] for k in keys) * 1.2)

# (b) Stacked percentage
ax2 = axes[1]
bottoms = np.zeros(len(keys))
for tier, color in colors.items():
    pcts  = [tier_data[k][tier] / tier_data[k]['total'] * 100 for k in keys]
    bars  = ax2.bar(x, pcts, 0.5, bottom=bottoms,
                    label=tier, color=color, alpha=0.85, edgecolor='white', linewidth=0.5)
    for bar, pct, bot in zip(bars, pcts, bottoms):
        if pct > 5:
            ax2.text(bar.get_x() + bar.get_width() / 2,
                     bot + pct / 2,
                     f'{pct:.1f}%', ha='center', va='center',
                     fontsize=9, fontweight='bold', color='white')
    bottoms += np.array(pcts)

ax2.set_xticks(x)
ax2.set_xticklabels([LABELS[k] for k in keys], fontsize=9)
ax2.set_ylabel('Percentage (%)', fontsize=11)
ax2.set_ylim(0, 100)
ax2.set_title('(b) Percentage Distribution by Risk Tier', fontsize=11)
ax2.legend(title='Risk Level', fontsize=9, loc='upper right')
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
path26 = f'{OUT}/figure26_risk_tier_distribution.png'
plt.savefig(path26, dpi=150, bbox_inches='tight')
plt.close()
print(f"\nFigure 26 saved: {path26}")


# ── FIGURE 26b: Threshold curve (Precision/Recall/F1 vs threshold) ────────────
thresholds_fine = np.arange(0.10, 0.91, 0.01)
prec_l, rec_l, f1_l = [], [], []
for t in thresholds_fine:
    pred = (probs_fm >= t).astype(int)
    prec_l.append(precision_score(y_fm, pred, zero_division=0))
    rec_l.append(recall_score(y_fm, pred, zero_division=0))
    f1_l.append(f1_score(y_fm, pred, zero_division=0))

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(thresholds_fine, prec_l, '#2196F3', lw=2.5, label='Precision')
ax.plot(thresholds_fine, rec_l,  '#F44336', lw=2.5, label='Recall')
ax.plot(thresholds_fine, f1_l,   '#4CAF50', lw=2.5, label='F1-Score')
ax.axvline(T_LOW,  color='#FF9800', linestyle='--', lw=2,
           label=f'T_low = {T_LOW} (Low | Medium)')
ax.axvline(T_HIGH, color='#9C27B0', linestyle='--', lw=2,
           label=f'T_high = {T_HIGH} (Medium | High)')
ax.axvspan(0.10,   T_LOW,  alpha=0.07, color='#4CAF50')
ax.axvspan(T_LOW,  T_HIGH, alpha=0.07, color='#FF9800')
ax.axvspan(T_HIGH, 0.90,   alpha=0.07, color='#F44336')

# zone labels
ax.text(0.18, 0.92, 'LOW', transform=ax.transAxes,
        fontsize=11, color='#2E7D32', fontweight='bold', ha='center')
ax.text(0.50, 0.92, 'MEDIUM', transform=ax.transAxes,
        fontsize=11, color='#E65100', fontweight='bold', ha='center')
ax.text(0.82, 0.92, 'HIGH', transform=ax.transAxes,
        fontsize=11, color='#B71C1C', fontweight='bold', ha='center')

ax.set_xlabel('Decision Threshold (p)', fontsize=12)
ax.set_ylabel('Metric Score', fontsize=12)
ax.set_title('Threshold vs Precision / Recall / F1 — FM101 Test Set (n = 186)',
             fontsize=12, fontweight='bold')
ax.legend(fontsize=10, loc='lower left')
ax.set_xlim(0.10, 0.90)
ax.set_ylim(0, 1.05)
ax.grid(alpha=0.3)

plt.tight_layout()
path26b = f'{OUT}/figure26b_threshold_curve.png'
plt.savefig(path26b, dpi=150, bbox_inches='tight')
plt.close()
print(f"Figure 26b saved: {path26b}")
print("\nAll done!")
