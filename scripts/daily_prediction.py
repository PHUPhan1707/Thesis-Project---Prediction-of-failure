"""
Daily Prediction Script
Chạy predictions hàng ngày cho tất cả courses
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ml.feature_engineering import FeatureEngineer
from ml.predict import DropoutPredictor

# Setup logging
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f"daily_prediction_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main daily prediction workflow"""
    logger.info("=" * 60)
    logger.info("Starting Daily Prediction Workflow")
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
        features_path = Path("data") / f"features_{datetime.now().strftime('%Y%m%d')}.csv"
        features_path.parent.mkdir(parents=True, exist_ok=True)
        engineer.save_features(df_features, str(features_path))
        engineer.close_db()
        
        # Step 2: Predictions
        logger.info("\nStep 2: Running predictions...")
        
        # Get unique courses
        courses = df_features['course_id'].unique()
        logger.info(f"Found {len(courses)} courses")
        
        # Create predictor
        predictor = DropoutPredictor()
        
        total_students = 0
        total_high_risk = 0
        
        for course_id in courses:
            logger.info(f"\nProcessing course: {course_id}")
            
            # Filter course data
            df_course = df_features[df_features['course_id'] == course_id].copy()
            
            # Predict
            predictions_df = predictor.predict_course(course_id, df_course)
            
            # Save to database
            predictor.save_predictions(predictions_df)
            
            # Update stats
            total_students += len(predictions_df)
            total_high_risk += (predictions_df['risk_level'] == 'HIGH').sum()
            
            # Save course predictions
            course_output = Path("data") / "predictions" / f"{course_id}_{datetime.now().strftime('%Y%m%d')}.csv"
            course_output.parent.mkdir(parents=True, exist_ok=True)
            predictions_df.to_csv(course_output, index=False)
            logger.info(f"Saved predictions to {course_output}")
        
        predictor.close_db()
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("Daily Prediction Summary")
        logger.info("=" * 60)
        logger.info(f"Total courses processed: {len(courses)}")
        logger.info(f"Total students: {total_students}")
        logger.info(f"High risk students: {total_high_risk} ({total_high_risk/total_students*100:.1f}%)")
        logger.info(f"Features saved to: {features_path}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in daily prediction workflow: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
