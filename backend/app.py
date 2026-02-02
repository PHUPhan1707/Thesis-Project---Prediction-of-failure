"""
Flask Backend API V2 - Refactored for new schema
Sử dụng student_features + predictions thay vì raw_data
"""
import os
import logging
from datetime import datetime
from typing import List, Any
from flask import Flask, jsonify, request
from flask_cors import CORS

# Conditional imports
if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from backend.db import fetch_one, fetch_all, execute  # type: ignore
    from backend.model_v4_service_v2 import ModelV4ServiceV2, get_model_for_course  # type: ignore
else:
    from .db import fetch_one, fetch_all, execute
    from .model_v4_service_v2 import ModelV4ServiceV2, get_model_for_course

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app():
    """Factory function to create Flask app"""
    app = Flask(__name__)
    CORS(app)

    # Initialize Model V4 Service (default model)
    try:
        model_service = ModelV4ServiceV2(model_name='fm101_v4')
        logger.info("Default Model V4 Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Model V4 Service: {e}")
        model_service = None

    # ------------------------------------------------------------------
    # Helper Functions
    # ------------------------------------------------------------------
    
    def classify_risk_level(score: float) -> str:
        """Classify risk level từ score"""
        if score >= 70:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    def generate_suggestions(student_data: dict) -> List[dict]:
        """Generate intervention suggestions"""
        if model_service:
            return model_service.generate_suggestions(student_data)
        return []

    # ------------------------------------------------------------------
    # 1. Health Check
    # ------------------------------------------------------------------
    @app.get("/")
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "version": "2.0",
            "schema": "refactored",
            "message": "Teacher Dashboard Backend API V2"
        })

    # ------------------------------------------------------------------
    # 2. Get Courses
    # ------------------------------------------------------------------
    @app.get("/api/courses")
    def get_courses():
        """Lấy danh sách khóa học từ enrollments"""
        try:
            rows = fetch_all("""
                SELECT course_id, COUNT(*) AS student_count
                FROM enrollments
                GROUP BY course_id
                ORDER BY course_id
            """)
            return jsonify({"courses": rows, "total": len(rows)})
        except Exception as e:
            logger.exception("Error loading courses")
            return jsonify({"error": "Database error"}), 500

    # ------------------------------------------------------------------
    # 3. Get Students (V2 - từ student_features + predictions)
    # ------------------------------------------------------------------
    @app.get("/api/students/<path:course_id>")
    def get_students(course_id: str):
        """Lấy danh sách sinh viên với predictions"""
        risk_level = request.args.get("risk_level")
        sort_by = request.args.get("sort_by", "risk_score")
        order = request.args.get("order", "desc").lower()

        # Map sort parameters
        sort_map = {
            "risk_score": "p.fail_risk_score",
            "name": "full_name",
            "grade": "f.mooc_grade_percentage",
            "last_activity": "f.days_since_last_activity",
        }
        sort_col = sort_map.get(sort_by, "p.fail_risk_score")
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
                
                # Get appropriate model for this course
                service = get_model_for_course(course_id)
                pred_result = service.predict_student(course_id, user_id, save_to_db=True)
                
                if pred_result:
                    student["fail_risk_score"] = pred_result["fail_risk_score"]
                    student["risk_level"] = pred_result["risk_level"]
                    student["model_name"] = pred_result["model_name"]
                else:
                    student["fail_risk_score"] = 50.0
                    student["risk_level"] = "MEDIUM"

            # Generate suggestions
            student["suggestions"] = generate_suggestions(student)

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
                "suggestions": student["suggestions"],
                "model_name": student.get("model_name"),
                "predicted_at": student.get("predicted_at"),
            }

            return jsonify(response)

        except Exception:
            logger.exception("Error loading student detail")
            return jsonify({"error": "Database error"}), 500

    # ------------------------------------------------------------------
    # 5. Get Course Statistics (V2)
    # ------------------------------------------------------------------
    @app.get("/api/statistics/<path:course_id>")
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

    # ------------------------------------------------------------------
    # 5b. Dashboard Summary (Việc cần làm hôm nay + Cảnh báo gần đây)
    # ------------------------------------------------------------------
    @app.get("/api/dashboard-summary/<path:course_id>")
    def get_dashboard_summary(course_id: str):
        """Lấy tổng quan dashboard: today_tasks, recent_alerts, quick_stats"""
        try:
            # Lấy danh sách sinh viên có prediction + features (chưa hoàn thành)
            rows = fetch_all(
                """
                SELECT
                    f.user_id,
                    COALESCE(NULLIF(e.full_name_vn, ''), NULLIF(e.full_name, ''), 'Sinh viên') AS full_name,
                    COALESCE(NULLIF(e.email, ''), '') AS email,
                    COALESCE(p.fail_risk_score, 50) AS fail_risk_score,
                    COALESCE(p.risk_level, 'MEDIUM') AS risk_level,
                    f.mooc_completion_rate,
                    f.days_since_last_activity,
                    f.mooc_grade_percentage,
                    p.predicted_at
                FROM student_features f
                LEFT JOIN enrollments e ON f.user_id = e.user_id AND f.course_id = e.course_id
                LEFT JOIN predictions p ON f.user_id = p.user_id AND f.course_id = p.course_id AND p.is_latest = TRUE
                WHERE f.course_id = %s
                  AND (f.mooc_is_passed IS NULL OR f.mooc_is_passed = 0)
                ORDER BY COALESCE(p.fail_risk_score, 0) DESC, f.days_since_last_activity DESC
                """,
                (course_id,),
            )

            if not rows:
                return jsonify({
                    "course_id": course_id,
                    "today_tasks": [],
                    "recent_alerts": [],
                    "quick_stats": {
                        "new_high_risk_count": 0,
                        "inactive_students_count": 0,
                        "intervention_pending": 0,
                    },
                })

            def _created_at(dt):
                if dt is None:
                    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
                return dt.isoformat() if hasattr(dt, "isoformat") else str(dt)

            # Chuẩn hóa risk_level và số
            high_risk_count = 0
            inactive_count = 0
            today_tasks = []
            recent_alerts = []
            alert_id = 0

            for r in rows:
                score = float(r.get("fail_risk_score") or 50)
                risk_level = (r.get("risk_level") or "MEDIUM").upper()
                if risk_level not in ("HIGH", "MEDIUM", "LOW"):
                    risk_level = "HIGH" if score >= 70 else ("MEDIUM" if score >= 40 else "LOW")

                days_inactive = int(r.get("days_since_last_activity") or 0)
                completion = float(r.get("mooc_completion_rate") or 0)
                predicted_at = r.get("predicted_at")

                if risk_level == "HIGH":
                    high_risk_count += 1
                if days_inactive >= 7:
                    inactive_count += 1

                # Việc cần làm hôm nay: HIGH risk hoặc MEDIUM + inactive
                urgency = "medium"
                reason = ""
                if risk_level == "HIGH":
                    urgency = "critical"
                    reason = "Nguy cơ bỏ học cao"
                elif risk_level == "MEDIUM":
                    urgency = "high"
                    reason = "Nguy cơ trung bình"
                elif days_inactive >= 7:
                    urgency = "high"
                    reason = "Không hoạt động {} ngày".format(days_inactive)
                else:
                    reason = "Theo dõi tiến độ"

                today_tasks.append({
                    "user_id": int(r["user_id"]),
                    "full_name": r.get("full_name") or "Sinh viên",
                    "email": r.get("email") or "",
                    "risk_level": risk_level,
                    "fail_risk_score": round(score, 1),
                    "reason": reason,
                    "urgency": "critical" if risk_level == "HIGH" else ("high" if risk_level == "MEDIUM" or days_inactive >= 7 else "medium"),
                })

                # Cảnh báo gần đây: risk_increase (HIGH), inactive, low_progress
                if risk_level == "HIGH":
                    alert_id += 1
                    recent_alerts.append({
                        "id": alert_id,
                        "user_id": int(r["user_id"]),
                        "full_name": r.get("full_name") or "Sinh viên",
                        "alert_type": "risk_increase",
                        "message": "Nguy cơ bỏ học cao ({}%)".format(round(score, 1)),
                        "created_at": _created_at(predicted_at),
                    })
                if days_inactive >= 7:
                    alert_id += 1
                    recent_alerts.append({
                        "id": alert_id,
                        "user_id": int(r["user_id"]),
                        "full_name": r.get("full_name") or "Sinh viên",
                        "alert_type": "inactive",
                        "message": "Không hoạt động {} ngày".format(days_inactive),
                        "created_at": _created_at(predicted_at),
                    })
                if completion < 30 and completion > 0:
                    alert_id += 1
                    recent_alerts.append({
                        "id": alert_id,
                        "user_id": int(r["user_id"]),
                        "full_name": r.get("full_name") or "Sinh viên",
                        "alert_type": "low_progress",
                        "message": "Tiến độ thấp ({:.0f}%)".format(completion),
                        "created_at": _created_at(predicted_at),
                    })

            # Giới hạn today_tasks (top 10), recent_alerts (top 20)
            today_tasks = today_tasks[:10]
            recent_alerts = recent_alerts[:20]

            # Sắp xếp cảnh báo: risk_increase trước, rồi inactive, rồi low_progress
            def alert_order(a):
                order = {"risk_increase": 0, "inactive": 1, "low_progress": 2}
                return (order.get(a["alert_type"], 3), -a["user_id"])

            recent_alerts.sort(key=alert_order)

            return jsonify({
                "course_id": course_id,
                "today_tasks": today_tasks,
                "recent_alerts": recent_alerts,
                "quick_stats": {
                    "new_high_risk_count": high_risk_count,
                    "inactive_students_count": inactive_count,
                    "intervention_pending": high_risk_count,
                },
            })
        except Exception:
            logger.exception("Error loading dashboard summary for course %s", course_id)
            return jsonify({"error": "Database error"}), 500

    # ------------------------------------------------------------------
    # 6. Record Intervention
    # ------------------------------------------------------------------
    @app.post("/api/interventions/<int:user_id>/<path:course_id>")
    def record_intervention(user_id: int, course_id: str):
        """Ghi lại can thiệp của giảng viên"""
        data = request.get_json()
        intervention_type = data.get("type")
        notes = data.get("notes", "")

        try:
            # Create interventions table if not exists
            execute("""
                CREATE TABLE IF NOT EXISTS interventions (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    course_id VARCHAR(255) NOT NULL,
                    intervention_type VARCHAR(100),
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_course (user_id, course_id)
                )
            """)

            # Insert intervention
            execute(
                """
                INSERT INTO interventions (user_id, course_id, intervention_type, notes)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, course_id, intervention_type, notes),
            )

            return jsonify({"success": True, "message": "Intervention recorded"})

        except Exception:
            logger.exception("Error recording intervention")
            return jsonify({"error": "Database error"}), 500

    # ------------------------------------------------------------------
    # 7. Predict V4 (Batch - entire course)
    # ------------------------------------------------------------------
    @app.post("/api/predict-v4/<path:course_id>")
    def predict_course_v4(course_id: str):
        """Trigger batch prediction cho toàn khóa học"""
        try:
            # Get appropriate model for this course
            service = get_model_for_course(course_id)
            
            logger.info(f"Starting batch prediction for course {course_id} with model {service.model_name}")
            
            result_df = service.predict_course(course_id, save_to_db=True)

            if result_df is not None and not result_df.empty:
                avg_risk = float(result_df["fail_risk_score"].mean())
                
                return jsonify({
                    "success": True,
                    "course_id": course_id,
                    "model_name": service.model_name,
                    "model_version": service.model_version,
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

    # ------------------------------------------------------------------
    # 8. Predict V4 (Single student - on-demand)
    # ------------------------------------------------------------------
    @app.post("/api/predict-v4/<int:user_id>/<path:course_id>")
    def predict_student_v4(user_id: int, course_id: str):
        """Trigger on-demand prediction cho một sinh viên"""
        try:
            # Get appropriate model for this course
            service = get_model_for_course(course_id)
            
            logger.info(f"Predicting for user {user_id} in course {course_id} with model {service.model_name}")
            
            result = service.predict_student(course_id, user_id, save_to_db=True)

            if result:
                return jsonify({
                    "success": True,
                    "user_id": user_id,
                    "course_id": course_id,
                    "model_name": result["model_name"],
                    "model_version": result["model_version"],
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

    return app


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
