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
    from backend.model_v4_service import ModelV4Service  # type: ignore
else:
    from .db import fetch_one, fetch_all, execute
    from .model_v4_service import ModelV4Service

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
        model_service = ModelV4Service()
        # Add model_name attribute for compatibility
        model_service.model_name = 'fm101_v4'
        logger.info("Default Model V4 Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Model V4 Service: {e}")
        model_service = None
    
    def get_model_for_course(course_id: str):
        """Get appropriate model service for a course"""
        # For now, return the default model service
        # Can be extended later to use different models per course
        return model_service

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
        """Lấy danh sách khóa học từ student_features (chỉ course có dữ liệu đầy đủ)"""
        try:
            rows = fetch_all("""
                SELECT 
                    course_id, 
                    COUNT(DISTINCT user_id) AS student_count
                FROM student_features
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
                pred_result = service.predict_student(course_id, user_id, save_db=True)
                
                if pred_result:
                    student["fail_risk_score"] = pred_result["fail_risk_score"]
                    student["risk_level"] = pred_result["risk_level"]
                    student["model_name"] = service.model_name
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
            
            result_df = service.predict_course(course_id, save_db=True)

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

    # ------------------------------------------------------------------
    # 9. H5P Content Performance Analytics
    # ------------------------------------------------------------------
    @app.get("/api/h5p-analytics/<path:course_id>/low-performance")
    def get_low_performance_h5p_contents(course_id: str):
        """
        Lấy danh sách các bài H5P có điểm trung bình thấp và tỉ lệ hoàn thành kém
        trong một khóa học
        """
        try:
            min_students = int(request.args.get('min_students', 5))  # Ít nhất 5 sinh viên làm
            limit = int(request.args.get('limit', 20))  # Top 20 bài kém nhất
            
            query = """
                SELECT 
                    content_id,
                    content_title,
                    folder_name,
                    COUNT(DISTINCT user_id) as total_students,
                    COUNT(DISTINCT CASE WHEN finished > 0 THEN user_id END) as completed_students,
                    COUNT(DISTINCT CASE WHEN percentage < 100 THEN user_id END) as students_not_max_score,
                    ROUND(COUNT(DISTINCT CASE WHEN percentage < 100 THEN user_id END) * 100.0 / COUNT(DISTINCT user_id), 2) as not_max_rate,
                    ROUND(COUNT(DISTINCT CASE WHEN finished > 0 THEN user_id END) * 100.0 / COUNT(DISTINCT user_id), 2) as completion_rate,
                    ROUND(AVG(percentage), 2) as avg_score,
                    ROUND(AVG(CASE WHEN finished > 0 THEN percentage END), 2) as avg_score_completed,
                    MIN(percentage) as min_score,
                    MAX(percentage) as max_score,
                    SUM(score) as total_score,
                    SUM(max_score) as total_max_score,
                    ROUND(AVG(time_spent), 0) as avg_time_spent_seconds
                FROM h5p_scores
                WHERE course_id = %s
                GROUP BY content_id, content_title, folder_name
                HAVING total_students >= %s
                ORDER BY students_not_max_score DESC, not_max_rate DESC, avg_score ASC
                LIMIT %s
            """
            
            results = fetch_all(query, (course_id, min_students, limit))
            
            if not results:
                return jsonify({
                    "success": True,
                    "course_id": course_id,
                    "contents": [],
                    "message": "No H5P content data found"
                })
            
            contents = []
            for row in results:
                # Phân loại mức độ khó khăn
                avg_score = float(row.get("avg_score") or 0)
                completion_rate = float(row.get("completion_rate") or 0)
                not_max_rate = float(row.get("not_max_rate") or 0)
                
                # Bài khó nếu nhiều sinh viên không đạt max hoặc điểm TB thấp
                if not_max_rate > 80 or avg_score < 50 or completion_rate < 50:
                    difficulty_level = "HIGH"  # Bài rất khó
                elif not_max_rate > 60 or avg_score < 70 or completion_rate < 70:
                    difficulty_level = "MEDIUM"  # Bài khá khó
                else:
                    difficulty_level = "LOW"  # Bài dễ
                
                contents.append({
                    "content_id": row["content_id"],
                    "content_title": row["content_title"],
                    "folder_name": row["folder_name"],
                    "total_students": row["total_students"],
                    "completed_students": row["completed_students"],
                    "students_not_max_score": row["students_not_max_score"],
                    "not_max_rate": row["not_max_rate"],
                    "completion_rate": row["completion_rate"],
                    "avg_score": row["avg_score"],
                    "avg_score_completed": row["avg_score_completed"],
                    "min_score": row["min_score"],
                    "max_score": row["max_score"],
                    "avg_time_spent_minutes": round(float(row.get("avg_time_spent_seconds") or 0) / 60, 1),
                    "difficulty_level": difficulty_level,
                    "needs_attention": not_max_rate > 70 or avg_score < 60 or completion_rate < 60
                })
            
            # Tính statistics tổng quát
            stats = {
                "total_contents_analyzed": len(contents),
                "avg_completion_rate": round(sum(c["completion_rate"] for c in contents) / len(contents), 2) if contents else 0,
                "avg_score_all": round(sum(c["avg_score"] for c in contents) / len(contents), 2) if contents else 0,
                "high_difficulty_count": sum(1 for c in contents if c["difficulty_level"] == "HIGH"),
                "needs_attention_count": sum(1 for c in contents if c["needs_attention"])
            }
            
            return jsonify({
                "success": True,
                "course_id": course_id,
                "statistics": stats,
                "contents": contents
            })
            
        except Exception:
            logger.exception(f"Error analyzing H5P performance for course {course_id}")
            return jsonify({"error": "Failed to analyze H5P content performance"}), 500

    @app.get("/api/h5p-analytics/<path:course_id>/content/<int:content_id>")
    def get_h5p_content_detail(course_id: str, content_id: int):
        """
        Lấy chi tiết performance của một bài H5P cụ thể:
        - Sinh viên nào làm tốt, ai làm kém
        - Phân bố điểm số
        """
        try:
            # Lấy thông tin tổng quan của content
            summary_query = """
                SELECT 
                    content_id,
                    content_title,
                    folder_name,
                    COUNT(DISTINCT user_id) as total_students,
                    COUNT(DISTINCT CASE WHEN finished > 0 THEN user_id END) as completed_students,
                    ROUND(AVG(percentage), 2) as avg_score,
                    MIN(percentage) as min_score,
                    MAX(percentage) as max_score
                FROM h5p_scores
                WHERE course_id = %s AND content_id = %s
                GROUP BY content_id, content_title, folder_name
            """
            
            summary = fetch_one(summary_query, (course_id, content_id))
            
            if not summary:
                return jsonify({
                    "success": False,
                    "error": "Content not found"
                }), 404
            
            # Lấy chi tiết từng sinh viên
            students_query = """
                SELECT 
                    h.user_id,
                    e.full_name,
                    e.email,
                    e.mssv,
                    h.score,
                    h.max_score,
                    h.percentage,
                    h.finished,
                    h.opened,
                    h.time_spent,
                    FROM_UNIXTIME(h.opened) as opened_time,
                    FROM_UNIXTIME(h.finished) as finished_time
                FROM h5p_scores h
                LEFT JOIN enrollments e ON h.user_id = e.user_id AND h.course_id = e.course_id
                WHERE h.course_id = %s AND h.content_id = %s
                ORDER BY h.percentage DESC, h.finished DESC
            """
            
            students_data = fetch_all(students_query, (course_id, content_id))
            
            # Phân loại sinh viên
            high_performers = []  # Điểm >= 80
            medium_performers = []  # 50 <= Điểm < 80
            low_performers = []  # Điểm < 50
            not_attempted = []  # Chưa làm
            
            for student in students_data:
                student_info = {
                    "user_id": student["user_id"],
                    "full_name": student["full_name"],
                    "email": student["email"],
                    "mssv": student["mssv"],
                    "score": student["score"],
                    "max_score": student["max_score"],
                    "percentage": float(student["percentage"]),
                    "is_completed": student["finished"] > 0,
                    "time_spent_minutes": round(float(student.get("time_spent") or 0) / 60, 1),
                    "opened_time": student["opened_time"].isoformat() if student["opened_time"] else None,
                    "finished_time": student["finished_time"].isoformat() if student["finished_time"] else None
                }
                
                if student["finished"] == 0:
                    not_attempted.append(student_info)
                elif student["percentage"] >= 80:
                    high_performers.append(student_info)
                elif student["percentage"] >= 50:
                    medium_performers.append(student_info)
                else:
                    low_performers.append(student_info)
            
            # Phân bố điểm (score distribution)
            score_distribution = {
                "excellent": len([s for s in students_data if s["percentage"] >= 90]),  # 90-100
                "good": len([s for s in students_data if 80 <= s["percentage"] < 90]),  # 80-89
                "average": len([s for s in students_data if 70 <= s["percentage"] < 80]),  # 70-79
                "below_average": len([s for s in students_data if 50 <= s["percentage"] < 70]),  # 50-69
                "poor": len([s for s in students_data if 0 < s["percentage"] < 50]),  # 1-49
                "not_attempted": len([s for s in students_data if s["finished"] == 0])  # 0
            }
            
            return jsonify({
                "success": True,
                "course_id": course_id,
                "content": {
                    "content_id": summary["content_id"],
                    "content_title": summary["content_title"],
                    "folder_name": summary["folder_name"],
                    "total_students": summary["total_students"],
                    "completed_students": summary["completed_students"],
                    "completion_rate": round(summary["completed_students"] * 100.0 / summary["total_students"], 2),
                    "avg_score": summary["avg_score"],
                    "min_score": summary["min_score"],
                    "max_score": summary["max_score"]
                },
                "score_distribution": score_distribution,
                "student_performance": {
                    "high_performers": high_performers,
                    "medium_performers": medium_performers,
                    "low_performers": low_performers,
                    "not_attempted": not_attempted
                }
            })
            
        except Exception:
            logger.exception(f"Error getting H5P content detail for content {content_id}")
            return jsonify({"error": "Failed to get content detail"}), 500

    @app.get("/api/h5p-analytics/<path:course_id>/student/<int:user_id>")
    def get_student_h5p_performance(course_id: str, user_id: int):
        """
        Lấy chi tiết performance H5P của một sinh viên:
        - Bài nào làm tốt, bài nào làm kém
        - Bài nào chưa làm
        """
        try:
            # Lấy thông tin sinh viên
            student_query = """
                SELECT user_id, full_name, email, mssv
                FROM enrollments
                WHERE course_id = %s AND user_id = %s
            """
            student = fetch_one(student_query, (course_id, user_id))
            
            if not student:
                return jsonify({
                    "success": False,
                    "error": "Student not found"
                }), 404
            
            # Lấy danh sách H5P đã làm
            completed_query = """
                SELECT 
                    content_id,
                    content_title,
                    folder_name,
                    score,
                    max_score,
                    percentage,
                    time_spent,
                    FROM_UNIXTIME(opened) as opened_time,
                    FROM_UNIXTIME(finished) as finished_time
                FROM h5p_scores
                WHERE course_id = %s AND user_id = %s
                ORDER BY percentage ASC
            """
            
            completed = fetch_all(completed_query, (course_id, user_id))
            
            # Phân loại các bài đã làm
            excellent = []  # >= 90
            good = []  # 80-89
            needs_improvement = []  # 50-79
            poor = []  # < 50
            in_progress = []  # opened but not finished
            
            for item in completed:
                content_info = {
                    "content_id": item["content_id"],
                    "content_title": item["content_title"],
                    "folder_name": item["folder_name"],
                    "score": item["score"],
                    "max_score": item["max_score"],
                    "percentage": float(item["percentage"]),
                    "time_spent_minutes": round(float(item.get("time_spent") or 0) / 60, 1),
                    "opened_time": item["opened_time"].isoformat() if item["opened_time"] else None,
                    "finished_time": item["finished_time"].isoformat() if item["finished_time"] else None
                }
                
                if item["finished_time"] is None:
                    in_progress.append(content_info)
                elif item["percentage"] >= 90:
                    excellent.append(content_info)
                elif item["percentage"] >= 80:
                    good.append(content_info)
                elif item["percentage"] >= 50:
                    needs_improvement.append(content_info)
                else:
                    poor.append(content_info)
            
            # Tính statistics
            total_attempted = len([c for c in completed if c["finished_time"]])
            avg_score = sum(c["percentage"] for c in completed if c["finished_time"]) / total_attempted if total_attempted > 0 else 0
            
            return jsonify({
                "success": True,
                "course_id": course_id,
                "student": {
                    "user_id": student["user_id"],
                    "full_name": student["full_name"],
                    "email": student["email"],
                    "mssv": student["mssv"]
                },
                "statistics": {
                    "total_attempted": total_attempted,
                    "total_in_progress": len(in_progress),
                    "avg_score": round(avg_score, 2),
                    "excellent_count": len(excellent),
                    "good_count": len(good),
                    "needs_improvement_count": len(needs_improvement),
                    "poor_count": len(poor)
                },
                "performance": {
                    "excellent": excellent,
                    "good": good,
                    "needs_improvement": needs_improvement,
                    "poor": poor,
                    "in_progress": in_progress
                }
            })
            
        except Exception:
            logger.exception(f"Error getting student H5P performance for user {user_id}")
            return jsonify({"error": "Failed to get student H5P performance"}), 500

    return app


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
