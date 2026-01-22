"""
Feature Engineering Module
Tạo derived features từ raw data để train model
"""
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import mysql.connector
from mysql.connector import Error

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Setup logging
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f"feature_engineering_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 4000,
    "database": "dropout_prediction_db",
    "user": "dropout_user",
    "password": "dropout_pass_123"
}


class FeatureEngineer:
    """Class để tạo derived features từ raw data"""
    
    def __init__(self):
        self.connection = None
    
    def connect_db(self):
        """Kết nối database"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            logger.info("Connected to database successfully")
            return True
        except Error as e:
            logger.error(f"Error connecting to database: {e}")
            return False
    
    def close_db(self):
        """Đóng kết nối"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
    
    def load_raw_data(self, course_id: Optional[str] = None) -> pd.DataFrame:
        """Load raw data từ database"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect_db():
                return pd.DataFrame()
        
        try:
            query = "SELECT * FROM raw_data"
            params = None
            
            if course_id:
                query += " WHERE course_id = %s"
                params = (course_id,)
            
            df = pd.read_sql(query, self.connection, params=params)
            logger.info(f"Loaded {len(df)} records from raw_data")
            return df
            
        except Error as e:
            logger.error(f"Error loading raw data: {e}")
            return pd.DataFrame()
    
    def create_engagement_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Tạo engagement score từ nhiều metrics
        Công thức: weighted average của discussion, video, h5p, quiz
        """
        logger.info("Creating engagement score...")
        
        # Normalize các metrics về scale 0-100
        df['discussion_score'] = (
            df['discussion_total_interactions'] / 
            df.groupby('course_id')['discussion_total_interactions'].transform('max').replace(0, 1) * 100
        )
        
        df['video_score'] = df['video_completion_rate']
        df['h5p_score'] = df['h5p_completion_rate']
        df['quiz_score'] = df['quiz_avg_score']
        
        # Weighted average
        df['engagement_score'] = (
            df['discussion_score'] * 0.25 +
            df['video_score'] * 0.25 +
            df['h5p_score'] * 0.25 +
            df['quiz_score'] * 0.25
        )
        
        # Fill NaN với 0
        df['engagement_score'] = df['engagement_score'].fillna(0)
        
        logger.info("Engagement score created")
        return df
    
    def create_activity_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tạo activity-related features"""
        logger.info("Creating activity features...")
        
        # Activity recency (inverse of days_since_last_activity)
        df['activity_recency'] = 100 - (df['days_since_last_activity'] / 30 * 100).clip(0, 100)
        
        # Activity consistency (based on engagement and recency)
        df['activity_consistency'] = (df['engagement_score'] + df['activity_recency']) / 2
        
        # Is inactive (không hoạt động > 7 ngày)
        df['is_inactive'] = (df['days_since_last_activity'] > 7).astype(int)
        
        # Is highly inactive (không hoạt động > 14 ngày)
        df['is_highly_inactive'] = (df['days_since_last_activity'] > 14).astype(int)
        
        logger.info("Activity features created")
        return df
    
    def create_performance_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tạo performance-related features (NO GRADE to avoid leakage)"""
        logger.info("Creating performance features...")
        
        # ⚠️ REMOVED: relative_grade (uses mooc_grade_percentage - DATA LEAKAGE!)
        # ⚠️ REMOVED: performance_gap (uses mooc_grade_percentage - DATA LEAKAGE!)
        # ⚠️ REMOVED: is_at_risk based on grade (DATA LEAKAGE!)
        
        # Relative completion (so với trung bình lớp) - OK, no leakage
        df['relative_completion'] = (
            df['mooc_completion_rate'] - 
            df.groupby('course_id')['mooc_completion_rate'].transform('mean')
        )
        
        # Is struggling based on COMPLETION only (not grade)
        df['is_struggling'] = (
            (df['mooc_completion_rate'] < 50) |
            (df['video_completion_rate'] < 50) |
            (df['h5p_completion_rate'] < 50)
        ).astype(int)
        
        # Is at_risk based on COMPLETION (not grade)
        df['is_at_risk'] = (df['mooc_completion_rate'] < 40).astype(int)
        
        # NEW: Completion consistency across different types
        df['completion_consistency'] = df[['mooc_completion_rate', 'video_completion_rate', 'h5p_completion_rate']].std(axis=1)
        
        logger.info("Performance features created (without grade leakage)")
        return df
    
    def create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tạo interaction-related features"""
        logger.info("Creating interaction features...")
        
        # Discussion engagement rate
        df['discussion_engagement_rate'] = (
            df['discussion_total_interactions'] / 
            df.groupby('course_id')['discussion_total_interactions'].transform('mean').replace(0, 1)
        )
        
        # Has no discussion (không tương tác forum)
        df['has_no_discussion'] = (df['discussion_total_interactions'] == 0).astype(int)
        
        # Video engagement rate
        df['video_engagement_rate'] = df['video_completion_rate'] / 100
        
        # H5P engagement rate
        df['h5p_engagement_rate'] = df['h5p_completion_rate'] / 100
        
        # Overall interaction score
        df['interaction_score'] = (
            df['discussion_engagement_rate'] * 0.4 +
            df['video_engagement_rate'] * 0.3 +
            df['h5p_engagement_rate'] * 0.3
        ) * 100
        
        logger.info("Interaction features created")
        return df
    
    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tạo time-related features"""
        logger.info("Creating time features...")
        
        # Weeks since enrollment bins
        df['enrollment_phase'] = pd.cut(
            df['weeks_since_enrollment'],
            bins=[0, 2, 4, 8, 12, float('inf')],
            labels=['very_early', 'early', 'mid', 'late', 'very_late']
        )
        
        # Time pressure (weeks remaining if course is 16 weeks)
        df['weeks_remaining'] = (16 - df['weeks_since_enrollment']).clip(0, 16)
        
        # Progress rate (completion per week)
        df['progress_rate'] = (
            df['mooc_completion_rate'] / 
            df['weeks_since_enrollment'].replace(0, 1)
        )
        
        logger.info("Time features created")
        return df
    
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tạo tất cả derived features"""
        logger.info("Creating all derived features...")
        
        # Create features
        df = self.create_engagement_score(df)
        df = self.create_activity_features(df)
        df = self.create_performance_features(df)
        df = self.create_interaction_features(df)
        df = self.create_time_features(df)
        
        # Fill NaN values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        logger.info(f"All features created. Total columns: {len(df.columns)}")
        return df
    
    def save_features(self, df: pd.DataFrame, output_path: str):
        """Save features to CSV"""
        try:
            df.to_csv(output_path, index=False)
            logger.info(f"Features saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving features: {e}")
            return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Feature Engineering for Dropout Prediction')
    parser.add_argument('--course-id', type=str, help='Course ID to process (optional, processes all if not specified)')
    parser.add_argument('--output', type=str, default='data/features.csv', help='Output CSV file path')
    
    args = parser.parse_args()
    
    # Create feature engineer
    engineer = FeatureEngineer()
    
    try:
        # Load raw data
        logger.info("Loading raw data...")
        df = engineer.load_raw_data(args.course_id)
        
        if df.empty:
            logger.error("No data loaded. Exiting.")
            return
        
        logger.info(f"Loaded {len(df)} records")
        
        # Create features
        df_features = engineer.create_all_features(df)
        
        # Save features
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        engineer.save_features(df_features, str(output_path))
        
        # Print summary
        logger.info("\n=== Feature Engineering Summary ===")
        logger.info(f"Total records: {len(df_features)}")
        logger.info(f"Total features: {len(df_features.columns)}")
        logger.info(f"Output file: {output_path}")
        
        # Print feature statistics
        logger.info("\n=== Key Feature Statistics ===")
        key_features = [
            'engagement_score', 'activity_recency', 'relative_grade',
            'interaction_score', 'progress_rate', 'is_at_risk'
        ]
        
        for feature in key_features:
            if feature in df_features.columns:
                logger.info(f"{feature}: mean={df_features[feature].mean():.2f}, std={df_features[feature].std():.2f}")
        
    finally:
        engineer.close_db()


if __name__ == "__main__":
    main()
