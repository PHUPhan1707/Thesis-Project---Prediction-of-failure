"""
Full Evaluation Script for 4.2.2 Model Performance
Generates: Test metrics, Confusion Matrix, ROC, PR Curve, Training Loss
Courses: FM101, ST101, QTH101, KTVM (merged 7 sections)
"""
import sys, os, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import mysql.connector
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, average_precision_score, log_loss,
    confusion_matrix, roc_curve, precision_recall_curve)
from catboost import CatBoostClassifier, Pool
import json

# ─── CONFIG ──────────────────────────────────────────────────────────────────
DB_CONFIG = dict(host='127.0.0.1', port=4000, user='dropout_user',
                 password='dropout_pass_123', database='dropout_prediction_db')

COURSES = {
    'FM101':  ['course-v1:DHQG-HCM+FM101+2025_S2'],
    'ST101':  ['course-v1:DHQG-HCM+ST101+2025_S2'],
    'QTH101': ['course-v1:DHQG-HCM+QTH101+2026_S1'],
    'KTVM':   [
        'course-v1:UEL+252BEE1038_01+2025_12',
        'course-v1:UEL+252BEE1038_02+2025_12',
        'course-v1:UEL+252BEE1038_03+2025_12',
        'course-v1:UEL+252BEE1038_04+2025_12',
        'course-v1:UEL+252BEE1038_05+2025_12',
        'course-v1:UEL+252BEE1038_06+2025_12',
        'course-v1:UEL+252BEE1038_07+2025_12',
    ]
}

COURSE_LABELS = {
    'FM101':  'Nguyên lý TTTC (FM101)',
    'ST101':  'Thống kê KD (ST101)',
    'QTH101': 'Quản trị học (QTH101)',
    'KTVM':   'Kinh tế vĩ mô (KTVM)',
}

LEAKAGE_COLS = ['mooc_grade_percentage','mooc_letter_grade','mooc_is_passed',
                'current_chapter','current_section','current_unit']
META_COLS    = ['id','user_id','course_id','username','email','full_name',
                'enrollment_id','mssv','faculty','mode','is_active','created',
                'last_activity','enrollment_date','fetched_at','extracted_at',
                'extraction_batch_id','updated_at','is_passed']
CAT_FEATURES = ['enrollment_mode','enrollment_phase']

CATBOOST_PARAMS = dict(
    iterations=1000, learning_rate=0.05, depth=6,
    l2_leaf_reg=3, loss_function='Logloss', eval_metric='F1',
    auto_class_weights='Balanced', random_seed=42,
    early_stopping_rounds=50, use_best_model=True, verbose=0
)

OUT_DIR = 'results/evaluation_4_2_2'
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs('data', exist_ok=True)

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def load_course_data(conn, course_ids):
    placeholders = ','.join(['%s']*len(course_ids))
    query = f'''
        SELECT sf.*, mg.is_passed
        FROM student_features sf
        LEFT JOIN mooc_grades mg
               ON sf.user_id=mg.user_id AND sf.course_id=mg.course_id
        WHERE sf.course_id IN ({placeholders}) AND mg.is_passed IS NOT NULL
    '''
    df = pd.read_sql(query, conn, params=course_ids)
    return df

def prepare_XY(df):
    drop_cols = [c for c in META_COLS + LEAKAGE_COLS if c in df.columns]
    X = df.drop(columns=drop_cols, errors='ignore')
    y = (~df['is_passed'].astype(bool)).astype(int)  # 1=fail risk
    # fill missing
    for col in X.columns:
        if col in CAT_FEATURES:
            X[col] = X[col].fillna('missing').astype(str)
        else:
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
    cat_idx = [i for i,c in enumerate(X.columns) if c in CAT_FEATURES]
    return X, y, cat_idx

def train_and_eval(X_train, y_train, X_test, y_test, cat_idx, verbose_iters=False):
    train_pool = Pool(X_train, y_train, cat_features=cat_idx)
    test_pool  = Pool(X_test,  y_test,  cat_features=cat_idx)

    params = CATBOOST_PARAMS.copy()
    if verbose_iters:
        params['verbose'] = 100

    model = CatBoostClassifier(**params)
    model.fit(train_pool, eval_set=test_pool)

    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    metrics = dict(
        accuracy  = accuracy_score(y_test, y_pred),
        precision = precision_score(y_test, y_pred, zero_division=0),
        recall    = recall_score(y_test, y_pred, zero_division=0),
        f1        = f1_score(y_test, y_pred, zero_division=0),
        roc_auc   = roc_auc_score(y_test, y_prob),
        pr_auc    = average_precision_score(y_test, y_prob),
        log_loss  = log_loss(y_test, y_prob),
    )
    cm = confusion_matrix(y_test, y_pred)
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    prec_curve, rec_curve, _ = precision_recall_curve(y_test, y_prob)

    # best iteration
    best_iter = model.get_best_iteration()

    return model, metrics, cm, (fpr, tpr), (prec_curve, rec_curve), y_prob, best_iter

# ─── FIGURE: Confusion Matrix 2x2 grid ───────────────────────────────────────
def plot_confusion_matrices(cms, course_names, filename):
    fig, axes = plt.subplots(1, 4, figsize=(18, 4))
    fig.suptitle('Confusion Matrices — Hold-out Test Set (20%)', fontsize=14, fontweight='bold')

    for ax, cm, name in zip(axes, cms, course_names):
        im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
        ax.set_title(name, fontsize=11, fontweight='bold')
        ax.set_xlabel('Predicted Label', fontsize=9)
        ax.set_ylabel('True Label', fontsize=9)
        ax.set_xticks([0,1]); ax.set_yticks([0,1])
        ax.set_xticklabels(['Pass (0)','Fail (1)'], fontsize=8)
        ax.set_yticklabels(['Pass (0)','Fail (1)'], fontsize=8)
        thresh = cm.max() / 2
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f'{cm[i,j]}',
                        ha='center', va='center', fontsize=14, fontweight='bold',
                        color='white' if cm[i,j] > thresh else 'black')
        labels = [['TN','FP'],['FN','TP']]
        for i in range(2):
            for j in range(2):
                ax.text(j, i+0.35, labels[i][j],
                        ha='center', va='center', fontsize=8,
                        color='white' if cm[i,j] > thresh else 'gray')
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {filename}')

# ─── FIGURE: ROC Curves ───────────────────────────────────────────────────────
def plot_roc_curves(roc_data, aucs, course_names, filename):
    colors = ['#2196F3','#4CAF50','#FF9800','#E91E63']
    fig, ax = plt.subplots(figsize=(7, 6))
    for (fpr, tpr), auc, name, color in zip(roc_data, aucs, course_names, colors):
        ax.plot(fpr, tpr, color=color, lw=2.5,
                label=f'{name}  (AUC = {auc:.4f})')
    ax.plot([0,1],[0,1],'k--', lw=1.5, label='Random Classifier')
    ax.set_xlim([0,1]); ax.set_ylim([0,1.01])
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title('ROC Curves — CatBoost (Hold-out Test Set)', fontsize=13, fontweight='bold')
    ax.legend(loc='lower right', fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {filename}')

# ─── FIGURE: PR Curves ────────────────────────────────────────────────────────
def plot_pr_curves(pr_data, pr_aucs, course_names, filename):
    colors = ['#2196F3','#4CAF50','#FF9800','#E91E63']
    fig, ax = plt.subplots(figsize=(7, 6))
    for (prec, rec), pr_auc, name, color in zip(pr_data, pr_aucs, course_names, colors):
        ax.plot(rec, prec, color=color, lw=2.5,
                label=f'{name}  (PR-AUC = {pr_auc:.4f})')
    ax.set_xlim([0,1]); ax.set_ylim([0,1.01])
    ax.set_xlabel('Recall', fontsize=12)
    ax.set_ylabel('Precision', fontsize=12)
    ax.set_title('Precision-Recall Curves — CatBoost (Hold-out Test Set)', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {filename}')

# ─── FIGURE: Training Loss & F1 ───────────────────────────────────────────────
def plot_training_curves(models, course_names, filename):
    colors = ['#2196F3','#4CAF50','#FF9800','#E91E63']
    fig, axes = plt.subplots(1, 4, figsize=(20, 4))
    fig.suptitle('Training Loss & F1 Curves (CatBoost — Early Stopping)', fontsize=14, fontweight='bold')

    for ax, model, name, color in zip(axes, models, course_names, colors):
        evals = model.get_evals_result()
        learn_key = list(evals.keys())[0]
        eval_key  = list(evals.keys())[1] if len(evals) > 1 else learn_key

        learn_loss = evals[learn_key].get('Logloss', [])
        eval_loss  = evals[eval_key].get('Logloss', [])
        learn_f1   = evals[learn_key].get('F1', [])
        eval_f1    = evals[eval_key].get('F1', [])

        iters = range(1, len(learn_loss)+1)

        ax2 = ax.twinx()
        if learn_loss:
            ax.plot(iters, learn_loss, '--', color=color, alpha=0.5, lw=1.5, label='Train Loss')
            ax.plot(iters, eval_loss,  '-',  color=color, lw=2,   label='Val Loss')
        if eval_f1:
            ax2.plot(iters, eval_f1, '-', color='gray', lw=1.5, alpha=0.7, label='Val F1')

        best = model.get_best_iteration()
        if best and learn_loss:
            ax.axvline(x=best, color='red', linestyle=':', lw=2, label=f'Best iter={best}')

        ax.set_title(name, fontsize=10, fontweight='bold')
        ax.set_xlabel('Iteration', fontsize=9)
        ax.set_ylabel('Logloss', fontsize=9, color=color)
        ax2.set_ylabel('F1-Score', fontsize=9, color='gray')
        ax.tick_params(axis='y', labelcolor=color)
        ax2.tick_params(axis='y', labelcolor='gray')
        ax.grid(alpha=0.3)
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1+lines2, labels1+labels2, fontsize=7, loc='upper right')

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {filename}')

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    print('Connecting to database...')
    conn = mysql.connector.connect(**DB_CONFIG)
    print('Connected!\n')

    all_metrics   = {}
    all_cms       = []
    all_roc       = []
    all_pr        = []
    all_roc_aucs  = []
    all_pr_aucs   = []
    all_models    = []
    course_label_list = []

    for course_key, course_ids in COURSES.items():
        label = COURSE_LABELS[course_key]
        print(f'{"="*60}')
        print(f'Processing: {label}')
        print(f'{"="*60}')

        # Load data
        df = load_course_data(conn, course_ids)
        passed = int((df['is_passed']==1).sum())
        failed = int((df['is_passed']==0).sum())
        print(f'  Loaded: {len(df)} students | Pass={passed} ({passed/len(df)*100:.1f}%) | Fail={failed} ({failed/len(df)*100:.1f}%)')

        # Save CSV
        csv_path = f'data/features_{course_key.lower()}_eval.csv'
        df.to_csv(csv_path, index=False)

        # Prepare
        X, y, cat_idx = prepare_XY(df)
        print(f'  Features: {X.shape[1]} | Cat features idx: {cat_idx}')

        # Split 80/20
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y)
        print(f'  Train={len(X_train)} | Test={len(X_test)}')

        # Train & evaluate
        print(f'  Training CatBoost...')
        model, metrics, cm, roc, pr, y_prob, best_iter = train_and_eval(
            X_train, y_train, X_test, y_test, cat_idx, verbose_iters=False)

        print(f'  Best iteration: {best_iter}')
        print(f'  Accuracy : {metrics["accuracy"]:.4f}')
        print(f'  Precision: {metrics["precision"]:.4f}')
        print(f'  Recall   : {metrics["recall"]:.4f}')
        print(f'  F1-Score : {metrics["f1"]:.4f}')
        print(f'  ROC-AUC  : {metrics["roc_auc"]:.4f}')
        print(f'  PR-AUC   : {metrics["pr_auc"]:.4f}')
        print(f'  Log Loss : {metrics["log_loss"]:.4f}')
        print(f'  CM: TN={cm[0,0]} FP={cm[0,1]} FN={cm[1,0]} TP={cm[1,1]}')
        print()

        all_metrics[course_key]  = metrics
        all_cms.append(cm)
        all_roc.append(roc)
        all_pr.append(pr)
        all_roc_aucs.append(metrics['roc_auc'])
        all_pr_aucs.append(metrics['pr_auc'])
        all_models.append(model)
        course_label_list.append(label)

    conn.close()

    # ── Generate Figures ──────────────────────────────────────────────────
    print('\nGenerating figures...')

    plot_confusion_matrices(all_cms, course_label_list,
        f'{OUT_DIR}/figure22_confusion_matrix.png')

    plot_roc_curves(all_roc, all_roc_aucs, course_label_list,
        f'{OUT_DIR}/figure23_roc_curve.png')

    plot_pr_curves(all_pr, all_pr_aucs, course_label_list,
        f'{OUT_DIR}/figure24_pr_curve.png')

    plot_training_curves(all_models, course_label_list,
        f'{OUT_DIR}/figure25_training_curves.png')

    # ── Summary Table ─────────────────────────────────────────────────────
    print('\n' + '='*70)
    print('TABLE 4.9: TEST SET PERFORMANCE METRICS — ALL COURSES')
    print('='*70)
    header = f"{'Course':<10} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'ROC-AUC':>10} {'PR-AUC':>10} {'LogLoss':>10}"
    print(header)
    print('-'*70)
    for k, m in all_metrics.items():
        print(f"{k:<10} {m['accuracy']:>10.4f} {m['precision']:>10.4f} {m['recall']:>10.4f} {m['f1']:>10.4f} {m['roc_auc']:>10.4f} {m['pr_auc']:>10.4f} {m['log_loss']:>10.4f}")

    print('\nConfusion Matrix Details:')
    for course_key, cm in zip(COURSES.keys(), all_cms):
        print(f'  {course_key}: TN={cm[0,0]} FP={cm[0,1]} FN={cm[1,0]} TP={cm[1,1]} | Total={cm.sum()}')

    # Save JSON
    with open(f'{OUT_DIR}/metrics_summary.json', 'w') as f:
        json.dump(all_metrics, f, indent=2)
    print(f'\nMetrics saved to {OUT_DIR}/metrics_summary.json')
    print('\nAll done!')

if __name__ == '__main__':
    main()
