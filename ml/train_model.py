"""
Model Training Module
Train CatBoost model để dự đoán dropout/fail risk
"""
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pickle

# CatBoost
from catboost import CatBoostClassifier, Pool

# Sklearn
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_curve
)

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Setup logging
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f"train_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DropoutModelTrainer:
    """Class để train CatBoost model cho dropout prediction"""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model = None
        self.feature_names = None
        self.categorical_features = None
        
    def prepare_data(
        self, 
        df: pd.DataFrame,
        target_col: str = 'is_passed',
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Chuẩn bị data cho training
        Target: is_passed = False → fail (label = 1), is_passed = True → pass (label = 0)
        """
        logger.info("Preparing training data...")
        
        # Filter out records without target
        df_clean = df[df[target_col].notna()].copy()
        logger.info(f"Records with target: {len(df_clean)}/{len(df)}")
        
        # Create target (1 = fail, 0 = pass)
        # Handle both boolean and numeric (0/1) from CSV
        # Convert: is_passed = 1/True → 0 (pass), is_passed = 0/False → 1 (fail)
        is_passed_values = df_clean[target_col]
        if is_passed_values.dtype == 'object':
            # String boolean: convert "True"/"1" → True, "False"/"0" → False
            is_passed_bool = is_passed_values.astype(str).str.lower().isin(['true', '1', 'yes'])
        else:
            # Numeric: 1 → True, 0 → False
            is_passed_bool = is_passed_values.astype(bool)
        
        # Invert: pass (True) → 0, fail (False) → 1
        y = (~is_passed_bool).astype(int)
        
        logger.info(f"Target distribution - Fail: {y.sum()}, Pass: {(~y.astype(bool)).sum()}")
        
        # Define feature columns
        exclude_cols = [
            # Identity columns
            'id', 'user_id', 'course_id', 'username', 'email', 'full_name',
            
            # Target labels
            'is_passed', 'is_dropout', 'fail_risk_score',
            
            # DATA LEAKAGE COLUMNS - Perfect correlation with target
            'mooc_grade_percentage',  # Final grade - direct leakage!
            'mooc_letter_grade',      # Letter grade - same as above
            'mooc_is_passed',         # This IS the target variable!
            
            # POSITIONAL LEAKAGE - extracted at end-of-course, directly reveals outcome
            'current_chapter',        # Student at last chapter = completed
            'current_section',        # Same positional leakage
            'current_unit',           # Same positional leakage
            
            # Timestamps & metadata
            'extracted_at', 'extraction_batch_id', 'fetched_at', 'updated_at',
            'created', 'enrollment_id', 'all_attributes',
            'enrollment_date', 'last_activity'  # datetime columns
        ]
        
        feature_cols = [col for col in df_clean.columns if col not in exclude_cols]
        X = df_clean[feature_cols].copy()
        
        # Identify categorical features
        self.categorical_features = [
            col for col in X.columns 
            if X[col].dtype == 'object' or col in [
                'enrollment_mode', 'enrollment_phase'
            ]
        ]
        
        logger.info(f"Total features: {len(feature_cols)}")
        logger.info(f"Categorical features: {len(self.categorical_features)}")
        logger.info(f"Numeric features: {len(feature_cols) - len(self.categorical_features)}")
        
        # Handle categorical features
        for col in self.categorical_features:
            if col in X.columns:
                X[col] = X[col].fillna('missing').astype(str)
        
        # Handle numeric features
        numeric_cols = [col for col in X.columns if col not in self.categorical_features]
        X[numeric_cols] = X[numeric_cols].fillna(0)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        logger.info(f"Train set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        logger.info(f"Train fail rate: {y_train.mean():.2%}")
        logger.info(f"Test fail rate: {y_test.mean():.2%}")
        
        self.feature_names = list(X.columns)
        
        return X_train, X_test, y_train, y_test
    
    def train_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame = None,
        y_val: pd.Series = None,
        iterations: int = 1000,
        learning_rate: float = 0.05,
        depth: int = 6,
        l2_leaf_reg: float = 3,
        random_seed: int = 42
    ) -> CatBoostClassifier:
        """Train CatBoost model"""
        logger.info("Training CatBoost model...")
        
        # Create model
        self.model = CatBoostClassifier(
            iterations=iterations,
            learning_rate=learning_rate,
            depth=depth,
            l2_leaf_reg=l2_leaf_reg,
            loss_function='Logloss',
            eval_metric='AUC',
            cat_features=self.categorical_features,
            random_seed=random_seed,
            verbose=100,
            early_stopping_rounds=50,
            use_best_model=True
        )
        
        # Prepare validation set
        eval_set = None
        if X_val is not None and y_val is not None:
            eval_set = (X_val, y_val)
        
        # Train
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=100
        )
        
        logger.info("Model training completed")
        return self.model
    
    def evaluate_model(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """Evaluate model performance"""
        logger.info("Evaluating model...")
        
        # Predictions
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = (y_pred_proba >= 0.5).astype(int)
        
        # Calculate metrics
        metrics = {
            'auc_roc': roc_auc_score(y_test, y_pred_proba),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        
        # Classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        metrics['classification_report'] = report
        
        # Feature importance
        feature_importance = self.model.get_feature_importance()
        feature_importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)
        
        metrics['top_features'] = feature_importance_df.head(20).to_dict('records')
        
        # Log metrics
        logger.info("\n=== Model Evaluation Results ===")
        logger.info(f"AUC-ROC: {metrics['auc_roc']:.4f}")
        logger.info(f"Precision: {metrics['precision']:.4f}")
        logger.info(f"Recall: {metrics['recall']:.4f}")
        logger.info(f"F1-Score: {metrics['f1_score']:.4f}")
        
        logger.info("\nConfusion Matrix:")
        logger.info(f"TN: {cm[0][0]}, FP: {cm[0][1]}")
        logger.info(f"FN: {cm[1][0]}, TP: {cm[1][1]}")
        
        logger.info("\nTop 10 Important Features:")
        for i, row in enumerate(feature_importance_df.head(10).itertuples(), 1):
            logger.info(f"{i}. {row.feature}: {row.importance:.2f}")
        
        return metrics
    
    def save_model(self, model_name: str = "dropout_prediction_model"):
        """Save trained model"""
        if self.model is None:
            logger.error("No model to save")
            return False
        
        try:
            # Save CatBoost model
            model_path = self.model_dir / f"{model_name}.cbm"
            self.model.save_model(str(model_path))
            logger.info(f"Model saved to {model_path}")
            
            # Save metadata
            metadata = {
                'feature_names': self.feature_names,
                'categorical_features': self.categorical_features,
                'model_params': self.model.get_params(),
                'trained_at': datetime.now().isoformat()
            }
            
            metadata_path = self.model_dir / f"{model_name}_metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            logger.info(f"Metadata saved to {metadata_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self, model_name: str = "dropout_prediction_model"):
        """Load trained model"""
        try:
            # Load CatBoost model
            model_path = self.model_dir / f"{model_name}.cbm"
            self.model = CatBoostClassifier()
            self.model.load_model(str(model_path))
            logger.info(f"Model loaded from {model_path}")
            
            # Load metadata
            metadata_path = self.model_dir / f"{model_name}_metadata.pkl"
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.feature_names = metadata['feature_names']
            self.categorical_features = metadata['categorical_features']
            logger.info(f"Metadata loaded from {metadata_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False


def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train Dropout Prediction Model')
    parser.add_argument('--input', type=str, required=True, help='Input features CSV file')
    parser.add_argument('--model-name', type=str, default='dropout_prediction_model', help='Model name')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test set size')
    parser.add_argument('--iterations', type=int, default=1000, help='Number of iterations')
    parser.add_argument('--learning-rate', type=float, default=0.05, help='Learning rate')
    parser.add_argument('--depth', type=int, default=6, help='Tree depth')
    
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading data from {args.input}...")
    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} records")
    
    # Create trainer
    trainer = DropoutModelTrainer()
    
    # Prepare data
    X_train, X_test, y_train, y_test = trainer.prepare_data(
        df, test_size=args.test_size
    )
    
    # Train model
    trainer.train_model(
        X_train, y_train,
        X_val=X_test, y_val=y_test,
        iterations=args.iterations,
        learning_rate=args.learning_rate,
        depth=args.depth
    )
    
    # Evaluate model
    metrics = trainer.evaluate_model(X_test, y_test)
    
    # Save model
    trainer.save_model(args.model_name)
    
    # Save metrics
    metrics_path = Path('models') / f"{args.model_name}_metrics.pkl"
    with open(metrics_path, 'wb') as f:
        pickle.dump(metrics, f)
    logger.info(f"Metrics saved to {metrics_path}")
    
    logger.info("\n=== Training Complete ===")


if __name__ == "__main__":
    main()
