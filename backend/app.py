"""
Backend API cho Teacher Dashboard - Dropout Prediction System
Tích hợp với MySQL database và Model V4
"""
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

# Support running both:
# - python -m backend.app   (recommended)
# - python backend/app.py   (also works)
if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from backend.db import execute, fetch_all, get_db_config  # type: ignore
    from backend.model_v4_service import ModelV4Service  # type: ignore
else:
    from .db import execute, fetch_all, get_db_config
    from .model_v4_service import ModelV4Service


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def classify_risk_level(risk_score: float) -> str:
    """Phân loại mức độ rủi ro dựa trên điểm risk score"""
    if risk_score >= 70:
        return "HIGH"
    if risk_score >= 40:
        return "MEDIUM"
    return "LOW"


def generate_suggestions(student: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Tạo gợi ý can thiệp dựa trên các chỉ số của sinh viên
    """
    suggestions: List[Dict[str, Any]] = []

    days_inactive = student.get("days_since_last_activity") or 0
    grade = student.get("mooc_grade_percentage") or 0
    completion = student.get("mooc_completion_rate") or 0
    video_completion = student.get("video_completion_rate") or 0
    quiz_avg = student.get("quiz_avg_score") or 0
    discussion = student.get("discussion_total_interactions") or 0

    # Can thiệp khẩn cấp cho inactive
    if days_inactive > 14:
        suggestions.append(
            {
                "icon": "📞",
                "title": "Liên hệ khẩn cấp",
                "description": f"Sinh viên không hoạt động {days_inactive} ngày, cần liên hệ ngay để tìm hiểu khó khăn.",
                "priority": "high",
            }
        )
    elif days_inactive > 7:
        suggestions.append(
            {
                "icon": "📧",
                "title": "Gửi email nhắc nhở",
                "description": f"Sinh viên đã không hoạt động {days_inactive} ngày, nên gửi email nhắc nhở quay lại học.",
                "priority": "medium",
            }
        )

    # Hỗ trợ học thuật cho điểm thấp
    if grade < 40:
        suggestions.append(
            {
                "icon": "📝",
                "title": "Hỗ trợ học thuật",
                "description": "Điểm tổng kết hiện tại thấp, nên đề xuất buổi tư vấn 1-1 hoặc tài liệu ôn tập thêm.",
                "priority": "high",
            }
        )

    # Nhắc nhở tiến độ
    if completion < 30:
        suggestions.append(
            {
                "icon": "⏰",
                "title": "Nhắc nhở tiến độ",
                "description": "Tiến độ hoàn thành khóa học thấp, cần nhắc sinh viên về deadline và lộ trình học.",
                "priority": "medium",
            }
        )

    # Khuyến khích tham gia thảo luận
    if discussion == 0:
        suggestions.append(
            {
                "icon": "💬",
                "title": "Khuyến khích tham gia thảo luận",
                "description": "Sinh viên chưa có tương tác trên diễn đàn, nên khuyến khích đặt câu hỏi hoặc thảo luận.",
                "priority": "low",
            }
        )

    # Kiểm tra việc xem video
    if video_completion < 30:
        suggestions.append(
            {
                "icon": "🎥",
                "title": "Kiểm tra việc xem video",
                "description": "Tiến độ video rất thấp, cần kiểm tra vấn đề kỹ thuật hoặc cung cấp transcript/tài liệu thay thế.",
                "priority": "medium",
            }
        )

    # Củng cố kiến thức quiz
    if quiz_avg < 50:
        suggestions.append(
            {
                "icon": "📚",
                "title": "Củng cố kiến thức quiz",
                "description": "Điểm quiz trung bình thấp, nên cung cấp bài tập luyện thêm hoặc buổi giải đáp thắc mắc.",
                "priority": "medium",
            }
        )

    # Nếu không có vấn đề gì
    if not suggestions:
        suggestions.append(
            {
                "icon": "✅",
                "title": "Tiếp tục theo dõi",
                "description": "Sinh viên đang học ổn, chỉ cần tiếp tục theo dõi định kỳ.",
                "priority": "low",
            }
        )

    return suggestions


def create_app() -> Flask:
    """Factory function để tạo Flask app"""
    app = Flask(__name__)
    CORS(app)

    logger.info("Using DB config: %s", get_db_config())

    # Lazy singleton cho model service (load khi cần)
    service: Optional[ModelV4Service] = None

    def get_service() -> ModelV4Service:
        nonlocal service
        if service is None:
            service = ModelV4Service(
                model_path=os.getenv("MODEL_V4_PATH"),
                feature_fallback_csv=os.getenv("MODEL_V4_FEATURES_CSV"),
            )
        return service

    # ------------------------------------------------------------------
    # 1. Health Check
    # ------------------------------------------------------------------
    @app.get("/api/health")
    def health():
        """Kiểm tra trạng thái API"""
        return jsonify(
            {
                "status": "ok",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "Teacher Dashboard API",
            }
        )

    # ------------------------------------------------------------------
    # 2. Get Courses
    # ------------------------------------------------------------------
    @app.get("/api/courses")
    def get_courses():
        """Lấy danh sách khóa học và số lượng sinh viên"""
        try:
            rows = fetch_all(
                """
                SELECT course_id, COUNT(*) AS student_count
                FROM raw_data
                GROUP BY course_id
                ORDER BY course_id
                """
            )
            return jsonify({"courses": rows, "total": len(rows)})
        except Exception as e:
            logger.exception("Error loading courses")
            return jsonify({"error": "Database error"}), 500

    # ------------------------------------------------------------------
    # 3. Get Students (with filters)
    # ------------------------------------------------------------------
    @app.get("/api/students/<path:course_id>")
    def get_students(course_id: str):
        """Lấy danh sách sinh viên theo khóa học với filters"""
        risk_level = request.args.get("risk_level")
        sort_by = request.args.get("sort_by", "risk_score")
        order = request.args.get("order", "desc").lower()

        # Map sort parameters to columns
        sort_map = {
            "risk_score": "r.fail_risk_score",
            "name": "full_name",
            "grade": "r.mooc_grade_percentage",
            "last_activity": "r.days_since_last_activity",
        }
        sort_col = sort_map.get(sort_by, "r.fail_risk_score")
        sort_dir = "ASC" if order == "asc" else "DESC"

        # Build WHERE clause
        where = ["r.course_id = %s"]
        params: List[Any] = [course_id]

        if risk_level == "HIGH":
            where.append("r.fail_risk_score >= 70")
        elif risk_level == "MEDIUM":
            where.append("r.fail_risk_score >= 40 AND r.fail_risk_score < 70")
        elif risk_level == "LOW":
            where.append("r.fail_risk_score < 40")

        where_sql = " AND ".join(where)

        try:
            rows = fetch_all(
                f"""
                SELECT
                    r.user_id,
                    COALESCE(NULLIF(e.email, ''), g.email) AS email,
                    COALESCE(NULLIF(e.full_name_vn, ''), NULLIF(e.full_name, ''), NULLIF(g.full_name, '')) AS full_name,
                    e.username,
                    e.mssv,
                    r.fail_risk_score,
                    r.mooc_grade_percentage,
                    r.mooc_completion_rate,
                    r.days_since_last_activity,
                    r.mooc_is_passed
                FROM raw_data r
                LEFT JOIN enrollments e
                    ON r.user_id = e.user_id AND r.course_id = e.course_id
                LEFT JOIN mooc_grades g
                    ON r.user_id = g.user_id AND r.course_id = g.course_id
                WHERE {where_sql}
                ORDER BY {sort_col} {sort_dir}
                """,
                params,
            )

            # Add risk_level classification and completion_status
            for row in rows:
                score = float(row.get("fail_risk_score") or 0)
                row["risk_level"] = classify_risk_level(score)
                
                # Determine completion_status based on mooc_is_passed
                # Use truthiness check to handle both bool and int (1/0)
                mooc_is_passed = row.get("mooc_is_passed")
                if mooc_is_passed in (True, 1, "1"):
                    row["completion_status"] = "completed"
                elif mooc_is_passed in (False, 0, "0"):
                    row["completion_status"] = "not_passed"
                else:
                    row["completion_status"] = "in_progress"

            return jsonify({"students": rows, "total": len(rows), "course_id": course_id})
        except Exception:
            logger.exception("Error loading students for course %s", course_id)
            return jsonify({"error": "Database error"}), 500

    # ------------------------------------------------------------------
    # 4. Get Student Detail
    # ------------------------------------------------------------------
    @app.get("/api/student/<int:user_id>/<path:course_id>")
    def get_student_detail(user_id: int, course_id: str):
        """Lấy thông tin chi tiết của một sinh viên"""
        try:
            rows = fetch_all(
                """
                SELECT
                    r.*,
                    COALESCE(NULLIF(e.email, ''), g.email) AS email,
                    COALESCE(NULLIF(e.full_name_vn, ''), NULLIF(e.full_name, ''), NULLIF(g.full_name, '')) AS full_name,
                    e.username,
                    e.mssv
                FROM raw_data r
                LEFT JOIN enrollments e
                    ON r.user_id = e.user_id AND r.course_id = e.course_id
                LEFT JOIN mooc_grades g
                    ON r.user_id = g.user_id AND r.course_id = g.course_id
                WHERE r.user_id = %s AND r.course_id = %s
                """,
                (user_id, course_id),
            )
        except Exception:
            logger.exception("Error loading student detail")
            return jsonify({"error": "Database error"}), 500

        if not rows:
            return jsonify({"error": "Student not found"}), 404

        student = rows[0]

        score = float(student.get("fail_risk_score") or 0)
        student["fail_risk_score"] = score
        student["risk_level"] = classify_risk_level(score)
        student["suggestions"] = generate_suggestions(student)

        # Return formatted response
        response: Dict[str, Any] = {
            "user_id": int(student["user_id"]),
            "email": student.get("email"),
            "full_name": student.get("full_name"),
            "username": student.get("username"),
            "mssv": student.get("mssv"),
            "fail_risk_score": score,
            "risk_level": student["risk_level"],
            "mooc_grade_percentage": float(student.get("mooc_grade_percentage") or 0),
            "mooc_completion_rate": float(student.get("mooc_completion_rate") or 0),
            "days_since_last_activity": int(student.get("days_since_last_activity") or 0),
            "video_completion_rate": float(student.get("video_completion_rate") or 0),
            "quiz_avg_score": float(student.get("quiz_avg_score") or 0),
            "discussion_threads_count": int(student.get("discussion_threads_count") or 0),
            "suggestions": student["suggestions"],
        }

        return jsonify(response)

    # ------------------------------------------------------------------
    # 5. Get Course Statistics
    # ------------------------------------------------------------------
    @app.get("/api/statistics/<path:course_id>")
    def get_statistics(course_id: str):
        """Lấy thống kê tổng quan của khóa học"""
        try:
            rows = fetch_all(
                """
                SELECT
                    COUNT(*) AS total_students,
                    AVG(fail_risk_score) AS avg_risk_score,
                    AVG(mooc_grade_percentage) AS avg_grade,
                    AVG(mooc_completion_rate) AS avg_completion_rate,
                    -- Risk counts: CHỈ tính sinh viên CHƯA hoàn thành (mooc_is_passed != 1)
                    SUM(CASE WHEN fail_risk_score >= 70 AND mooc_is_passed != 1 THEN 1 ELSE 0 END) AS high_risk_count,
                    SUM(CASE WHEN fail_risk_score >= 40 AND fail_risk_score < 70 AND mooc_is_passed != 1 THEN 1 ELSE 0 END) AS medium_risk_count,
                    SUM(CASE WHEN fail_risk_score < 40 AND mooc_is_passed != 1 THEN 1 ELSE 0 END) AS low_risk_count,
                    -- Completion status counts
                    SUM(CASE WHEN mooc_is_passed = 1 THEN 1 ELSE 0 END) AS completed_count,
                    SUM(CASE WHEN mooc_is_passed = 0 THEN 1 ELSE 0 END) AS not_passed_count,
                    SUM(CASE WHEN mooc_is_passed IS NULL THEN 1 ELSE 0 END) AS in_progress_count
                FROM raw_data
                WHERE course_id = %s
                """,
                (course_id,),
            )
        except Exception:
            logger.exception("Error loading statistics for course %s", course_id)
            return jsonify({"error": "Database error"}), 500

        if not rows:
            return jsonify({"error": "Course not found"}), 404

        stats = rows[0]
        
        # Convert Decimal to float for averages
        for key in ["avg_risk_score", "avg_grade", "avg_completion_rate"]:
            stats[key] = float(stats.get(key) or 0)
        
        # Convert Decimal to int for counts
        for key in ["total_students", "high_risk_count", "medium_risk_count", "low_risk_count",
                    "completed_count", "not_passed_count", "in_progress_count"]:
            stats[key] = int(stats.get(key) or 0)

        return jsonify({"course_id": course_id, "statistics": stats})

    # ------------------------------------------------------------------
    # 6. Record Intervention
    # ------------------------------------------------------------------
    def _ensure_interventions_table() -> None:
        """Đảm bảo bảng interventions tồn tại"""
        execute(
            """
            CREATE TABLE IF NOT EXISTS interventions (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                course_id VARCHAR(255) NOT NULL,
                action VARCHAR(255) NOT NULL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_course (user_id, course_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        )

    @app.post("/api/interventions/<int:user_id>/<path:course_id>")
    def record_intervention(user_id: int, course_id: str):
        """Ghi nhận hành động can thiệp của giảng viên"""
        data = request.get_json(silent=True) or {}
        action = (data.get("action") or "").strip()
        notes = (data.get("notes") or "").strip()

        if not action:
            return jsonify({"error": "action is required"}), 400

        try:
            _ensure_interventions_table()
            execute(
                """
                INSERT INTO interventions (user_id, course_id, action, notes)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, course_id, action, notes),
            )
        except Exception:
            logger.exception("Error recording intervention")
            return jsonify({"error": "Database error"}), 500

        return jsonify(
            {
                "success": True,
                "message": "Intervention recorded successfully",
                "user_id": user_id,
                "course_id": course_id,
                "action": action,
            }
        )

    # ------------------------------------------------------------------
    # 7. Dashboard Summary (NEW)
    # ------------------------------------------------------------------
    @app.get("/api/dashboard-summary/<path:course_id>")
    def get_dashboard_summary(course_id: str):
        """Lấy thông tin tổng hợp dashboard cho giảng viên"""
        try:
            # Get today's tasks - HIGH risk students needing intervention
            today_tasks_rows = fetch_all(
                """
                SELECT
                    r.user_id,
                    COALESCE(NULLIF(e.full_name_vn, ''), NULLIF(e.full_name, ''), NULLIF(g.full_name, '')) AS full_name,
                    COALESCE(NULLIF(e.email, ''), g.email) AS email,
                    r.fail_risk_score,
                    r.days_since_last_activity,
                    r.mooc_completion_rate,
                    r.mooc_grade_percentage
                FROM raw_data r
                LEFT JOIN enrollments e ON r.user_id = e.user_id AND r.course_id = e.course_id
                LEFT JOIN mooc_grades g ON r.user_id = g.user_id AND r.course_id = g.course_id
                WHERE r.course_id = %s AND r.fail_risk_score >= 70
                ORDER BY r.fail_risk_score DESC, r.days_since_last_activity DESC
                LIMIT 10
                """,
                (course_id,),
            )

            # Transform to today_tasks format
            today_tasks = []
            for row in today_tasks_rows:
                score = float(row.get("fail_risk_score") or 0)
                days_inactive = int(row.get("days_since_last_activity") or 0)
                
                # Determine urgency and reason
                if score >= 85 or days_inactive > 14:
                    urgency = "critical"
                    reason = f"Rủi ro rất cao ({score:.0f}%)" if score >= 85 else f"Không hoạt động {days_inactive} ngày"
                elif score >= 70 or days_inactive > 7:
                    urgency = "high"
                    reason = f"Rủi ro cao ({score:.0f}%)" if score >= 70 else f"Không hoạt động {days_inactive} ngày"
                else:
                    urgency = "medium"
                    reason = f"Cần theo dõi (risk: {score:.0f}%)"
                
                today_tasks.append({
                    "user_id": int(row["user_id"]),
                    "full_name": row.get("full_name") or "Chưa có tên",
                    "email": row.get("email") or "",
                    "risk_level": classify_risk_level(score),
                    "fail_risk_score": score,
                    "reason": reason,
                    "urgency": urgency,
                })

            # Get recent alerts - students with issues in last 7 days
            recent_alerts_rows = fetch_all(
                """
                SELECT
                    r.user_id,
                    COALESCE(NULLIF(e.full_name_vn, ''), NULLIF(e.full_name, ''), NULLIF(g.full_name, '')) AS full_name,
                    r.fail_risk_score,
                    r.days_since_last_activity,
                    r.mooc_completion_rate
                FROM raw_data r
                LEFT JOIN enrollments e ON r.user_id = e.user_id AND r.course_id = e.course_id
                LEFT JOIN mooc_grades g ON r.user_id = g.user_id AND r.course_id = g.course_id
                WHERE r.course_id = %s
                    AND (r.fail_risk_score >= 60 OR r.days_since_last_activity > 5)
                ORDER BY r.fail_risk_score DESC
                LIMIT 8
                """,
                (course_id,),
            )

            # Transform to alerts format
            recent_alerts = []
            for idx, row in enumerate(recent_alerts_rows):
                score = float(row.get("fail_risk_score") or 0)
                days_inactive = int(row.get("days_since_last_activity") or 0)
                completion = float(row.get("mooc_completion_rate") or 0)
                
                # Determine alert type
                if days_inactive > 7:
                    alert_type = "inactive"
                    message = f"Không hoạt động {days_inactive} ngày"
                elif score >= 70:
                    alert_type = "risk_increase"
                    message = f"Nguy cơ cao: {score:.0f}%"
                elif completion < 20:
                    alert_type = "low_progress"
                    message = f"Tiến độ thấp: {completion:.0f}%"
                else:
                    alert_type = "risk_increase"
                    message = f"Cần theo dõi: {score:.0f}%"
                
                recent_alerts.append({
                    "id": idx + 1,
                    "user_id": int(row["user_id"]),
                    "full_name": row.get("full_name") or "Chưa có tên",
                    "alert_type": alert_type,
                    "message": message,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

            # Get quick stats
            stats_rows = fetch_all(
                """
                SELECT
                    SUM(CASE WHEN fail_risk_score >= 70 THEN 1 ELSE 0 END) AS new_high_risk_count,
                    SUM(CASE WHEN days_since_last_activity > 7 THEN 1 ELSE 0 END) AS inactive_students_count
                FROM raw_data
                WHERE course_id = %s
                """,
                (course_id,),
            )
            
            quick_stats = {
                "new_high_risk_count": int(stats_rows[0].get("new_high_risk_count") or 0) if stats_rows else 0,
                "inactive_students_count": int(stats_rows[0].get("inactive_students_count") or 0) if stats_rows else 0,
                "intervention_pending": len(today_tasks),
            }

            return jsonify({
                "course_id": course_id,
                "today_tasks": today_tasks,
                "recent_alerts": recent_alerts,
                "quick_stats": quick_stats,
            })
        except Exception:
            logger.exception("Error loading dashboard summary for course %s", course_id)
            return jsonify({"error": "Database error"}), 500

    # ------------------------------------------------------------------
    # 8. Urgent Students (NEW)
    # ------------------------------------------------------------------
    @app.get("/api/students/<path:course_id>/urgent")
    def get_urgent_students(course_id: str):
        """Lấy danh sách sinh viên cần can thiệp khẩn cấp"""
        try:
            rows = fetch_all(
                """
                SELECT
                    r.user_id,
                    COALESCE(NULLIF(e.email, ''), g.email) AS email,
                    COALESCE(NULLIF(e.full_name_vn, ''), NULLIF(e.full_name, ''), NULLIF(g.full_name, '')) AS full_name,
                    e.username,
                    e.mssv,
                    r.fail_risk_score,
                    r.mooc_grade_percentage,
                    r.mooc_completion_rate,
                    r.days_since_last_activity
                FROM raw_data r
                LEFT JOIN enrollments e ON r.user_id = e.user_id AND r.course_id = e.course_id
                LEFT JOIN mooc_grades g ON r.user_id = g.user_id AND r.course_id = g.course_id
                WHERE r.course_id = %s
                    AND (r.fail_risk_score >= 70 OR r.days_since_last_activity > 7)
                ORDER BY r.fail_risk_score DESC, r.days_since_last_activity DESC
                LIMIT 20
                """,
                (course_id,),
            )

            # Add risk_level classification
            for row in rows:
                score = float(row.get("fail_risk_score") or 0)
                row["risk_level"] = classify_risk_level(score)

            return jsonify({
                "students": rows,
                "total": len(rows),
                "course_id": course_id,
            })
        except Exception:
            logger.exception("Error loading urgent students for course %s", course_id)
            return jsonify({"error": "Database error"}), 500

    # ------------------------------------------------------------------
    # 9. Model V4 Prediction Endpoints (Optional)
    # ------------------------------------------------------------------
    @app.get("/api/predict-v4/<path:course_id>")
    def predict_v4_course(course_id: str):
        """Dự đoán risk score cho tất cả sinh viên trong khóa học bằng Model V4"""
        save_db = request.args.get("save_db", "0") in ("1", "true", "True")
        
        try:
            df = get_service().predict_course(course_id, save_db=save_db)
            return jsonify(
                {
                    "success": True,
                    "model": "fm101_model_v4",
                    "course_id": course_id,
                    "total": int(len(df)),
                    "students": df.to_dict(orient="records"),
                    "saved_to_db": bool(save_db),
                }
            )
        except Exception:
            logger.exception("Error predicting with model v4 for course %s", course_id)
            return jsonify({"error": "Prediction error"}), 500

    @app.get("/api/predict-v4/<int:user_id>/<path:course_id>")
    def predict_v4_student(user_id: int, course_id: str):
        """Dự đoán risk score cho một sinh viên cụ thể bằng Model V4"""
        save_db = request.args.get("save_db", "0") in ("1", "true", "True")
        
        try:
            payload = get_service().predict_student(course_id, user_id, save_db=save_db)
            if payload is None:
                return jsonify({"success": False, "error": "Student not found"}), 404
            return jsonify({"success": True, "saved_to_db": bool(save_db), **payload})
        except Exception:
            logger.exception("Error predicting with model v4 for user %s", user_id)
            return jsonify({"error": "Prediction error"}), 500

    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
