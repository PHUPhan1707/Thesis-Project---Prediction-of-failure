"""
K-Fold Cross-Validation for Dropout Prediction Model
Evaluate model stability and performance across multiple train/test splits
"""
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import pickle
import json

# CatBoost
from catboost import CatBoostClassifier

# Sklearn
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    accuracy_score, confusion_matrix, classification_report
)

# Plotting
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
        logging.FileHandler(LOGS_DIR / f"kfold_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class KFoldModelEvaluator:
    """K-Fold Cross-Validation Evaluator for CatBoost"""
    
    def __init__(self, n_splits: int = 10, random_state: int = 42):
        self.n_splits = n_splits
        self.random_state = random_state
        self.results = []
        self.models = []
        
    def prepare_data(
        self, 
        df: pd.DataFrame,
        target_col: str = 'is_passed'
    ):
        """Prepare data for K-Fold CV"""
        logger.info("Preparing data for K-Fold Cross-Validation...")
        
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
        
        logger.info(f"Target distribution - Fail: {y.sum()} ({y.mean():.2%}), Pass: {(~y.astype(bool)).sum()} ({(~y.astype(bool)).mean():.2%})")
        
        # Define feature columns (same as train_model.py)
        exclude_cols = [
            'id', 'user_id', 'course_id', 'username', 'email', 'full_name',
            'is_passed', 'is_dropout', 'fail_risk_score',
            'mooc_grade_percentage', 'mooc_letter_grade', 'mooc_is_passed',
            'extracted_at', 'extraction_batch_id', 'fetched_at', 'updated_at',
            'created', 'enrollment_id', 'all_attributes',
            'enrollment_date', 'last_activity'
        ]
        
        feature_cols = [col for col in df_clean.columns if col not in exclude_cols]
        X = df_clean[feature_cols].copy()
        
        # Identify categorical features
        self.categorical_features = [
            col for col in X.columns 
            if X[col].dtype == 'object' or col in [
                'enrollment_mode', 'current_chapter', 'current_section', 
                'current_unit', 'mooc_letter_grade', 'enrollment_phase'
            ]
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
        logger.info(f"Categorical features: {len(self.categorical_features)}")
        
        return X, y
    
    def run_kfold_cv(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        iterations: int = 1000,
        learning_rate: float = 0.05,
        depth: int = 6,
        l2_leaf_reg: float = 3,
        save_models: bool = False
    ):
        """Run K-Fold Cross-Validation"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting {self.n_splits}-Fold Cross-Validation")
        logger.info(f"{'='*60}\n")
        
        # Initialize StratifiedKFold
        skf = StratifiedKFold(
            n_splits=self.n_splits, 
            shuffle=True, 
            random_state=self.random_state
        )
        
        # Store results for each fold
        fold_metrics = []
        
        # Iterate through folds
        for fold, (train_idx, test_idx) in enumerate(skf.split(X, y), 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"FOLD {fold}/{self.n_splits}")
            logger.info(f"{'='*60}")
            
            # Split data
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            logger.info(f"Train samples: {len(X_train)} (Fail rate: {y_train.mean():.2%})")
            logger.info(f"Test samples: {len(X_test)} (Fail rate: {y_test.mean():.2%})")
            
            # Create and train model
            model = CatBoostClassifier(
                iterations=iterations,
                learning_rate=learning_rate,
                depth=depth,
                l2_leaf_reg=l2_leaf_reg,
                loss_function='Logloss',
                eval_metric='AUC',
                cat_features=self.categorical_features,
                random_seed=self.random_state + fold,  # Different seed per fold
                verbose=False,  # Reduce output
                early_stopping_rounds=50,
                use_best_model=True
            )
            
            # Train
            logger.info("Training model...")
            model.fit(
                X_train, y_train,
                eval_set=(X_test, y_test),
                verbose=False
            )
            
            # Predictions
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            y_pred = (y_pred_proba >= 0.5).astype(int)
            
            # Calculate metrics
            metrics = {
                'fold': int(fold),
                'train_size': int(len(X_train)),
                'test_size': int(len(X_test)),
                'train_fail_rate': float(y_train.mean()),
                'test_fail_rate': float(y_test.mean()),
                'accuracy': float(accuracy_score(y_test, y_pred)),
                'auc_roc': float(roc_auc_score(y_test, y_pred_proba)),
                'precision': float(precision_score(y_test, y_pred, zero_division=0)),
                'recall': float(recall_score(y_test, y_pred, zero_division=0)),
                'f1_score': float(f1_score(y_test, y_pred, zero_division=0)),
            }
            
            # Confusion matrix
            cm = confusion_matrix(y_test, y_pred)
            metrics['confusion_matrix'] = cm.tolist()
            metrics['tn'] = int(cm[0][0])
            metrics['fp'] = int(cm[0][1])
            metrics['fn'] = int(cm[1][0])
            metrics['tp'] = int(cm[1][1])
            
            # Log fold results
            logger.info(f"\nFold {fold} Results:")
            logger.info(f"  Accuracy:  {metrics['accuracy']:.4f}")
            logger.info(f"  AUC-ROC:   {metrics['auc_roc']:.4f}")
            logger.info(f"  Precision: {metrics['precision']:.4f}")
            logger.info(f"  Recall:    {metrics['recall']:.4f}")
            logger.info(f"  F1-Score:  {metrics['f1_score']:.4f}")
            logger.info(f"  Confusion Matrix: TN={metrics['tn']}, FP={metrics['fp']}, FN={metrics['fn']}, TP={metrics['tp']}")
            
            fold_metrics.append(metrics)
            
            # Save model if requested
            if save_models:
                self.models.append(model)
        
        self.results = fold_metrics
        return fold_metrics
    
    def summarize_results(self):
        """Summarize K-Fold CV results"""
        if not self.results:
            logger.error("No results to summarize. Run K-Fold CV first.")
            return None
        
        logger.info(f"\n{'='*60}")
        logger.info(f"K-FOLD CROSS-VALIDATION SUMMARY ({self.n_splits} folds)")
        logger.info(f"{'='*60}\n")
        
        # Convert to DataFrame for easy analysis
        df_results = pd.DataFrame(self.results)
        
        # Calculate statistics
        summary = {
            'n_folds': int(self.n_splits),
            'total_samples': int(df_results['train_size'].iloc[0] + df_results['test_size'].iloc[0]),
            'avg_train_size': float(df_results['train_size'].mean()),
            'avg_test_size': float(df_results['test_size'].mean()),
        }
        
        # Metrics statistics
        metric_names = ['accuracy', 'auc_roc', 'precision', 'recall', 'f1_score']
        
        for metric in metric_names:
            values = df_results[metric].values
            summary[f'{metric}_mean'] = float(np.mean(values))
            summary[f'{metric}_std'] = float(np.std(values))
            summary[f'{metric}_min'] = float(np.min(values))
            summary[f'{metric}_max'] = float(np.max(values))
        
        # Log summary
        logger.info(f"Total samples: {summary['total_samples']}")
        logger.info(f"Avg train/test split: {summary['avg_train_size']:.0f} / {summary['avg_test_size']:.0f}")
        logger.info("")
        
        logger.info("Model Performance (Mean ± Std):")
        logger.info(f"  Accuracy:  {summary['accuracy_mean']:.4f} ± {summary['accuracy_std']:.4f}")
        logger.info(f"  AUC-ROC:   {summary['auc_roc_mean']:.4f} ± {summary['auc_roc_std']:.4f}")
        logger.info(f"  Precision: {summary['precision_mean']:.4f} ± {summary['precision_std']:.4f}")
        logger.info(f"  Recall:    {summary['recall_mean']:.4f} ± {summary['recall_std']:.4f}")
        logger.info(f"  F1-Score:  {summary['f1_score_mean']:.4f} ± {summary['f1_score_std']:.4f}")
        logger.info("")
        
        logger.info("Performance Range:")
        for metric in metric_names:
            logger.info(f"  {metric.upper()}: [{summary[f'{metric}_min']:.4f}, {summary[f'{metric}_max']:.4f}]")
        
        # Stability assessment
        logger.info("\nModel Stability Assessment:")
        for metric in metric_names:
            std = summary[f'{metric}_std']
            if std < 0.02:
                stability = "Very Stable ✓"
            elif std < 0.05:
                stability = "Stable"
            elif std < 0.10:
                stability = "Moderately Stable"
            else:
                stability = "Unstable ⚠"
            logger.info(f"  {metric.upper()}: {stability} (std={std:.4f})")
        
        return summary
    
    def plot_results(self, save_dir: str = "results"):
        """Create visualization of K-Fold results"""
        if not self.results:
            logger.error("No results to plot. Run K-Fold CV first.")
            return
        
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        df_results = pd.DataFrame(self.results)
        metric_names = ['accuracy', 'auc_roc', 'precision', 'recall', 'f1_score']
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'{self.n_splits}-Fold Cross-Validation Results', fontsize=16, fontweight='bold')
        
        # Plot 1: Metrics across folds
        ax1 = axes[0, 0]
        for metric in metric_names:
            ax1.plot(df_results['fold'], df_results[metric], marker='o', label=metric.upper(), linewidth=2)
        ax1.set_xlabel('Fold', fontsize=12)
        ax1.set_ylabel('Score', fontsize=12)
        ax1.set_title('Metrics Across Folds', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim([0, 1])
        
        # Plot 2: Box plot of metrics
        ax2 = axes[0, 1]
        df_metrics = df_results[metric_names]
        df_metrics.columns = [m.upper() for m in metric_names]
        df_metrics.boxplot(ax=ax2)
        ax2.set_ylabel('Score', fontsize=12)
        ax2.set_title('Metrics Distribution', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim([0, 1])
        
        # Plot 3: Mean ± Std bar chart
        ax3 = axes[0, 2]
        means = [df_results[m].mean() for m in metric_names]
        stds = [df_results[m].std() for m in metric_names]
        x_pos = np.arange(len(metric_names))
        ax3.bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7, color='skyblue', edgecolor='black')
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels([m.upper() for m in metric_names], rotation=45)
        ax3.set_ylabel('Score', fontsize=12)
        ax3.set_title('Mean ± Std', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')
        ax3.set_ylim([0, 1])
        
        # Plot 4: Confusion matrix heatmap (average)
        ax4 = axes[1, 0]
        avg_cm = np.mean([np.array(r['confusion_matrix']) for r in self.results], axis=0)
        sns.heatmap(avg_cm, annot=True, fmt='.1f', cmap='Blues', ax=ax4, 
                   xticklabels=['Pass', 'Fail'], yticklabels=['Pass', 'Fail'])
        ax4.set_title('Average Confusion Matrix', fontsize=14, fontweight='bold')
        ax4.set_ylabel('True Label', fontsize=12)
        ax4.set_xlabel('Predicted Label', fontsize=12)
        
        # Plot 5: Train/Test fail rate
        ax5 = axes[1, 1]
        x = df_results['fold']
        ax5.plot(x, df_results['train_fail_rate']*100, marker='o', label='Train Fail Rate', linewidth=2)
        ax5.plot(x, df_results['test_fail_rate']*100, marker='s', label='Test Fail Rate', linewidth=2)
        ax5.set_xlabel('Fold', fontsize=12)
        ax5.set_ylabel('Fail Rate (%)', fontsize=12)
        ax5.set_title('Train/Test Fail Rate', fontsize=14, fontweight='bold')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        # Plot 6: Metric stability (std comparison)
        ax6 = axes[1, 2]
        stds = [df_results[m].std() for m in metric_names]
        colors = ['green' if s < 0.05 else 'orange' if s < 0.10 else 'red' for s in stds]
        ax6.barh([m.upper() for m in metric_names], stds, color=colors, alpha=0.7, edgecolor='black')
        ax6.set_xlabel('Standard Deviation', fontsize=12)
        ax6.set_title('Metric Stability (Lower = Better)', fontsize=14, fontweight='bold')
        ax6.grid(True, alpha=0.3, axis='x')
        ax6.axvline(x=0.05, color='orange', linestyle='--', alpha=0.5, label='Stable threshold')
        ax6.legend()
        
        plt.tight_layout()
        
        # Save figure
        plot_path = save_path / f"kfold_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        logger.info(f"Results plot saved to {plot_path}")
        
        return fig
    
    def save_results(self, output_dir: str = "results"):
        """Save K-Fold results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed results (JSON)
        results_json = output_path / f"kfold_results_{timestamp}.json"
        with open(results_json, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Detailed results saved to {results_json}")
        
        # Save summary (CSV)
        df_results = pd.DataFrame(self.results)
        results_csv = output_path / f"kfold_results_{timestamp}.csv"
        df_results.to_csv(results_csv, index=False)
        logger.info(f"Results CSV saved to {results_csv}")
        
        # Save summary statistics
        summary = self.summarize_results()
        summary_json = output_path / f"kfold_summary_{timestamp}.json"
        with open(summary_json, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Summary saved to {summary_json}")
        
        return {
            'results_json': str(results_json),
            'results_csv': str(results_csv),
            'summary_json': str(summary_json)
        }


def main():
    """Main K-Fold evaluation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='K-Fold Cross-Validation for Dropout Prediction')
    parser.add_argument('--input', type=str, required=True, help='Input features CSV file')
    parser.add_argument('--n-folds', type=int, default=10, help='Number of folds (default: 10)')
    parser.add_argument('--iterations', type=int, default=1000, help='CatBoost iterations')
    parser.add_argument('--learning-rate', type=float, default=0.05, help='Learning rate')
    parser.add_argument('--depth', type=int, default=6, help='Tree depth')
    parser.add_argument('--output-dir', type=str, default='results', help='Output directory')
    parser.add_argument('--save-models', action='store_true', help='Save all trained models')
    
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading data from {args.input}...")
    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} records")
    
    # Create evaluator
    evaluator = KFoldModelEvaluator(n_splits=args.n_folds)
    
    # Prepare data
    X, y = evaluator.prepare_data(df)
    
    # Run K-Fold CV
    evaluator.run_kfold_cv(
        X, y,
        iterations=args.iterations,
        learning_rate=args.learning_rate,
        depth=args.depth,
        save_models=args.save_models
    )
    
    # Summarize results
    summary = evaluator.summarize_results()
    
    # Plot results
    evaluator.plot_results(save_dir=args.output_dir)
    
    # Save results
    files = evaluator.save_results(output_dir=args.output_dir)
    
    logger.info(f"\n{'='*60}")
    logger.info("K-Fold Cross-Validation Complete!")
    logger.info(f"{'='*60}")
    logger.info(f"Results saved to: {args.output_dir}")
    logger.info(f"  - {files['results_json']}")
    logger.info(f"  - {files['results_csv']}")
    logger.info(f"  - {files['summary_json']}")


if __name__ == "__main__":
    main()
