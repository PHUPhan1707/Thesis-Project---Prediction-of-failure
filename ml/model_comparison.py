"""
Model Comparison for Dropout Prediction - Thesis Evaluation
Compare multiple ML models using identical K-fold splits for fair comparison.
Models: Logistic Regression, Random Forest, SVM, XGBoost, CatBoost
"""
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import json
import warnings

# ML Libraries
from catboost import CatBoostClassifier
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    accuracy_score,
)

# Plotting
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Setup logging
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f"model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModelComparisonEvaluator:
    """Compare multiple ML models using identical K-fold splits."""

    def __init__(self, n_splits: int = 10, random_state: int = 42):
        self.n_splits = n_splits
        self.random_state = random_state
        self.fold_results: List[Dict] = []
        self.categorical_features: List[str] = []
        self.feature_names: List[str] = []

    def prepare_data(
        self,
        df: pd.DataFrame,
        target_col: str = 'is_passed'
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for evaluation (same logic as KFoldModelEvaluator)."""
        logger.info("Preparing data for model comparison...")

        # Filter out records without target
        df_clean = df[df[target_col].notna()].copy()
        logger.info(f"Records with target: {len(df_clean)}/{len(df)}")

        # Create target (1 = fail, 0 = pass)
        is_passed_values = df_clean[target_col]
        if is_passed_values.dtype == 'object':
            is_passed_bool = is_passed_values.astype(str).str.lower().isin(['true', '1', 'yes'])
        else:
            is_passed_bool = is_passed_values.astype(bool)

        y = (~is_passed_bool).astype(int)

        logger.info(
            f"Target distribution - Fail: {y.sum()} ({y.mean():.2%}), "
            f"Pass: {(~y.astype(bool)).sum()} ({(~y.astype(bool)).mean():.2%})"
        )

        # Define feature columns (same exclusions as kfold_evaluation.py)
        exclude_cols = [
            'id', 'user_id', 'course_id', 'username', 'email', 'full_name',
            'is_passed', 'is_dropout', 'fail_risk_score',
            'mooc_grade_percentage', 'mooc_letter_grade', 'mooc_is_passed',
            'current_chapter', 'current_section', 'current_unit',
            'extracted_at', 'extraction_batch_id', 'fetched_at', 'updated_at',
            'created', 'enrollment_id', 'all_attributes',
            'enrollment_date', 'last_activity'
        ]

        feature_cols = [col for col in df_clean.columns if col not in exclude_cols]
        X = df_clean[feature_cols].copy()

        # Identify categorical features
        self.categorical_features = [
            col for col in X.columns
            if X[col].dtype == 'object' or col in ['enrollment_mode', 'enrollment_phase']
        ]

        # Handle categorical features
        for col in self.categorical_features:
            if col in X.columns:
                X[col] = X[col].fillna('missing').astype(str)

        # Handle numeric features
        numeric_cols = [col for col in X.columns if col not in self.categorical_features]
        X[numeric_cols] = X[numeric_cols].fillna(0)

        self.feature_names = list(X.columns)
        logger.info(f"Total features: {len(self.feature_names)}")
        logger.info(f"Categorical features: {self.categorical_features}")

        return X, y

    def _get_models(self) -> Dict:
        """Return configured model instances."""
        return {
            'Logistic Regression': LogisticRegression(
                max_iter=1000,
                random_state=self.random_state,
                solver='lbfgs',
                C=1.0,
            ),
            'Random Forest': RandomForestClassifier(
                n_estimators=500,
                max_depth=10,
                random_state=self.random_state,
                n_jobs=-1,
            ),
            'SVM': SVC(
                kernel='rbf',
                C=1.0,
                gamma='scale',
                probability=True,
                random_state=self.random_state,
            ),
            'XGBoost': XGBClassifier(
                n_estimators=1000,
                learning_rate=0.05,
                max_depth=6,
                random_state=self.random_state,
                eval_metric='logloss',
                enable_categorical=False,
                verbosity=0,
            ),
            'CatBoost': CatBoostClassifier(
                iterations=1000,
                learning_rate=0.05,
                depth=6,
                l2_leaf_reg=3,
                loss_function='Logloss',
                eval_metric='AUC',
                random_seed=self.random_state,
                verbose=False,
            ),
        }

    # Models that need feature scaling
    NEEDS_SCALING = {'Logistic Regression', 'SVM'}

    def _preprocess_fold(
        self,
        model_name: str,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess features per model type for a single fold.

        Returns numpy arrays ready for fitting.
        """
        cat_cols = self.categorical_features
        num_cols = [c for c in X_train.columns if c not in cat_cols]

        if model_name == 'CatBoost':
            # CatBoost handles categoricals natively - return DataFrames as-is
            return X_train.copy(), X_test.copy()

        # For all other sklearn/xgboost models: ordinal-encode categoricals
        enc = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)

        X_train_cat = enc.fit_transform(X_train[cat_cols]) if cat_cols else np.empty((len(X_train), 0))
        X_test_cat = enc.transform(X_test[cat_cols]) if cat_cols else np.empty((len(X_test), 0))

        X_train_num = X_train[num_cols].values
        X_test_num = X_test[num_cols].values

        if model_name in self.NEEDS_SCALING:
            scaler = StandardScaler()
            X_train_num = scaler.fit_transform(X_train_num)
            X_test_num = scaler.transform(X_test_num)

        X_train_out = np.hstack([X_train_num, X_train_cat])
        X_test_out = np.hstack([X_test_num, X_test_cat])

        return X_train_out, X_test_out

    def run_comparison(self, X: pd.DataFrame, y: pd.Series) -> List[Dict]:
        """Run all models on identical K-fold splits."""
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Starting Model Comparison ({self.n_splits}-Fold CV, 5 models)")
        logger.info(f"{'=' * 60}\n")

        # Store for summarize_comparison dataset_info
        self._total_samples = len(y)
        self._fail_rate = float(y.mean())

        skf = StratifiedKFold(
            n_splits=self.n_splits,
            shuffle=True,
            random_state=self.random_state,
        )
        folds = list(skf.split(X, y))

        models_dict = self._get_models()
        self.fold_results = []

        for model_name, model_template in models_dict.items():
            logger.info(f"\n{'=' * 60}")
            logger.info(f"  MODEL: {model_name}")
            logger.info(f"{'=' * 60}")

            for fold_idx, (train_idx, test_idx) in enumerate(folds):
                fold_num = fold_idx + 1
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

                # Preprocess per model type
                X_tr_proc, X_te_proc = self._preprocess_fold(model_name, X_train, X_test)

                # Clone model for this fold
                from sklearn.base import clone
                if model_name == 'CatBoost':
                    model = CatBoostClassifier(
                        **model_template.get_params(),
                        cat_features=self.categorical_features,
                        early_stopping_rounds=50,
                        use_best_model=True,
                    )
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        model.fit(X_tr_proc, y_train, eval_set=(X_te_proc, y_test), verbose=False)
                elif model_name == 'XGBoost':
                    model = clone(model_template)
                    model.set_params(early_stopping_rounds=50)
                    model.fit(
                        X_tr_proc, y_train,
                        eval_set=[(X_te_proc, y_test)],
                        verbose=False,
                    )
                else:
                    model = clone(model_template)
                    model.fit(X_tr_proc, y_train)

                # Predict
                y_pred_proba = model.predict_proba(X_te_proc)[:, 1]
                y_pred = (y_pred_proba >= 0.5).astype(int)

                # Metrics
                metrics = {
                    'model': model_name,
                    'fold': fold_num,
                    'accuracy': float(accuracy_score(y_test, y_pred)),
                    'auc_roc': float(roc_auc_score(y_test, y_pred_proba)),
                    'precision': float(precision_score(y_test, y_pred, zero_division=0)),
                    'recall': float(recall_score(y_test, y_pred, zero_division=0)),
                    'f1_score': float(f1_score(y_test, y_pred, zero_division=0)),
                }
                self.fold_results.append(metrics)

                logger.info(
                    f"  Fold {fold_num:2d} | AUC={metrics['auc_roc']:.4f}  "
                    f"Acc={metrics['accuracy']:.4f}  F1={metrics['f1_score']:.4f}"
                )

            # Log model average
            model_metrics = [r for r in self.fold_results if r['model'] == model_name]
            avg_auc = np.mean([r['auc_roc'] for r in model_metrics])
            avg_f1 = np.mean([r['f1_score'] for r in model_metrics])
            logger.info(f"  >>> {model_name} AVG: AUC={avg_auc:.4f}, F1={avg_f1:.4f}")

        return self.fold_results

    def summarize_comparison(self) -> Dict:
        """Produce comparison summary table."""
        if not self.fold_results:
            logger.error("No results. Run run_comparison() first.")
            return {}

        df = pd.DataFrame(self.fold_results)
        metric_names = ['accuracy', 'auc_roc', 'precision', 'recall', 'f1_score']
        model_names = df['model'].unique()

        summary: Dict = {'models': {}, 'best_model': {}, 'dataset_info': {}}

        for model_name in model_names:
            model_df = df[df['model'] == model_name]
            model_stats = {}
            for m in metric_names:
                model_stats[f'{m}_mean'] = float(model_df[m].mean())
                model_stats[f'{m}_std'] = float(model_df[m].std())
            summary['models'][model_name] = model_stats

        # Determine best model per metric
        for m in metric_names:
            best_name = max(
                summary['models'],
                key=lambda name: summary['models'][name][f'{m}_mean']
            )
            summary['best_model'][f'by_{m}'] = best_name

        # Dataset info
        summary['dataset_info'] = {
            'total_samples': getattr(self, '_total_samples', None),
            'n_features': len(self.feature_names),
            'fail_rate': round(getattr(self, '_fail_rate', 0), 4),
            'n_folds': self.n_splits,
        }

        # Log comparison table
        logger.info(f"\n{'=' * 80}")
        logger.info("MODEL COMPARISON SUMMARY")
        logger.info(f"{'=' * 80}")
        header = f"{'Model':<25}" + "".join(f"{m.upper():>14}" for m in metric_names)
        logger.info(header)
        logger.info("-" * 80)
        for model_name in model_names:
            s = summary['models'][model_name]
            row = f"{model_name:<25}"
            for m in metric_names:
                row += f"  {s[f'{m}_mean']:.4f}±{s[f'{m}_std']:.3f}"
            logger.info(row)
        logger.info("-" * 80)
        logger.info(f"Best by AUC-ROC: {summary['best_model']['by_auc_roc']}")
        logger.info(f"Best by F1:      {summary['best_model']['by_f1_score']}")

        return summary

    def plot_comparison(self, save_dir: str = "results/model_comparison"):
        """Generate thesis-quality comparison plots."""
        if not self.fold_results:
            logger.error("No results to plot.")
            return

        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        df = pd.DataFrame(self.fold_results)
        metric_names = ['accuracy', 'auc_roc', 'precision', 'recall', 'f1_score']
        metric_labels = ['Accuracy', 'AUC-ROC', 'Precision', 'Recall', 'F1-Score']
        model_names = list(df['model'].unique())

        # ── 1. Grouped bar chart (main thesis figure) ──
        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(metric_names))
        width = 0.15
        colors = ['#4C72B0', '#55A868', '#C44E52', '#8172B2', '#CCB974']

        for i, model_name in enumerate(model_names):
            model_df = df[df['model'] == model_name]
            means = [model_df[m].mean() for m in metric_names]
            stds = [model_df[m].std() for m in metric_names]
            offset = (i - len(model_names) / 2 + 0.5) * width
            bars = ax.bar(x + offset, means, width, yerr=stds, capsize=3,
                          label=model_name, color=colors[i], edgecolor='white', linewidth=0.5)
            # Add value labels on bars
            for bar, mean in zip(bars, means):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                        f'{mean:.3f}', ha='center', va='bottom', fontsize=7, rotation=0)

        ax.set_xticks(x)
        ax.set_xticklabels(metric_labels, fontsize=11)
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title('Model Comparison - All Metrics (10-Fold CV)', fontsize=14, fontweight='bold')
        ax.set_ylim([0, 1.12])
        ax.legend(loc='lower right', fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        chart_path = save_path / f"comparison_chart_{timestamp}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Grouped bar chart saved: {chart_path}")

        # ── 2. Box plots per metric ──
        fig, axes = plt.subplots(1, 5, figsize=(20, 5), sharey=True)
        for idx, (m, label) in enumerate(zip(metric_names, metric_labels)):
            ax = axes[idx]
            data_for_box = [df[df['model'] == mn][m].values for mn in model_names]
            bp = ax.boxplot(data_for_box, labels=model_names, patch_artist=True, widths=0.6)
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            ax.set_title(label, fontsize=12, fontweight='bold')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3, axis='y')
            if idx == 0:
                ax.set_ylabel('Score', fontsize=11)

        fig.suptitle('Metric Distribution by Model (10-Fold CV)', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        box_path = save_path / f"comparison_boxplot_{timestamp}.png"
        plt.savefig(box_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Box plot saved: {box_path}")

        # ── 3. Radar / Spider chart ──
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        angles = np.linspace(0, 2 * np.pi, len(metric_names), endpoint=False).tolist()
        angles += angles[:1]  # close polygon

        for i, model_name in enumerate(model_names):
            model_df = df[df['model'] == model_name]
            values = [model_df[m].mean() for m in metric_names]
            values += values[:1]
            ax.plot(angles, values, 'o-', linewidth=2, label=model_name, color=colors[i])
            ax.fill(angles, values, alpha=0.1, color=colors[i])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels, fontsize=10)
        ax.set_ylim([0, 1.0])
        ax.set_title('Model Profiles', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
        plt.tight_layout()
        radar_path = save_path / f"comparison_radar_{timestamp}.png"
        plt.savefig(radar_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Radar chart saved: {radar_path}")

        # ── 4. Heatmap ──
        fig, ax = plt.subplots(figsize=(10, 5))
        heatmap_data = []
        for model_name in model_names:
            model_df = df[df['model'] == model_name]
            heatmap_data.append([model_df[m].mean() for m in metric_names])
        heatmap_df = pd.DataFrame(heatmap_data, index=model_names, columns=metric_labels)

        sns.heatmap(heatmap_df, annot=True, fmt='.4f', cmap='YlGnBu', ax=ax,
                    linewidths=0.5, vmin=0.5, vmax=1.0, cbar_kws={'label': 'Score'})
        ax.set_title('Model x Metric Heatmap (Mean Scores)', fontsize=14, fontweight='bold')
        ax.set_ylabel('')
        plt.tight_layout()
        heatmap_path = save_path / f"comparison_heatmap_{timestamp}.png"
        plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Heatmap saved: {heatmap_path}")

    def save_results(self, output_dir: str = "results/model_comparison") -> Dict:
        """Save comparison results to JSON and CSV."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 1. Detailed per-fold results CSV
        details_csv = output_path / f"comparison_details_{timestamp}.csv"
        pd.DataFrame(self.fold_results).to_csv(details_csv, index=False)
        logger.info(f"Details CSV saved: {details_csv}")

        # 2. Summary JSON
        summary = self.summarize_comparison()
        summary_json = output_path / f"comparison_summary_{timestamp}.json"
        with open(summary_json, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Summary JSON saved: {summary_json}")

        return {
            'details_csv': str(details_csv),
            'summary_json': str(summary_json),
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Model Comparison for Dropout Prediction (Thesis)')
    parser.add_argument('--input', type=str, required=True, help='Input features CSV file')
    parser.add_argument('--output-dir', type=str, default='results/model_comparison', help='Output directory')
    parser.add_argument('--n-folds', type=int, default=10, help='Number of CV folds (default: 10)')
    args = parser.parse_args()

    logger.info(f"Loading data from {args.input}...")
    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} records")

    evaluator = ModelComparisonEvaluator(n_splits=args.n_folds)

    X, y = evaluator.prepare_data(df)

    evaluator.run_comparison(X, y)

    summary = evaluator.summarize_comparison()

    evaluator.plot_comparison(save_dir=args.output_dir)

    files = evaluator.save_results(output_dir=args.output_dir)

    logger.info(f"\n{'=' * 60}")
    logger.info("Model Comparison Complete!")
    logger.info(f"{'=' * 60}")
    logger.info(f"Output directory: {args.output_dir}")
    for key, path in files.items():
        logger.info(f"  - {path}")


if __name__ == "__main__":
    main()
