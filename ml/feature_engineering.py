"""
Feature Engineering Module
Tạo derived features từ raw data để train model
"""
import os
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

# Load .env từ thư mục gốc project (2 levels lên từ ml/)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
        # logger chưa khởi tạo ở đây, dùng print tạm
        print(f"[feature_engineering] Loaded .env from {_env_path}")
    else:
        print(f"[feature_engineering] WARNING: .env not found at {_env_path}")
except ImportError:
    print("[feature_engineering] WARNING: python-dotenv not installed. Install with: pip install python-dotenv")

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

# Database configuration — đọc từ environment variables (set bởi .env)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "4000")),
    "database": os.getenv("DB_NAME", "dropout_prediction_db"),
    "user": os.getenv("DB_USER", "dropout_user"),
    "password": os.getenv("DB_PASSWORD", ""),  # Không có default password
}

# Cảnh báo nếu password rỗng
if not DB_CONFIG["password"]:
    logger.warning(
        "DB_PASSWORD is not set! "
        "Please set DB_PASSWORD in your .env file or as an environment variable."
    )


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
    
    # Ngưỡng tối thiểu tương tác discussion để đạt 100%
    # Giúp tránh discussion_score = 100 khi khóa chỉ có 1 sinh viên
    # (vì groupby max sẽ = chính giá trị đó → score luôn = 100)
    _DISCUSSION_MIN_DENOMINATOR = 10

    def create_engagement_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Tạo engagement score từ nhiều metrics.
        Công thức: weighted average của discussion, video, h5p, quiz.

        Dùng clip(lower=_DISCUSSION_MIN_DENOMINATOR) để tránh discussion_score = 100
        khi khóa học chỉ có 1 sinh viên (single-batch inference edge case).
        """
        logger.info("Creating engagement score...")

        # Normalize discussion: tối thiểu _DISCUSSION_MIN_DENOMINATOR tương tác = 100%
        # clip(lower=N) đảm bảo denominator luôn >= N, tránh 1-student artifact
        course_max_discussion = (
            df.groupby('course_id')['discussion_total_interactions']
            .transform('max')
            .clip(lower=self._DISCUSSION_MIN_DENOMINATOR)
        )
        df['discussion_score'] = (
            df['discussion_total_interactions'] / course_max_discussion * 100
        ).clip(0, 100)

        df['video_score'] = df['video_completion_rate']
        df['h5p_score'] = df['h5p_completion_rate']
        df['quiz_score'] = df['quiz_avg_score']

        df['engagement_score'] = (
            df['discussion_score'] * 0.25 +
            df['video_score'] * 0.25 +
            df['h5p_score'] * 0.25 +
            df['quiz_score'] * 0.25
        ).fillna(0)

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
        
        # Discussion engagement rate (chuẩn hóa theo mean lớp, floor = 5 để tránh
        # single-student artifact tương tự discussion_score)
        course_mean_discussion = (
            df.groupby('course_id')['discussion_total_interactions']
            .transform('mean')
            .clip(lower=5)
        )
        df['discussion_engagement_rate'] = (
            df['discussion_total_interactions'] / course_mean_discussion
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
        """Tạo time-related features cho open course (không có số tuần cố định).

        Vì khóa học là open-ended (không có deadline), weeks_remaining không có
        ý nghĩa thực tế. Thay vào đó dùng các features phản ánh tốc độ và
        chất lượng học tập tương đối so với thời gian đã đăng ký.
        """
        logger.info("Creating time features (open course mode)...")

        weeks = df['weeks_since_enrollment'].replace(0, 1)

        # Enrollment phase: mô tả sinh viên đang ở giai đoạn nào của quá trình học.
        # Bins tuyệt đối theo tuần — vẫn có nghĩa cho open course:
        # very_early (0-2w), early (2-4w), mid (4-8w), late (8-12w), very_late (>12w)
        df['enrollment_phase'] = pd.cut(
            df['weeks_since_enrollment'],
            bins=[0, 2, 4, 8, 12, float('inf')],
            labels=['very_early', 'early', 'mid', 'late', 'very_late']
        )

        # Progress rate: % hoàn thành / tuần đã học
        # Cao → học nhanh; thấp → học chậm hoặc bỏ bê
        df['progress_rate'] = df['mooc_completion_rate'] / weeks

        # Learning pace score: tốc độ học trên thang log (triệt tiêu ảnh hưởng
        # của sinh viên đăng ký rất lâu nhưng không học gì).
        # Công thức: completion / log2(weeks + 1)  →  range [0, ~100]
        df['learning_pace_score'] = (
            df['mooc_completion_rate'] / np.log2(weeks + 1)
        ).clip(0, 200)

        # weeks_remaining = 0 cho open course (không có deadline).
        # Giá trị này nhất quán với training data khi model đã thấy sinh viên
        # có weeks_since_enrollment lớn (weeks_remaining tự nhiên = 0 sau clipping).
        df['weeks_remaining'] = 0

        logger.info("Time features created (open course: weeks_remaining=0, added learning_pace_score)")
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
            'engagement_score', 'activity_recency', 'relative_completion',
            'interaction_score', 'progress_rate', 'is_at_risk'
        ]
        
        for feature in key_features:
            if feature in df_features.columns:
                logger.info(f"{feature}: mean={df_features[feature].mean():.2f}, std={df_features[feature].std():.2f}")
        
    finally:
        engineer.close_db()


if __name__ == "__main__":
    main()
