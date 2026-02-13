"""
Dashboard routes - Dashboard summary
"""
import logging
from datetime import datetime
from flask import Blueprint, jsonify

from ..db import fetch_all
from ..utils.helpers import classify_risk_level

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api')


@dashboard_bp.get("/dashboard-summary/<path:course_id>")
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
                risk_level = classify_risk_level(score)

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
