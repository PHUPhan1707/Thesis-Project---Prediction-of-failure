"""
Model Retraining Script
Retrain model định kỳ với data mới
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ml.feature_engineering import FeatureEngineer
from ml.train_model import DropoutModelTrainer

# Setup logging
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f"retrain_model_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main retraining workflow"""
    logger.info("=" * 60)
    logger.info("Starting Model Retraining Workflow")
    logger.info("=" * 60)
    
    try:
        # Step 1: Feature Engineering
        logger.info("\nStep 1: Creating features from raw data...")
        engineer = FeatureEngineer()
        
        # Load all raw data
        df_raw = engineer.load_raw_data()
        
        if df_raw.empty:
            logger.error("No raw data found. Exiting.")
            return
        
        logger.info(f"Loaded {len(df_raw)} records")
        
        # Create features
        df_features = engineer.create_all_features(df_raw)
        
        # Save features
        features_path = Path("data") / f"features_retrain_{datetime.now().strftime('%Y%m%d')}.csv"
        features_path.parent.mkdir(parents=True, exist_ok=True)
        engineer.save_features(df_features, str(features_path))
        engineer.close_db()
        
        # Step 2: Train Model
        logger.info("\nStep 2: Training new model...")
        
        trainer = DropoutModelTrainer()
        
        # Prepare data
        X_train, X_test, y_train, y_test = trainer.prepare_data(
            df_features, test_size=0.2
        )
        
        # Train model
        trainer.train_model(
            X_train, y_train,
            X_val=X_test, y_val=y_test,
            iterations=1000,
            learning_rate=0.05,
            depth=6
        )
        
        # Evaluate model
        metrics = trainer.evaluate_model(X_test, y_test)
        
        # Save new model with timestamp
        model_name = f"dropout_prediction_model_{datetime.now().strftime('%Y%m%d')}"
        trainer.save_model(model_name)
        
        # Also save as default model (overwrite)
        trainer.save_model("dropout_prediction_model")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("Model Retraining Summary")
        logger.info("=" * 60)
        logger.info(f"Training data: {len(X_train)} samples")
        logger.info(f"Test data: {len(X_test)} samples")
        logger.info(f"AUC-ROC: {metrics['auc_roc']:.4f}")
        logger.info(f"F1-Score: {metrics['f1_score']:.4f}")
        logger.info(f"Model saved as: {model_name}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in retraining workflow: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
