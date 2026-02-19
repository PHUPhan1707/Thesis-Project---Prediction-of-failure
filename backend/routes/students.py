"""
Students routes - List, Detail, Statistics
"""
import logging
from flask import Blueprint, jsonify, request, current_app

from ..db import fetch_one, fetch_all
from ..utils.helpers import (
    classify_risk_level, 
    get_completion_status,
    ALLOWED_SORT_COLUMNS,
    ALLOWED_SORT_ORDERS
)

logger = logging.getLogger(__name__)

students_bp = Blueprint('students', __name__, url_prefix='/api')


@students_bp.get("/students/<path:course_id>")
def get_students(course_id: str):
    """Lấy danh sách sinh viên với predictions"""
    risk_level = request.args.get("risk_level")
    sort_by = request.args.get("sort_by", "risk_score")
    order = request.args.get("order", "desc").lower()

    # Validate sort parameters against whitelist to prevent SQL injection
    if sort_by not in ALLOWED_SORT_COLUMNS:
        sort_by = "risk_score"  # Default to safe value
    if order not in ALLOWED_SORT_ORDERS:
        order = "desc"  # Default to safe value

    sort_col = ALLOWED_SORT_COLUMNS[sort_by]
    sort_dir = "ASC" if order == "asc" else "DESC"

    # Build WHERE clause for risk filtering
    risk_where = ""
    if risk_level == "HIGH":
        risk_where = "AND p.fail_risk_score >= 70"
    elif risk_level == "MEDIUM":
        risk_where = "AND p.fail_risk_score >= 40 AND p.fail_risk_score < 70"
    elif risk_level == "LOW":
        risk_where = "AND p.fail_risk_score < 40"

    try:
        rows = fetch_all(
            f"""
            SELECT
                f.user_id,
                COALESCE(NULLIF(e.email, ''), g.email) AS email,
                COALESCE(NULLIF(e.full_name_vn, ''), NULLIF(e.full_name, ''), NULLIF(g.full_name, '')) AS full_name,
                e.username,
                e.mssv,
                COALESCE(p.fail_risk_score, 50) AS fail_risk_score,
                f.mooc_grade_percentage,
                f.mooc_completion_rate,
                f.days_since_last_activity,
                f.mooc_is_passed,
                p.model_name,
                p.predicted_at
            FROM student_features f
            LEFT JOIN enrollments e ON f.user_id = e.user_id AND f.course_id = e.course_id
            LEFT JOIN mooc_grades g ON f.user_id = g.user_id AND f.course_id = g.course_id
            LEFT JOIN predictions p ON f.user_id = p.user_id AND f.course_id = p.course_id AND p.is_latest = TRUE
            WHERE f.course_id = %s {risk_where}
            ORDER BY {sort_col} {sort_dir}
            """,
            (course_id,),
        )

        # Add risk_level and completion_status
        for row in rows:
            score = float(row.get("fail_risk_score") or 50)
            row["risk_level"] = classify_risk_level(score)
            row["completion_status"] = get_completion_status(row.get("mooc_is_passed"))

        return jsonify({"students": rows, "total": len(rows), "course_id": course_id})
    except Exception:
        logger.exception("Error loading students for course %s", course_id)
        return jsonify({"error": "Database error"}), 500


@students_bp.get("/student/<int:user_id>/<path:course_id>")
def get_student_detail(user_id: int, course_id: str):
    """Lấy thông tin chi tiết của sinh viên"""
    try:
        # Get student features
        student = fetch_one(
            """
            SELECT
                f.*,
                COALESCE(NULLIF(e.email, ''), g.email) AS email,
                COALESCE(NULLIF(e.full_name_vn, ''), NULLIF(e.full_name, ''), NULLIF(g.full_name, '')) AS full_name,
                e.username,
                e.mssv,
                p.fail_risk_score,
                p.risk_level,
                p.model_name,
                p.predicted_at
            FROM student_features f
            LEFT JOIN enrollments e ON f.user_id = e.user_id AND f.course_id = e.course_id
            LEFT JOIN mooc_grades g ON f.user_id = g.user_id AND f.course_id = g.course_id
            LEFT JOIN predictions p ON f.user_id = p.user_id AND f.course_id = p.course_id AND p.is_latest = TRUE
            WHERE f.user_id = %s AND f.course_id = %s
            """,
            (user_id, course_id),
        )

        if not student:
            return jsonify({"error": "Student not found"}), 404

        # Convert to native types
        for key in ["mooc_grade_percentage", "mooc_completion_rate", "video_completion_rate", "quiz_avg_score"]:
            if key in student:
                student[key] = float(student.get(key) or 0)

        for key in ["days_since_last_activity", "discussion_threads_count", "quiz_attempts"]:
            if key in student:
                student[key] = int(student.get(key) or 0)

        # If no prediction, trigger on-demand prediction
        if student.get("fail_risk_score") is None:
            logger.info(f"No prediction found for user {user_id}, triggering prediction...")
            
            # Get model service from app context
            model_service = current_app.config.get('model_service')
            if model_service:
                pred_result = model_service.predict_student(course_id, user_id, save_db=True)
                
                if pred_result:
                    student["fail_risk_score"] = pred_result["fail_risk_score"]
                    student["risk_level"] = pred_result["risk_level"]
                    student["model_name"] = model_service.model_name
                else:
                    student["fail_risk_score"] = 50.0
                    student["risk_level"] = "MEDIUM"
            else:
                student["fail_risk_score"] = 50.0
                student["risk_level"] = "MEDIUM"

        # Generate suggestions
        suggestions = []
        model_service = current_app.config.get('model_service')
        if model_service:
            suggestions = model_service.generate_suggestions(student)

        # Build response
        response = {
            "user_id": student["user_id"],
            "course_id": student["course_id"],
            "full_name": student.get("full_name"),
            "email": student.get("email"),
            "username": student.get("username"),
            "mssv": student.get("mssv"),
            "fail_risk_score": float(student.get("fail_risk_score") or 50),
            "risk_level": student.get("risk_level") or "MEDIUM",
            "mooc_grade_percentage": float(student.get("mooc_grade_percentage") or 0),
            "mooc_completion_rate": float(student.get("mooc_completion_rate") or 0),
            "days_since_last_activity": int(student.get("days_since_last_activity") or 0),
            "video_completion_rate": float(student.get("video_completion_rate") or 0),
            "quiz_avg_score": float(student.get("quiz_avg_score") or 0),
            "discussion_threads_count": int(student.get("discussion_threads_count") or 0),
            "suggestions": suggestions,
            "model_name": student.get("model_name"),
            "predicted_at": student.get("predicted_at"),
        }

        return jsonify(response)

    except Exception:
        logger.exception("Error loading student detail")
        return jsonify({"error": "Database error"}), 500


@students_bp.get("/student/<int:user_id>/<path:course_id>/explain")
def get_student_explanation(user_id: int, course_id: str):
    """SHAP explanation for a single student's risk prediction"""
    try:
        model_service = current_app.config.get('model_service')
        if not model_service:
            return jsonify({"error": "Model service not available"}), 503

        result = model_service.explain_student(course_id, user_id)
        if result is None:
            return jsonify({"error": "Student not found or no data available"}), 404

        return jsonify(result)
    except Exception:
        logger.exception("Error generating SHAP explanation for user %s course %s", user_id, course_id)
        return jsonify({"error": "Failed to generate explanation"}), 500


@students_bp.get("/statistics/<path:course_id>")
def get_statistics(course_id: str):
    """Lấy thống kê từ student_features + predictions"""
    try:
        rows = fetch_all(
            """
            SELECT
                COUNT(*) AS total_students,
                AVG(COALESCE(p.fail_risk_score, 50)) AS avg_risk_score,
                AVG(f.mooc_grade_percentage) AS avg_grade,
                AVG(f.mooc_completion_rate) AS avg_completion_rate,
                
                -- Risk counts (chỉ students chưa hoàn thành)
                SUM(CASE WHEN p.fail_risk_score >= 70 AND f.mooc_is_passed != 1 THEN 1 ELSE 0 END) AS high_risk_count,
                SUM(CASE WHEN p.fail_risk_score >= 40 AND p.fail_risk_score < 70 AND f.mooc_is_passed != 1 THEN 1 ELSE 0 END) AS medium_risk_count,
                SUM(CASE WHEN p.fail_risk_score < 40 AND f.mooc_is_passed != 1 THEN 1 ELSE 0 END) AS low_risk_count,
                
                -- Completion status counts
                SUM(CASE WHEN f.mooc_is_passed = 1 THEN 1 ELSE 0 END) AS completed_count,
                SUM(CASE WHEN f.mooc_is_passed = 0 THEN 1 ELSE 0 END) AS not_passed_count,
                SUM(CASE WHEN f.mooc_is_passed IS NULL THEN 1 ELSE 0 END) AS in_progress_count
                
            FROM student_features f
            LEFT JOIN predictions p ON f.user_id = p.user_id 
                AND f.course_id = p.course_id 
                AND p.is_latest = TRUE
            WHERE f.course_id = %s
            """,
            (course_id,),
        )
    except Exception:
        logger.exception("Error loading statistics for course %s", course_id)
        return jsonify({"error": "Database error"}), 500

    if not rows:
        return jsonify({"error": "Course not found"}), 404

    stats = rows[0]
    
    # Convert types
    for key in ["avg_risk_score", "avg_grade", "avg_completion_rate"]:
        stats[key] = float(stats.get(key) or 0)
    
    for key in ["total_students", "high_risk_count", "medium_risk_count", "low_risk_count",
                "completed_count", "not_passed_count", "in_progress_count"]:
        stats[key] = int(stats.get(key) or 0)

    return jsonify({"course_id": course_id, "statistics": stats})
