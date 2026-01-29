"""
Model V4 Service - Tích hợp CatBoost model với database
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any

from catboost import CatBoostClassifier

# Conditional import for running as script or module
if __package__ in (None, ""):
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from backend.db import fetch_one, fetch_all, execute  # type: ignore
else:
    from .db import fetch_one, fetch_all, execute

logger = logging.getLogger(__name__)


class ModelV4Service:
    """
    Service để load và sử dụng Model v4 (CatBoost) cho dự đoán dropout/fail risk.
    Bao gồm logic feature engineering và tương tác với database.
    """

    def __init__(self, model_path: Optional[str] = None, feature_fallback_csv: Optional[str] = None):
        """
        Khởi tạo service và load model
        
        Args:
            model_path: Đường dẫn đến file model .cbm
            feature_fallback_csv: Đường dẫn đến CSV chứa danh sách features
        """
        self.model: Optional[CatBoostClassifier] = None
        self.feature_names: Optional[List[str]] = None
        self.categorical_features: Optional[List[str]] = None
        
        # Set default paths
        if model_path:
            self.model_path = model_path
        else:
            self.model_path = str(Path(__file__).parent.parent / "models" / "fm101_model_v4.cbm")
        
        if feature_fallback_csv:
            self.feature_fallback_csv = feature_fallback_csv
        else:
            self.feature_fallback_csv = str(
                Path(__file__).parent.parent / "models" / "fm101_model_v4_feature_importance.csv"
            )
        
        self._load_model()

    def _load_model(self):
        """Tải model CatBoost và metadata"""
        try:
            self.model = CatBoostClassifier()
            self.model.load_model(self.model_path)
            logger.info(f"Model v4 loaded successfully from {self.model_path}")

            # Get feature names from model
            if self.model.feature_names_:
                self.feature_names = self.model.feature_names_
            else:
                logger.warning("Model does not contain feature_names_. Loading from fallback CSV.")
                self._load_feature_names_from_csv()

            # Define categorical features (phải match với training)
            self.categorical_features = [
                "enrollment_mode",
                "current_chapter",
                "current_section",
                "current_unit",
                "enrollment_phase",
            ]
            logger.info(f"Categorical features: {self.categorical_features}")

        except Exception as e:
            logger.error(f"Error loading Model v4 from {self.model_path}: {e}")
            self.model = None
            self._load_feature_names_from_csv()

    def _load_feature_names_from_csv(self):
        """Tải danh sách feature names từ CSV fallback"""
        try:
            df_features = pd.read_csv(self.feature_fallback_csv)
            self.feature_names = df_features["feature"].tolist()
            logger.info(f"Feature names loaded from fallback CSV: {self.feature_fallback_csv}")
        except Exception as e:
            logger.error(f"Error loading feature names from {self.feature_fallback_csv}: {e}")
            self.feature_names = []

    def _fetch_raw_data_for_course(self, course_id: str) -> Optional[pd.DataFrame]:
        """
        Lấy tất cả raw data cần thiết cho một khóa học từ database
        
        Args:
            course_id: ID của khóa học
            
        Returns:
            DataFrame chứa raw data hoặc None nếu không có data
        """
        query = """
            SELECT rd.*, e.email, e.full_name, e.username, e.mssv
            FROM raw_data rd
            LEFT JOIN enrollments e ON rd.user_id = e.user_id AND rd.course_id = e.course_id
            WHERE rd.course_id = %s
        """
        data = fetch_all(query, (course_id,))
        if not data:
            return None

        df = pd.DataFrame(data)

        # Convert datetime columns
        for col in ["last_activity", "extracted_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Ensure numeric types
        numeric_cols = [
            "mooc_grade_percentage",
            "mooc_completion_rate",
            "days_since_last_activity",
            "h5p_total_contents",
            "h5p_completed_contents",
            "h5p_overall_percentage",
            "video_completion_rate",
            "discussion_total_interactions",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df

    def _feature_engineer(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Tạo các features cần thiết cho model từ raw data
        Đây là phiên bản rút gọn, trong thực tế nên import từ ml/feature_engineering.py
        
        Args:
            df: DataFrame chứa raw data
            
        Returns:
            DataFrame với các features đã được tạo
        """
        if df.empty:
            return df

        # Basic engagement features
        df["engagement_score"] = (
            df.get("mooc_completion_rate", 0)
            + df.get("video_completion_rate", 0)
            + df.get("h5p_overall_percentage", 0)
        ) / 3

        df["activity_recency"] = 100 - (df.get("days_since_last_activity", 0) / 30 * 100).clip(0, 100)
        df["activity_consistency"] = (df["engagement_score"] + df["activity_recency"]) / 2
        
        df["is_inactive"] = (df.get("days_since_last_activity", 0) > 7).astype(int)
        df["is_struggling"] = (
            (df.get("mooc_completion_rate", 0) < 50) | (df.get("video_completion_rate", 0) < 50)
        ).astype(int)
        
        df["discussion_engagement_rate"] = df.get("discussion_total_interactions", 0)
        df["has_no_discussion"] = (df.get("discussion_total_interactions", 0) == 0).astype(int)

        # Add enrollment_phase if not present
        if "enrollment_phase" not in df.columns:
            df["enrollment_phase"] = "mid"

        # Ensure all expected features exist
        if self.feature_names:
            for col in self.feature_names:
                if col not in df.columns:
                    if col in self.categorical_features:
                        df[col] = "missing"
                    else:
                        df[col] = 0

        return df

    def predict_course(self, course_id: str, save_db: bool = False) -> pd.DataFrame:
        """
        Dự đoán risk cho tất cả sinh viên trong một khóa học
        
        Args:
            course_id: ID của khóa học
            save_db: Có lưu kết quả vào database không
            
        Returns:
            DataFrame chứa predictions
        """
        if not self.model or not self.feature_names:
            logger.error("Model not loaded or feature names missing.")
            return pd.DataFrame()

        raw_df = self._fetch_raw_data_for_course(course_id)
        if raw_df is None or raw_df.empty:
            logger.info(f"No raw data found for course {course_id}")
            return pd.DataFrame()

        features_df = self._feature_engineer(raw_df.copy())

        # Prepare features for prediction
        X = features_df[self.feature_names].copy()

        # Handle categorical features
        for col in self.categorical_features:
            if col in X.columns:
                X[col] = X[col].fillna("missing").astype(str)

        # Handle numeric features
        numeric_cols = [col for col in X.columns if col not in self.categorical_features]
        X[numeric_cols] = X[numeric_cols].fillna(0)

        # Predict
        predictions = self.model.predict_proba(X)[:, 1] * 100  # Probability of class 1 (fail)

        # Build results
        results_df = raw_df[
            [
                "user_id",
                "course_id",
                "email",
                "full_name",
                "mooc_grade_percentage",
                "mooc_completion_rate",
                "days_since_last_activity",
            ]
        ].copy()
        results_df["fail_risk_score"] = predictions
        results_df["risk_level"] = results_df["fail_risk_score"].apply(self.classify_risk_level)

        if save_db:
            self._save_predictions_to_db(results_df)

        return results_df

    def predict_student(self, course_id: str, user_id: int, save_db: bool = False) -> Optional[Dict[str, Any]]:
        """
        Dự đoán risk cho một sinh viên cụ thể
        
        Args:
            course_id: ID của khóa học
            user_id: ID của sinh viên
            save_db: Có lưu kết quả vào database không
            
        Returns:
            Dictionary chứa thông tin và prediction của sinh viên
        """
        if not self.model or not self.feature_names:
            logger.error("Model not loaded or feature names missing.")
            return None

        raw_df = self._fetch_raw_data_for_course(course_id)
        if raw_df is None or raw_df.empty:
            return None

        student_raw_data = raw_df[raw_df["user_id"] == user_id]
        if student_raw_data.empty:
            return None

        features_df = self._feature_engineer(student_raw_data.copy())

        # Prepare features
        X = features_df[self.feature_names].copy()

        # Handle categorical
        for col in self.categorical_features:
            if col in X.columns:
                X[col] = X[col].fillna("missing").astype(str)

        # Handle numeric
        numeric_cols = [col for col in X.columns if col not in self.categorical_features]
        X[numeric_cols] = X[numeric_cols].fillna(0)

        # Predict
        prediction = self.model.predict_proba(X)[:, 1][0] * 100

        student_result = student_raw_data.iloc[0].to_dict()
        student_result["fail_risk_score"] = prediction
        student_result["risk_level"] = self.classify_risk_level(prediction)
        student_result["suggestions"] = self.generate_suggestions(student_result)

        if save_db:
            save_df = pd.DataFrame([student_result])
            self._save_predictions_to_db(save_df)

        return student_result

    def _save_predictions_to_db(self, predictions_df: pd.DataFrame):
        """
        Lưu fail_risk_score vào bảng raw_data
        
        Args:
            predictions_df: DataFrame chứa predictions cần lưu
        """
        update_query = """
            UPDATE raw_data
            SET fail_risk_score = %s
            WHERE user_id = %s AND course_id = %s
        """
        for _, row in predictions_df.iterrows():
            execute(
                update_query,
                (row["fail_risk_score"], row["user_id"], row["course_id"]),
            )
        logger.info(f"Updated {len(predictions_df)} student risk scores in raw_data table.")

    def classify_risk_level(self, risk_score: float) -> str:
        """Phân loại risk level dựa trên risk score"""
        if risk_score >= 70:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    def generate_suggestions(self, student_data: Dict) -> List[Dict[str, str]]:
        """
        Tạo gợi ý can thiệp dựa trên student data
        
        Args:
            student_data: Dictionary chứa thông tin sinh viên
            
        Returns:
            List các gợi ý can thiệp
        """
        suggestions = []
        risk_level = student_data.get("risk_level", "LOW")
        days_inactive = student_data.get("days_since_last_activity", 0)
        grade_percentage = student_data.get("mooc_grade_percentage", 100)
        completion_rate = student_data.get("mooc_completion_rate", 100)
        discussion_interactions = student_data.get("discussion_total_interactions", 0)
        video_completion_rate = student_data.get("video_completion_rate", 100)
        quiz_avg_score = student_data.get("quiz_avg_score", 100)

        if risk_level == "HIGH":
            suggestions.append(
                {
                    "icon": "🚨",
                    "title": "Can thiệp khẩn cấp",
                    "description": "Sinh viên có nguy cơ bỏ học/rớt môn rất cao. Cần liên hệ ngay.",
                    "priority": "high",
                }
            )

        if days_inactive > 14:
            suggestions.append(
                {
                    "icon": "📞",
                    "title": "Liên hệ trực tiếp",
                    "description": f"Sinh viên không hoạt động {days_inactive} ngày. Hãy gọi điện hoặc nhắn tin.",
                    "priority": "high",
                }
            )
        elif days_inactive > 7:
            suggestions.append(
                {
                    "icon": "📧",
                    "title": "Gửi email nhắc nhở",
                    "description": f"Sinh viên không hoạt động {days_inactive} ngày. Gửi email khuyến khích quay lại.",
                    "priority": "medium",
                }
            )

        if grade_percentage < 40:
            suggestions.append(
                {
                    "icon": "📉",
                    "title": "Hỗ trợ học tập",
                    "description": f"Điểm trung bình thấp ({grade_percentage}%). Cung cấp tài liệu bổ sung hoặc buổi phụ đạo.",
                    "priority": "high",
                }
            )
        elif grade_percentage < 60:
            suggestions.append(
                {
                    "icon": "📚",
                    "title": "Kiểm tra tiến độ",
                    "description": f"Điểm trung bình khá thấp ({grade_percentage}%). Theo dõi sát sao và gợi ý tài liệu.",
                    "priority": "medium",
                }
            )

        if completion_rate < 30:
            suggestions.append(
                {
                    "icon": "⏳",
                    "title": "Nhắc nhở lộ trình",
                    "description": f"Tiến độ hoàn thành khóa học rất chậm ({completion_rate}%). Nhắc nhở về deadline và kế hoạch học.",
                    "priority": "high",
                }
            )
        elif completion_rate < 50:
            suggestions.append(
                {
                    "icon": "🗓️",
                    "title": "Đánh giá lại mục tiêu",
                    "description": f"Tiến độ hoàn thành khóa học chậm ({completion_rate}%). Giúp sinh viên đặt mục tiêu thực tế hơn.",
                    "priority": "medium",
                }
            )

        if discussion_interactions == 0 and risk_level in ["HIGH", "MEDIUM"]:
            suggestions.append(
                {
                    "icon": "💬",
                    "title": "Khuyến khích tương tác",
                    "description": "Sinh viên không tham gia thảo luận. Khuyến khích đặt câu hỏi hoặc tham gia forum.",
                    "priority": "medium",
                }
            )

        if video_completion_rate < 50 and risk_level in ["HIGH", "MEDIUM"]:
            suggestions.append(
                {
                    "icon": "🎥",
                    "title": "Kiểm tra việc học video",
                    "description": f"Tỷ lệ hoàn thành video thấp ({video_completion_rate}%). Có thể sinh viên gặp khó khăn với nội dung video.",
                    "priority": "medium",
                }
            )

        if quiz_avg_score < 50 and risk_level in ["HIGH", "MEDIUM"]:
            suggestions.append(
                {
                    "icon": "📝",
                    "title": "Hỗ trợ làm bài tập/quiz",
                    "description": f"Điểm quiz trung bình thấp ({quiz_avg_score}%). Cung cấp thêm bài tập hoặc giải đáp thắc mắc.",
                    "priority": "medium",
                }
            )

        if not suggestions:
            suggestions.append(
                {
                    "icon": "👍",
                    "title": "Tiếp tục theo dõi",
                    "description": "Sinh viên đang có tiến độ tốt. Tiếp tục duy trì và khuyến khích.",
                    "priority": "low",
                }
            )

        return suggestions

