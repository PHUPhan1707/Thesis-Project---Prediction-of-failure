"""
Predictions routes - Trigger ML predictions
"""
import logging
from flask import Blueprint, jsonify, current_app

logger = logging.getLogger(__name__)

predictions_bp = Blueprint('predictions', __name__, url_prefix='/api')


def get_model_service():
    """Get model service from app config"""
    return current_app.config.get('model_service')


@predictions_bp.post("/predict-v4/<path:course_id>")
def predict_course_v4(course_id: str):
    """Trigger batch prediction cho toàn khóa học"""
    try:
        # Get appropriate model for this course
        service = get_model_service()
        if not service:
            return jsonify({"error": "Model service not initialized"}), 500
        
        logger.info(f"Starting batch prediction for course {course_id} with model {service.model_name}")
        
        result_df = service.predict_course(course_id, save_db=True)

        if result_df is not None and not result_df.empty:
            avg_risk = float(result_df["fail_risk_score"].mean())
            
            return jsonify({
                "success": True,
                "course_id": course_id,
                "model_name": service.model_name,
                "model_version": getattr(service, 'model_version', 'v5.0.0'),
                "predicted_students": len(result_df),
                "avg_risk_score": avg_risk,
                "message": f"Successfully predicted {len(result_df)} students"
            })
        else:
            return jsonify({
                "success": False,
                "error": "No student features found or prediction failed"
            }), 400

    except Exception:
        logger.exception("Error during course prediction")
        return jsonify({"error": "Prediction failed"}), 500


@predictions_bp.post("/predict-v4/<int:user_id>/<path:course_id>")
def predict_student_v4(user_id: int, course_id: str):
    """Trigger on-demand prediction cho một sinh viên"""
    try:
        # Get appropriate model for this course
        service = get_model_service()
        if not service:
            return jsonify({"error": "Model service not initialized"}), 500
        
        logger.info(f"Predicting for user {user_id} in course {course_id} with model {service.model_name}")
        
        result = service.predict_student(course_id, user_id, save_db=True)

        if result:
            return jsonify({
                "success": True,
                "user_id": user_id,
                "course_id": course_id,
                "model_name": service.model_name,
                "model_version": "v4.0.0",
                "fail_risk_score": result["fail_risk_score"],
                "risk_level": result["risk_level"],
            })
        else:
            return jsonify({
                "success": False,
                "error": "No features found or prediction failed"
            }), 400

    except Exception:
        logger.exception("Error during student prediction")
        return jsonify({"error": "Prediction failed"}), 500
