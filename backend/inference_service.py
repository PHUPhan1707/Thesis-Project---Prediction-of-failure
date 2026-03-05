"""
Inference Service — CatBoost model inference cho dropout/fail risk prediction.

Kiến trúc 3 class tách biệt trách nhiệm:
  DataFetcher       — Lấy dữ liệu từ database
  FeaturePreparator — Tạo feature matrix cho inference
  RiskPredictor     — Load model, predict, SHAP explain
  InferenceService  — Facade kết hợp 3 class trên, public API chính
"""
import os
import logging
import pandas as pd
import numpy as np
from decimal import Decimal as _Dec
from pathlib import Path
from typing import Dict, List, Optional, Any

from catboost import CatBoostClassifier

# Conditional import for running as script or module
if __package__ in (None, ""):
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from backend.db import fetch_one, fetch_all, execute, save_prediction, save_predictions_batch  # type: ignore
    from backend.utils.feature_labels import get_vi_label                                          # type: ignore
else:
    from .db import fetch_one, fetch_all, execute, save_prediction, save_predictions_batch
    from .utils.feature_labels import get_vi_label

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _serialize_value(val):
    """Convert numpy/pandas types to JSON-serializable Python types."""
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return round(float(val), 4)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if pd.isna(val):
        return None
    return val


# ─────────────────────────────────────────────────────────────
# 1. DataFetcher — DB queries
# ─────────────────────────────────────────────────────────────

class DataFetcher:
    """
    Chịu trách nhiệm lấy dữ liệu thô từ database.
    Tách biệt toàn bộ SQL queries ra khỏi business logic.
    """

    @staticmethod
    def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
        """
        Chuẩn hoá kiểu dữ liệu sau khi load từ MySQL:
        - Decimal → float
        - datetime columns → pd.Timestamp
        - Các numeric columns quan trọng → numeric, fillna(0)
        Hàm dùng chung để tránh lặp code giữa 2 query methods.
        """
        # Decimal → float
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, _Dec)).any():
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # DateTime columns
        for col in ["last_activity", "extracted_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Numeric columns — đảm bảo không có NaN gây lỗi feature engineering
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

    def fetch_course(self, course_id: str) -> Optional[pd.DataFrame]:
        """
        Lấy tất cả raw data của một khóa học (bao gồm thông tin enrollment).

        Args:
            course_id: ID khóa học

        Returns:
            DataFrame hoặc None nếu không có data
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
        return self._normalize_df(pd.DataFrame(data))

    def fetch_student(self, course_id: str, user_id: int) -> Optional[pd.DataFrame]:
        """
        Lấy raw data của một sinh viên cụ thể (filter thêm user_id).

        Args:
            course_id: ID khóa học
            user_id: ID sinh viên

        Returns:
            DataFrame hoặc None
        """
        query = """
            SELECT rd.*, e.email, e.full_name, e.username, e.mssv
            FROM raw_data rd
            LEFT JOIN enrollments e ON rd.user_id = e.user_id AND rd.course_id = e.course_id
            WHERE rd.course_id = %s AND rd.user_id = %s
        """
        data = fetch_all(query, (course_id, user_id))
        if not data:
            return None
        return self._normalize_df(pd.DataFrame(data))


# ─────────────────────────────────────────────────────────────
# 2. FeaturePreparator — Feature engineering cho inference
# ─────────────────────────────────────────────────────────────

class FeaturePreparator:
    """
    Chuẩn bị feature matrix X từ raw DataFrame.
    Đảm bảo CÙNG công thức feature engineering giữa training và inference
    bằng cách dùng shared FeatureEngineer class từ ml module.
    """

    def __init__(
        self,
        feature_names: List[str],
        categorical_features: List[str],
    ):
        self.feature_names = feature_names
        self.categorical_features = categorical_features

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Tạo derived features từ raw DataFrame, dùng shared FeatureEngineer.
        Fallback về công thức đơn giản nếu import thất bại.

        Args:
            df: Raw DataFrame (đã normalize kiểu dữ liệu)

        Returns:
            DataFrame với tất cả derived features
        """
        if df.empty:
            return df

        try:
            from ml.feature_engineering import FeatureEngineer
            engineer = FeatureEngineer()
            df = engineer.create_all_features(df)
            logger.info("Features created using shared FeatureEngineer (consistent with training)")
        except ImportError:
            logger.warning("Could not import FeatureEngineer, using fallback feature engineering")
            df = self._fallback_engineer(df)
        except Exception as e:
            logger.warning(f"FeatureEngineer failed ({e}), using fallback")
            df = self._fallback_engineer(df)

        # Đảm bảo tất cả expected features tồn tại (fill missing với defaults)
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = "missing" if col in self.categorical_features else 0

        return df

    def build_X(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Chọn đúng columns và xử lý NaN sẵn sàng cho model.predict_proba().

        Args:
            features_df: DataFrame đã có đầy đủ derived features

        Returns:
            DataFrame X sẵn sàng cho prediction
        """
        X = features_df[self.feature_names].copy()

        # Categorical features
        # Ép kiểu sang string trước rồi mới fillna để tránh lỗi Categorical:
        # \"Cannot setitem on a Categorical with a new category (missing)\".
        for col in self.categorical_features:
            if col in X.columns:
                X[col] = X[col].astype(str)
                X[col] = X[col].fillna("missing")

        # Numeric features
        numeric_cols = [c for c in X.columns if c not in self.categorical_features]
        X[numeric_cols] = X[numeric_cols].fillna(0)

        return X

    # ── Fallback (chỉ dùng khi import FeatureEngineer thất bại) ──

    def _fallback_engineer(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        [FALLBACK ONLY] Feature engineering khi không import được FeatureEngineer.
        Đồng bộ với feature_engineering.py — hỗ trợ open course (không có deadline).
        """
        df["engagement_score"] = (
            df.get("mooc_completion_rate", 0)
            + df.get("video_completion_rate", 0)
            + df.get("h5p_overall_percentage", 0)
        ) / 3

        df["activity_recency"] = 100 - (
            df.get("days_since_last_activity", 0) / 30 * 100
        ).clip(0, 100)
        df["activity_consistency"] = (df["engagement_score"] + df["activity_recency"]) / 2

        df["is_inactive"] = (df.get("days_since_last_activity", 0) > 7).astype(int)
        df["is_highly_inactive"] = (df.get("days_since_last_activity", 0) > 14).astype(int)
        df["is_struggling"] = (
            (df.get("mooc_completion_rate", 0) < 50)
            | (df.get("video_completion_rate", 0) < 50)
        ).astype(int)
        df["is_at_risk"] = (df.get("mooc_completion_rate", 0) < 40).astype(int)

        if "course_id" in df.columns:
            df["relative_completion"] = (
                df.get("mooc_completion_rate", 0)
                - df.groupby("course_id")["mooc_completion_rate"].transform("mean")
            )
        else:
            df["relative_completion"] = 0

        completion_cols = ["mooc_completion_rate", "video_completion_rate", "h5p_completion_rate"]
        if all(c in df.columns for c in completion_cols):
            df["completion_consistency"] = df[completion_cols].std(axis=1).fillna(0)
        else:
            df["completion_consistency"] = 0

        df["discussion_engagement_rate"] = df.get("discussion_total_interactions", 0)
        df["has_no_discussion"] = (
            df.get("discussion_total_interactions", 0) == 0
        ).astype(int)
        df["video_engagement_rate"] = df.get("video_completion_rate", 0) / 100
        df["h5p_engagement_rate"] = df.get("h5p_completion_rate", 0) / 100
        df["interaction_score"] = (
            df["discussion_engagement_rate"] * 0.4
            + df["video_engagement_rate"] * 0.3
            + df["h5p_engagement_rate"] * 0.3
        ) * 100

        # ── Time features (open course) ──────────────────────────────────
        weeks = df.get(
            "weeks_since_enrollment", pd.Series([1] * len(df), index=df.index)
        ).replace(0, 1)

        df["progress_rate"] = df.get("mooc_completion_rate", 0) / weeks

        # learning_pace_score: tốc độ học trên thang log — triệt tiêu ảnh hưởng
        # của sinh viên đăng ký lâu nhưng không học (nhất quán với feature_engineering.py)
        df["learning_pace_score"] = (
            df.get("mooc_completion_rate", 0) / np.log2(weeks + 1)
        ).clip(0, 200)

        # open course → không có deadline → weeks_remaining = 0
        df["weeks_remaining"] = 0

        if "enrollment_phase" not in df.columns:
            wk = df.get("weeks_since_enrollment", pd.Series([0] * len(df), index=df.index))
            df["enrollment_phase"] = pd.cut(
                wk,
                bins=[0, 2, 4, 8, 12, float("inf")],
                labels=["very_early", "early", "mid", "late", "very_late"],
            ).astype(str).fillna("mid")

        return df


# ─────────────────────────────────────────────────────────────
# 3. RiskPredictor — Model loading, prediction, SHAP
# ─────────────────────────────────────────────────────────────

class RiskPredictor:
    """
    Chịu trách nhiệm về model machine learning:
    - Load CatBoost model từ file .cbm
    - predict_proba (fail risk score)
    - SHAP TreeExplainer (lazy-initialized)
    - classify_risk_level
    """

    def __init__(
        self,
        model_path: str,
        feature_fallback_csv: str,
    ):
        self.model_path = model_path
        self.feature_fallback_csv = feature_fallback_csv
        self.model: Optional[CatBoostClassifier] = None
        self.feature_names: Optional[List[str]] = None
        self.categorical_features: List[str] = ["enrollment_mode", "enrollment_phase"]
        self._shap_explainer = None  # lazy-initialized

        self._load_model()

    def _load_model(self):
        """Load CatBoost model từ file .cbm và lấy feature names."""
        try:
            self.model = CatBoostClassifier()
            self.model.load_model(self.model_path)
            logger.info(f"Model loaded from {self.model_path}")

            if self.model.feature_names_:
                self.feature_names = self.model.feature_names_
            else:
                logger.warning("Model has no feature_names_, loading from fallback CSV")
                self._load_feature_names_from_csv()

            logger.info(f"Categorical features: {self.categorical_features}")

        except Exception as e:
            logger.error(f"Error loading model from {self.model_path}: {e}")
            self.model = None
            self._load_feature_names_from_csv()

    def _load_feature_names_from_csv(self):
        """Load feature names từ CSV fallback khi model file không có metadata."""
        try:
            df_features = pd.read_csv(self.feature_fallback_csv)
            self.feature_names = df_features["feature"].tolist()
            logger.info(f"Feature names loaded from {self.feature_fallback_csv}")
        except Exception as e:
            logger.error(f"Error loading feature names from CSV: {e}")
            self.feature_names = []

    def is_ready(self) -> bool:
        """Kiểm tra model đã load đủ để predict chưa."""
        return self.model is not None and bool(self.feature_names)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Trả về xác suất fail (class 1) cho mỗi hàng trong X.

        Returns:
            1D array, mỗi giá trị từ 0–1
        """
        return self.model.predict_proba(X)[:, 1]

    def shap_explain(self, X: pd.DataFrame) -> Dict[str, Any]:
        """
        Tính SHAP values cho X (thường chứa 1 sinh viên).
        Lazy-init explainer lần đầu gọi.

        Returns:
            dict với keys: sv (1D array), base_value (float)
        """
        if self._shap_explainer is None:
            import shap
            self._shap_explainer = shap.TreeExplainer(self.model)
            logger.info("SHAP TreeExplainer initialized")

        shap_values = self._shap_explainer.shap_values(X)

        # Xử lý tất cả dạng output từ SHAP TreeExplainer + CatBoost:
        # - list [class0, class1]           → lấy class 1 (fail)
        # - 3D array [classes, samples, features] → lấy class 1
        # - 2D array [samples, features]        → đã là fail class
        # - 1D array                            → flatten sẵn
        if isinstance(shap_values, list):
            sv = np.array(shap_values[1]).flatten()
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            sv = shap_values[1][0]
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 2:
            sv = shap_values[0]
        else:
            sv = np.array(shap_values).flatten()

        expected = self._shap_explainer.expected_value
        if isinstance(expected, (list, np.ndarray)):
            raw_base = float(expected[1]) if len(expected) > 1 else float(expected[0])
        else:
            raw_base = float(expected)

        # Log-odds → probability
        base_value = 1.0 / (1.0 + np.exp(-raw_base))

        return {"sv": sv, "base_value": base_value}

    @staticmethod
    def classify_risk_level(risk_score: float) -> str:
        """Phân loại risk level dựa trên risk score (0–100)."""
        if risk_score >= 70:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"


# ─────────────────────────────────────────────────────────────
# 4. InferenceService — Facade (public API)
# ─────────────────────────────────────────────────────────────

class InferenceService:
    """
    Facade kết hợp DataFetcher + FeaturePreparator + RiskPredictor.
    Public API giữ nguyên hoàn toàn tương thích với ModelV4Service cũ:
      predict_course(), predict_student(), explain_student(),
      generate_suggestions(), classify_risk_level()
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        feature_fallback_csv: Optional[str] = None,
    ):
        _base = Path(__file__).parent.parent

        _model_path = model_path or str(_base / "models" / "fm101_model_v5.cbm")
        _csv_path = feature_fallback_csv or str(
            _base / "models" / "fm101_model_v5_feature_importance.csv"
        )

        self.model_path = _model_path
        self.model_name = "fm101_v5"

        # Khởi tạo 3 sub-components
        self._predictor = RiskPredictor(_model_path, _csv_path)
        self._fetcher = DataFetcher()
        self._preparator = FeaturePreparator(
            feature_names=self._predictor.feature_names or [],
            categorical_features=self._predictor.categorical_features,
        )

        logger.info(
            f"InferenceService ready — model: {_model_path}, "
            f"features: {len(self._predictor.feature_names or [])} columns"
        )

    # ── Convenience accessors (backward compat) ──────────────

    @property
    def model(self):
        return self._predictor.model

    @property
    def feature_names(self):
        return self._predictor.feature_names

    @property
    def categorical_features(self):
        return self._predictor.categorical_features

    # ── Public API ───────────────────────────────────────────

    def predict_course(self, course_id: str, save_db: bool = False) -> pd.DataFrame:
        """
        Dự đoán fail risk cho TẤT CẢ sinh viên trong một khóa học.

        Args:
            course_id: ID khóa học
            save_db:   Có lưu kết quả vào database không

        Returns:
            DataFrame với cột fail_risk_score và risk_level
        """
        if not self._predictor.is_ready():
            logger.error("Model not loaded or feature names missing.")
            return pd.DataFrame()

        raw_df = self._fetcher.fetch_course(course_id)
        if raw_df is None or raw_df.empty:
            logger.info(f"No raw data for course {course_id}")
            return pd.DataFrame()

        features_df = self._preparator.engineer_features(raw_df.copy())
        X = self._preparator.build_X(features_df)

        probas = self._predictor.predict_proba(X) * 100  # → score 0–100

        results_df = raw_df[[
            "user_id", "course_id", "email", "full_name",
            "mooc_grade_percentage", "mooc_completion_rate",
            "days_since_last_activity",
        ]].copy()
        results_df["fail_risk_score"] = probas
        results_df["risk_level"] = results_df["fail_risk_score"].apply(
            self._predictor.classify_risk_level
        )

        if save_db:
            self._save_predictions_to_db(results_df)

        return results_df

    def predict_student(
        self, course_id: str, user_id: int, save_db: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Dự đoán fail risk cho MỘT sinh viên.
        Feature-engineer toàn bộ course để group-relative features đúng.

        Args:
            course_id: ID khóa học
            user_id:   ID sinh viên
            save_db:   Có lưu kết quả không

        Returns:
            Dict chứa thông tin sinh viên + fail_risk_score + suggestions
        """
        if not self._predictor.is_ready():
            logger.error("Model not loaded or feature names missing.")
            return None

        raw_df = self._fetcher.fetch_course(course_id)
        if raw_df is None or raw_df.empty:
            return None

        student_raw = raw_df[raw_df["user_id"] == user_id]
        if student_raw.empty:
            return None

        # Feature-engineer toàn bộ course → extract target student
        features_df = self._preparator.engineer_features(raw_df.copy())
        features_df = features_df[features_df["user_id"] == user_id]

        X = self._preparator.build_X(features_df)
        proba = self._predictor.predict_proba(X)[0] * 100

        result = student_raw.iloc[0].to_dict()
        result["fail_risk_score"] = proba
        result["risk_level"] = self._predictor.classify_risk_level(proba)
        result["suggestions"] = self.generate_suggestions(result)

        if save_db:
            self._save_predictions_to_db(pd.DataFrame([result]))

        return result

    def explain_student(
        self, course_id: str, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        SHAP explanation cho dự đoán của một sinh viên.
        Trả về risk_factors (SHAP > 0) và protective_factors (SHAP < 0).

        Args:
            course_id: ID khóa học
            user_id:   ID sinh viên

        Returns:
            Dict với fail_risk_score, base_value, risk_factors, protective_factors
        """
        if not self._predictor.is_ready():
            logger.error("Model not loaded or feature names missing.")
            return None

        raw_df = self._fetcher.fetch_course(course_id)
        if raw_df is None or raw_df.empty:
            return None

        features_df = self._preparator.engineer_features(raw_df.copy())

        student_mask = features_df["user_id"] == user_id
        if not student_mask.any():
            return None
        features_df = features_df.loc[student_mask]

        X = self._preparator.build_X(features_df)

        fail_risk_score = float(self._predictor.predict_proba(X)[0]) * 100
        shap_result = self._predictor.shap_explain(X)
        sv = shap_result["sv"]
        base_value = shap_result["base_value"]

        # Build factor list
        feature_values = X.iloc[0]
        factors = [
            {
                "feature": fname,
                "label_vi": get_vi_label(fname),
                "shap_value": round(float(sv[i]), 6),
                "feature_value": _serialize_value(feature_values[fname]),
            }
            for i, fname in enumerate(self._predictor.feature_names)
        ]

        risk_factors = sorted(
            [f for f in factors if f["shap_value"] > 0],
            key=lambda x: x["shap_value"],
            reverse=True,
        )[:7]

        protective_factors = sorted(
            [f for f in factors if f["shap_value"] < 0],
            key=lambda x: x["shap_value"],
        )[:5]

        return {
            "user_id": int(user_id),
            "course_id": course_id,
            "fail_risk_score": round(fail_risk_score, 2),
            "base_value": round(base_value, 4),
            "risk_factors": risk_factors,
            "protective_factors": protective_factors,
        }

    def classify_risk_level(self, risk_score: float) -> str:
        """Delegate sang RiskPredictor.classify_risk_level."""
        return self._predictor.classify_risk_level(risk_score)

    def generate_suggestions(self, student_data: Dict) -> List[Dict[str, str]]:
        """
        Tạo gợi ý can thiệp dựa trên student data.

        Args:
            student_data: Dict chứa thông tin sinh viên (risk_level, days_since_last_activity, ...)

        Returns:
            List các gợi ý can thiệp với icon, title, description, priority
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
                "icon": "🚨",
                "title": "Can thiệp khẩn cấp",
                "description": "Sinh viên có nguy cơ bỏ học/rớt môn rất cao. Cần liên hệ ngay.",
                "priority": "high",
            })

        if days_inactive > 14:
            suggestions.append({
                "icon": "📞",
                "title": "Liên hệ trực tiếp",
                "description": f"Sinh viên không hoạt động {days_inactive} ngày. Hãy gọi điện hoặc nhắn tin.",
                "priority": "high",
            })
        elif days_inactive > 7:
            suggestions.append({
                "icon": "📧",
                "title": "Gửi email nhắc nhở",
                "description": f"Sinh viên không hoạt động {days_inactive} ngày. Gửi email khuyến khích quay lại.",
                "priority": "medium",
            })

        if grade_percentage < 40:
            suggestions.append({
                "icon": "📉",
                "title": "Hỗ trợ học tập",
                "description": f"Điểm trung bình thấp ({grade_percentage}%). Cung cấp tài liệu bổ sung hoặc buổi phụ đạo.",
                "priority": "high",
            })
        elif grade_percentage < 60:
            suggestions.append({
                "icon": "📚",
                "title": "Kiểm tra tiến độ",
                "description": f"Điểm trung bình khá thấp ({grade_percentage}%). Theo dõi sát sao và gợi ý tài liệu.",
                "priority": "medium",
            })

        if completion_rate < 30:
            suggestions.append({
                "icon": "⏳",
                "title": "Nhắc nhở lộ trình",
                "description": f"Tiến độ hoàn thành khóa học rất chậm ({completion_rate}%). Nhắc nhở về deadline và kế hoạch học.",
                "priority": "high",
            })
        elif completion_rate < 50:
            suggestions.append({
                "icon": "🗓️",
                "title": "Đánh giá lại mục tiêu",
                "description": f"Tiến độ hoàn thành chậm ({completion_rate}%). Giúp sinh viên đặt mục tiêu thực tế hơn.",
                "priority": "medium",
            })

        if discussion_interactions == 0 and risk_level in ["HIGH", "MEDIUM"]:
            suggestions.append({
                "icon": "💬",
                "title": "Khuyến khích tương tác",
                "description": "Sinh viên không tham gia thảo luận. Khuyến khích đặt câu hỏi hoặc tham gia forum.",
                "priority": "medium",
            })

        if video_completion_rate < 50 and risk_level in ["HIGH", "MEDIUM"]:
            suggestions.append({
                "icon": "🎥",
                "title": "Kiểm tra việc học video",
                "description": f"Tỷ lệ hoàn thành video thấp ({video_completion_rate}%). Sinh viên có thể gặp khó khăn với nội dung.",
                "priority": "medium",
            })

        if quiz_avg_score < 50 and risk_level in ["HIGH", "MEDIUM"]:
            suggestions.append({
                "icon": "📝",
                "title": "Hỗ trợ làm bài tập/quiz",
                "description": f"Điểm quiz trung bình thấp ({quiz_avg_score}%). Cung cấp thêm bài tập hoặc giải đáp thắc mắc.",
                "priority": "medium",
            })

        if not suggestions:
            suggestions.append({
                "icon": "👍",
                "title": "Tiếp tục theo dõi",
                "description": "Sinh viên đang có tiến độ tốt. Tiếp tục duy trì và khuyến khích.",
                "priority": "low",
            })

        return suggestions

    # ── Private ──────────────────────────────────────────────

    def _save_predictions_to_db(self, predictions_df: pd.DataFrame):
        """
        Lưu fail_risk_score vào raw_data (V1 compat) VÀ predictions table (V2).
        Dùng save_predictions_batch → 1 connection, 3 câu SQL thay vì N*2 câu.
        """
        predictions = [
            {
                "user_id": int(row["user_id"]),
                "course_id": row["course_id"],
                "fail_risk_score": float(row["fail_risk_score"]),
                "risk_level": row["risk_level"],
                "snapshot_grade": float(row.get("mooc_grade_percentage") or 0),
                "snapshot_completion_rate": float(row.get("mooc_completion_rate") or 0),
                "snapshot_days_inactive": int(row.get("days_since_last_activity") or 0),
            }
            for _, row in predictions_df.iterrows()
        ]

        saved = save_predictions_batch(
            predictions=predictions,
            model_name=self.model_name,
            model_version=getattr(self, "model_version", "v5.0.0"),
            model_path=self.model_path,
        )
        logger.info(f"Batch saved {saved}/{len(predictions_df)} predictions")
