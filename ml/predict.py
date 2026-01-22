"""
Prediction Module
Sử dụng trained model để predict fail risk cho sinh viên
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

from ml.train_model import DropoutModelTrainer

# Setup logging
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f"predict_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
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


class DropoutPredictor:
    """Class để predict fail risk cho sinh viên"""
    
    def __init__(self, model_name: str = "dropout_prediction_model"):
        self.trainer = DropoutModelTrainer()
        self.model_name = model_name
        self.connection = None
        
        # Load model
        if not self.trainer.load_model(model_name):
            raise ValueError(f"Failed to load model: {model_name}")
    
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
    
    def classify_risk_level(self, risk_score: float) -> str:
        """Phân loại risk level dựa trên risk score"""
        if risk_score >= 70:
            return 'HIGH'
        elif risk_score >= 40:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def generate_suggestions(self, student_data: Dict) -> List[str]:
        """Tạo gợi ý can thiệp dựa trên student data"""
        suggestions = []
        
        # Check inactivity
        if student_data.get('days_since_last_activity', 0) > 7:
            suggestions.append("📧 Gửi email nhắc nhở sinh viên quay lại học")
        
        if student_data.get('days_since_last_activity', 0) > 14:
            suggestions.append("📞 Liên hệ trực tiếp qua điện thoại hoặc tin nhắn")
        
        # Check grade
        if student_data.get('mooc_grade_percentage', 100) < 40:
            suggestions.append("👨‍🏫 Tổ chức buổi ôn tập hoặc tư vấn 1-1")
            suggestions.append("📚 Cung cấp tài liệu học tập bổ sung")
        
        # Check completion rate
        if student_data.get('mooc_completion_rate', 100) < 30:
            suggestions.append("⏰ Nhắc nhở về deadline và lộ trình học tập")
        
        # Check discussion participation
        if student_data.get('discussion_total_interactions', 1) == 0:
            suggestions.append("💬 Khuyến khích tham gia thảo luận forum")
            suggestions.append("👥 Ghép nhóm học tập với sinh viên khác")
        
        # Check video completion
        if student_data.get('video_completion_rate', 100) < 30:
            suggestions.append("🎥 Kiểm tra xem video có vấn đề kỹ thuật không")
            suggestions.append("📝 Cung cấp transcript hoặc tài liệu thay thế")
        
        # Check quiz performance
        if student_data.get('quiz_avg_score', 100) < 50:
            suggestions.append("✍️ Tổ chức buổi giải đáp thắc mắc về quiz")
            suggestions.append("📖 Cung cấp bài tập luyện tập thêm")
        
        # General high risk
        if student_data.get('fail_risk_score', 0) >= 70:
            suggestions.append("🚨 Ưu tiên can thiệp ngay - Nguy cơ rất cao")
            suggestions.append("📊 Lập kế hoạch học tập cá nhân hóa")
        
        return suggestions if suggestions else ["✅ Sinh viên đang học tốt, tiếp tục theo dõi"]
    
    def predict_course(self, course_id: str, features_df: pd.DataFrame) -> pd.DataFrame:
        """Predict fail risk cho tất cả sinh viên trong course"""
        logger.info(f"Predicting fail risk for course {course_id}...")
        
        # Save student info columns (không dùng để predict nhưng cần cho output)
        info_columns = ['user_id', 'course_id', 'email', 'full_name', 'mooc_grade_percentage']
        student_info = features_df[[col for col in info_columns if col in features_df.columns]].copy()
        
        # Prepare features (same as training)
        X = features_df[self.trainer.feature_names].copy()
        
        # Handle categorical features
        for col in self.trainer.categorical_features:
            if col in X.columns:
                X[col] = X[col].fillna('missing').astype(str)
        
        # Handle numeric features
        numeric_cols = [col for col in X.columns if col not in self.trainer.categorical_features]
        X[numeric_cols] = X[numeric_cols].fillna(0)
        
        # Predict
        predictions = self.trainer.model.predict_proba(X)[:, 1] * 100
        
        # Add predictions to student info
        student_info['fail_risk_score'] = predictions
        student_info['risk_level'] = student_info['fail_risk_score'].apply(self.classify_risk_level)
        
        logger.info(f"Predictions completed for {len(student_info)} students")
        logger.info(f"HIGH risk: {(student_info['risk_level'] == 'HIGH').sum()}")
        logger.info(f"MEDIUM risk: {(student_info['risk_level'] == 'MEDIUM').sum()}")
        logger.info(f"LOW risk: {(student_info['risk_level'] == 'LOW').sum()}")
        
        return student_info
    
    def save_predictions(self, predictions_df: pd.DataFrame) -> bool:
        """Save predictions vào database"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect_db():
                return False
        
        try:
            cursor = self.connection.cursor()
            
            # Update raw_data table với predictions
            update_query = """
            UPDATE raw_data
            SET fail_risk_score = %s, dropout_risk_score = %s
            WHERE user_id = %s AND course_id = %s
            """
            
            updated_count = 0
            for _, row in predictions_df.iterrows():
                values = (
                    row['fail_risk_score'],
                    row['fail_risk_score'],  # Use same score for dropout_risk for now
                    row['user_id'],
                    row['course_id']
                )
                cursor.execute(update_query, values)
                updated_count += 1
            
            self.connection.commit()
            logger.info(f"Updated {updated_count} predictions in database")
            return True
            
        except Error as e:
            logger.error(f"Error saving predictions: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()


def main():
    """Main prediction function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Predict Dropout Risk')
    parser.add_argument('--input', type=str, required=True, help='Input features CSV file')
    parser.add_argument('--course-id', type=str, required=True, help='Course ID')
    parser.add_argument('--model-name', type=str, default='dropout_prediction_model', help='Model name')
    parser.add_argument('--output', type=str, help='Output CSV file (optional)')
    parser.add_argument('--save-db', action='store_true', help='Save predictions to database')
    
    args = parser.parse_args()
    
    # Load features
    logger.info(f"Loading features from {args.input}...")
    df = pd.read_csv(args.input)
    
    # Filter by course_id
    df_course = df[df['course_id'] == args.course_id].copy()
    logger.info(f"Found {len(df_course)} students in course {args.course_id}")
    
    if df_course.empty:
        logger.error("No students found for this course")
        return
    
    # Create predictor
    predictor = DropoutPredictor(args.model_name)
    
    try:
        # Predict
        predictions_df = predictor.predict_course(args.course_id, df_course)
        
        # Add suggestions
        suggestions_list = []
        for _, row in predictions_df.iterrows():
            suggestions = predictor.generate_suggestions(row.to_dict())
            suggestions_list.append('; '.join(suggestions))
        
        predictions_df['suggestions'] = suggestions_list
        
        # Save to CSV if specified
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            predictions_df.to_csv(output_path, index=False)
            logger.info(f"Predictions saved to {output_path}")
        
        # Save to database if specified
        if args.save_db:
            predictor.save_predictions(predictions_df)
        
        # Print summary
        logger.info("\n=== Prediction Summary ===")
        logger.info(f"Total students: {len(predictions_df)}")
        logger.info(f"Average fail risk: {predictions_df['fail_risk_score'].mean():.2f}%")
        
        logger.info("\nRisk Distribution:")
        risk_counts = predictions_df['risk_level'].value_counts()
        for level in ['HIGH', 'MEDIUM', 'LOW']:
            count = risk_counts.get(level, 0)
            pct = count / len(predictions_df) * 100
            logger.info(f"  {level}: {count} ({pct:.1f}%)")
        
        logger.info("\nTop 10 At-Risk Students:")
        # Select columns that exist
        display_cols = ['user_id', 'fail_risk_score', 'risk_level', 'mooc_grade_percentage']
        if 'email' in predictions_df.columns:
            display_cols.insert(1, 'email')
        if 'full_name' in predictions_df.columns:
            display_cols.insert(2, 'full_name')
        
        top_risk = predictions_df.nlargest(10, 'fail_risk_score')[display_cols]
        for _, row in top_risk.iterrows():
            email_str = f"{row.get('email', 'N/A')}: " if 'email' in row else f"User {row['user_id']}: "
            logger.info(f"  {email_str}{row['fail_risk_score']:.1f}% ({row['risk_level']}) - Grade: {row['mooc_grade_percentage']:.1f}%")
        
    finally:
        predictor.close_db()


if __name__ == "__main__":
    main()
