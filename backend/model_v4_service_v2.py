"""
Model V4 Service V2 - Refactored for new schema
Đọc từ student_features, ghi vào predictions
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from catboost import CatBoostClassifier

# Conditional import
if __package__ in (None, ""):
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from backend.db import fetch_one, fetch_all, execute, save_prediction, get_course_model_mapping, get_default_model  # type: ignore
else:
    from .db import fetch_one, fetch_all, execute, save_prediction, get_course_model_mapping, get_default_model

logger = logging.getLogger(__name__)


class ModelV4ServiceV2:
    """
    Service V2 - Sử dụng schema mới với student_features và predictions
    """

    def __init__(self, model_name: Optional[str] = None, model_path: Optional[str] = None, 
                 feature_fallback_csv: Optional[str] = None):
        """
        Khởi tạo service và load model
        
        Args:
            model_name: Tên model trong registry (e.g., 'fm101_v4')
            model_path: Path trực tiếp đến model (override registry)
            feature_fallback_csv: Path đến CSV chứa feature names
        """
        self.model: Optional[CatBoostClassifier] = None
        self.feature_names: Optional[List[str]] = None
        self.categorical_features: Optional[List[str]] = None
        self.model_name = model_name or 'fm101_v4'
        self.model_version = 'v4.0.0'
        
        # Load model info from registry or use provided path
        if model_path:
            self.model_path = model_path
        else:
            # Try to get from registry
            model_info = fetch_one(
                "SELECT * FROM model_registry WHERE model_name = %s AND is_active = TRUE",
                (self.model_name,)
            )
            if model_info:
                self.model_path = model_info['model_path']
                self.model_version = model_info['model_version']
                self.feature_fallback_csv = model_info.get('features_csv_path') or feature_fallback_csv
                logger.info(f"Loaded model config from registry: {self.model_name} v{self.model_version}")
            else:
                # Fallback to default path
                self.model_path = str(Path(__file__).parent.parent / "models" / "fm101_model_v4.cbm")
                logger.warning(f"Model {self.model_name} not in registry, using default path")
        
        if not feature_fallback_csv and not hasattr(self, 'feature_fallback_csv'):
            self.feature_fallback_csv = str(
                Path(__file__).parent.parent / "models" / "fm101_model_v4_feature_importance.csv"
            )
        
        self._load_model()

    def _load_model(self):
        """Load CatBoost model và metadata"""
        try:
            self.model = CatBoostClassifier()
            self.model.load_model(self.model_path)
            logger.info(f"Model v4 loaded successfully from {self.model_path}")

            if self.model.feature_names_:
                self.feature_names = self.model.feature_names_
            else:
                logger.warning("Model does not contain feature_names_. Loading from CSV.")
                self._load_feature_names_from_csv()

            self.categorical_features = [
                "enrollment_mode",
                "current_chapter",
                "current_section",
                "current_unit",
                "enrollment_phase",
            ]
            logger.info(f"Loaded {len(self.feature_names)} features")

        except Exception as e:
            logger.error(f"Error loading Model v4 from {self.model_path}: {e}")
            self.model = None
            self._load_feature_names_from_csv()

    def _load_feature_names_from_csv(self):
        """Load feature names từ CSV fallback"""
        try:
            df_features = pd.read_csv(self.feature_fallback_csv)
            self.feature_names = df_features["feature"].tolist()
            logger.info(f"Feature names loaded from CSV: {self.feature_fallback_csv}")
        except Exception as e:
            logger.error(f"Error loading feature names from CSV: {e}")
            self.feature_names = []

    def _fetch_student_features(self, course_id: str) -> Optional[pd.DataFrame]:
        """
        Lấy student features từ student_features table
        
        Args:
            course_id: ID khóa học
            
        Returns:
            DataFrame chứa features
        """
        query = """
            SELECT f.*, e.email, e.full_name, e.username, e.mssv
            FROM student_features f
            LEFT JOIN enrollments e ON f.user_id = e.user_id AND f.course_id = e.course_id
            WHERE f.course_id = %s
        """
        data = fetch_all(query, (course_id,))
        
        if not data:
            logger.warning(f"No student_features found for course {course_id}")
            return None

        df = pd.DataFrame(data)

        # Convert datetime columns
        for col in ["last_activity", "updated_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Ensure numeric types
        numeric_cols = [
            "mooc_grade_percentage", "mooc_completion_rate", "overall_completion",
            "h5p_overall_percentage", "h5p_completion_rate",
            "video_completion_rate", "video_watch_rate",
            "quiz_avg_score", "quiz_completion_rate",
            "access_frequency", "relative_to_course_problem_score",
            "relative_to_course_completion", "relative_to_course_video_completion",
            "relative_to_course_discussion", "performance_percentile",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df

    def _feature_engineer(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Feature engineering - Tạo thêm features từ raw features
        
        Args:
            df: DataFrame chứa student_features
            
        Returns:
            DataFrame với features đầy đủ cho model
        """
        df = df.copy()

        # 1. Enrollment phase
        df["enrollment_phase"] = df["weeks_since_enrollment"].apply(
            lambda x: "early" if x <= 2 else "mid" if x <= 6 else "late"
        )

        # 2. Activity engagement
        df["is_highly_engaged"] = (
            (df["access_frequency"] > df["access_frequency"].median()) &
            (df["discussion_total_interactions"] > 0)
        ).astype(int)

        # 3. Video engagement
        df["video_engagement_score"] = (
            df["video_completion_rate"] * 0.6 + df["video_watch_rate"] * 0.4
        )

        # 4. Quiz performance indicator
        df["quiz_performance"] = df["quiz_avg_score"]

        # 5. Interaction density
        df["interaction_density"] = np.where(
            df["weeks_since_enrollment"] > 0,
            (df["discussion_total_interactions"] + df["quiz_attempts"]) / df["weeks_since_enrollment"],
            0,
        )

        # 6. Overall engagement
        df["overall_engagement"] = (
            df["mooc_completion_rate"] * 0.3 +
            df["video_completion_rate"] * 0.25 +
            df["quiz_completion_rate"] * 0.25 +
            (df["discussion_total_interactions"] / max(df["discussion_total_interactions"].max(), 1)) * 100 * 0.2
        )

        # 7. Risk indicators
        df["low_completion_flag"] = (df["mooc_completion_rate"] < 30).astype(int)
        df["inactive_flag"] = (df["days_since_last_activity"] > 7).astype(int)
        df["low_grade_flag"] = (df["mooc_grade_percentage"] < 40).astype(int)

        # Fill NaN
        df.fillna(0, inplace=True)

        return df

    def predict_course(self, course_id: str, save_to_db: bool = True) -> pd.DataFrame:
        """
        Predict risk cho tất cả sinh viên trong khóa học
        
        Args:
            course_id: ID khóa học
            save_to_db: Lưu vào predictions table
            
        Returns:
            DataFrame chứa predictions
        """
        if not self.model or not self.feature_names:
            logger.error("Model not loaded or feature names missing")
            return pd.DataFrame()

        # Fetch student features
        df = self._fetch_student_features(course_id)
        if df is None or df.empty:
            logger.info(f"No student features found for course {course_id}")
            return pd.DataFrame()

        logger.info(f"Predicting for {len(df)} students in {course_id}")

        # Feature engineering
        features_df = self._feature_engineer(df.copy())

        # Prepare features for prediction
        X = features_df[self.feature_names].copy()

        # Handle categorical features
        for col in self.categorical_features:
            if col in X.columns:
                X[col] = X[col].fillna("missing").astype(str)

        # Handle numeric features
        numeric_features = [f for f in self.feature_names if f not in self.categorical_features]
        for col in numeric_features:
            if col in X.columns:
                X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

        # Predict probabilities
        try:
            proba = self.model.predict_proba(X)
            fail_proba = proba[:, 1] * 100  # Class 1 probability as percentage

            # Build results
            results_df = pd.DataFrame({
                "user_id": features_df["user_id"],
                "course_id": features_df["course_id"],
                "fail_risk_score": fail_proba,
                "mooc_grade_percentage": features_df["mooc_grade_percentage"],
                "mooc_completion_rate": features_df["mooc_completion_rate"],
                "days_since_last_activity": features_df["days_since_last_activity"],
            })

            # Add risk level
            results_df["risk_level"] = results_df["fail_risk_score"].apply(self.classify_risk_level)

            logger.info(f"Prediction completed for {len(results_df)} students")

            # Save to database
            if save_to_db:
                self._save_predictions_to_db(results_df)

            return results_df

        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            return pd.DataFrame()

    def predict_student(self, course_id: str, user_id: int, save_to_db: bool = True) -> Optional[Dict[str, Any]]:
        """
        Predict risk cho một sinh viên cụ thể
        
        Args:
            course_id: ID khóa học
            user_id: ID sinh viên
            save_to_db: Lưu vào predictions table
            
        Returns:
            Dictionary chứa prediction result
        """
        if not self.model or not self.feature_names:
            logger.error("Model not loaded")
            return None

        # Fetch student features
        query = """
            SELECT f.*, e.email, e.full_name, e.username, e.mssv
            FROM student_features f
            LEFT JOIN enrollments e ON f.user_id = e.user_id AND f.course_id = e.course_id
            WHERE f.user_id = %s AND f.course_id = %s
        """
        data = fetch_one(query, (user_id, course_id))
        
        if not data:
            logger.warning(f"No features found for user {user_id} in course {course_id}")
            return None

        df = pd.DataFrame([data])
        
        # Convert types
        for col in ["last_activity", "updated_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Feature engineering
        features_df = self._feature_engineer(df)
        X = features_df[self.feature_names].copy()

        # Handle features
        for col in self.categorical_features:
            if col in X.columns:
                X[col] = X[col].fillna("missing").astype(str)
        
        for col in [f for f in self.feature_names if f not in self.categorical_features]:
            if col in X.columns:
                X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

        # Predict
        try:
            proba = self.model.predict_proba(X)
            fail_risk_score = float(proba[0, 1] * 100)
            risk_level = self.classify_risk_level(fail_risk_score)

            result = {
                "user_id": user_id,
                "course_id": course_id,
                "fail_risk_score": fail_risk_score,
                "risk_level": risk_level,
                "model_name": self.model_name,
                "model_version": self.model_version,
                "mooc_grade_percentage": float(data.get("mooc_grade_percentage") or 0),
                "mooc_completion_rate": float(data.get("mooc_completion_rate") or 0),
                "days_since_last_activity": int(data.get("days_since_last_activity") or 0),
            }

            # Save to database
            if save_to_db:
                success = save_prediction(
                    user_id=user_id,
                    course_id=course_id,
                    model_name=self.model_name,
                    fail_risk_score=fail_risk_score,
                    risk_level=risk_level,
                    model_version=self.model_version,
                    model_path=self.model_path,
                    snapshot_grade=result["mooc_grade_percentage"],
                    snapshot_completion_rate=result["mooc_completion_rate"],
                    snapshot_days_inactive=result["days_since_last_activity"]
                )
                if success:
                    logger.info(f"Saved prediction for user {user_id} to database")

            return result

        except Exception as e:
            logger.error(f"Error predicting for user {user_id}: {e}")
            return None

    def _save_predictions_to_db(self, predictions_df: pd.DataFrame):
        """
        Lưu predictions vào predictions table
        
        Args:
            predictions_df: DataFrame chứa predictions
        """
        saved_count = 0
        for _, row in predictions_df.iterrows():
            success = save_prediction(
                user_id=int(row["user_id"]),
                course_id=row["course_id"],
                model_name=self.model_name,
                fail_risk_score=float(row["fail_risk_score"]),
                risk_level=row["risk_level"],
                model_version=self.model_version,
                model_path=self.model_path,
                snapshot_grade=float(row.get("mooc_grade_percentage", 0)),
                snapshot_completion_rate=float(row.get("mooc_completion_rate", 0)),
                snapshot_days_inactive=int(row.get("days_since_last_activity", 0))
            )
            if success:
                saved_count += 1
        
        logger.info(f"Saved {saved_count}/{len(predictions_df)} predictions to database")

    def classify_risk_level(self, risk_score: float) -> str:
        """Classify risk level từ risk score"""
        if risk_score >= 70:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    def generate_suggestions(self, student_data: Dict) -> List[Dict[str, str]]:
        """
        Generate intervention suggestions
        
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
            suggestions.append({
                "type": "urgent",
                "icon": "🚨",
                "title": "Liên hệ ngay",
                "description": "Gặp trực tiếp hoặc gọi điện để tìm hiểu khó khăn"
            })

        if days_inactive > 7:
            suggestions.append({
                "type": "warning",
                "icon": "⏰",
                "title": "Nhắc nhở tham gia",
                "description": f"Sinh viên không hoạt động {days_inactive} ngày"
            })

        if grade_percentage < 50:
            suggestions.append({
                "type": "academic",
                "icon": "📚",
                "title": "Hỗ trợ học tập",
                "description": "Gợi ý tài liệu bổ sung, buổi tutorial"
            })

        if completion_rate < 40:
            suggestions.append({
                "type": "progress",
                "icon": "📈",
                "title": "Động viên tiến độ",
                "description": "Nhắc deadline, khuyến khích hoàn thành bài tập"
            })

        if discussion_interactions == 0:
            suggestions.append({
                "type": "engagement",
                "icon": "💬",
                "title": "Khuyến khích tương tác",
                "description": "Mời tham gia thảo luận, đặt câu hỏi"
            })

        if video_completion_rate < 50:
            suggestions.append({
                "type": "content",
                "icon": "🎥",
                "title": "Xem video bài giảng",
                "description": "Nhắc nhở xem đầy đủ video"
            })

        if quiz_avg_score < 60:
            suggestions.append({
                "type": "assessment",
                "icon": "✍️",
                "title": "Luyện tập thêm",
                "description": "Gợi ý bài tập thêm, quiz ôn tập"
            })

        if not suggestions:
            suggestions.append({
                "type": "success",
                "icon": "✅",
                "title": "Tiếp tục duy trì",
                "description": "Sinh viên đang học tốt, tiếp tục theo dõi"
            })

        return suggestions


# ============================================================================
# HELPER FUNCTION: Auto-select model for course
# ============================================================================

def get_model_for_course(course_id: str) -> ModelV4ServiceV2:
    """
    Tự động chọn model phù hợp cho course
    
    Args:
        course_id: ID khóa học
        
    Returns:
        ModelV4ServiceV2 instance với model phù hợp
    """
    # Try to get mapping from database
    mapping = get_course_model_mapping(course_id)
    
    if mapping:
        logger.info(f"Using mapped model '{mapping['model_name']}' for course {course_id}")
        return ModelV4ServiceV2(
            model_name=mapping['model_name'],
            model_path=mapping['model_path'],
            feature_fallback_csv=mapping.get('features_csv_path')
        )
    else:
        # Fallback to default model
        default = get_default_model()
        if default:
            logger.info(f"Using default model '{default['model_name']}' for course {course_id}")
            return ModelV4ServiceV2(
                model_name=default['model_name'],
                model_path=default['model_path'],
                feature_fallback_csv=default.get('features_csv_path')
            )
        else:
            # Ultimate fallback
            logger.warning(f"No model mapping or default found, using fm101_v4")
            return ModelV4ServiceV2(model_name='fm101_v4')
