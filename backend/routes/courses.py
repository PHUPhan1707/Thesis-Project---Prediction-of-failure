"""
Courses routes
"""
import logging
from flask import Blueprint, jsonify

from ..db import fetch_all

logger = logging.getLogger(__name__)

courses_bp = Blueprint('courses', __name__, url_prefix='/api')


@courses_bp.get("/courses")
def get_courses():
    """Lấy danh sách khóa học đã có prediction model, kèm tên đầy đủ từ enrollments"""
    try:
        rows = fetch_all("""
            SELECT
                e.course_id,
                COUNT(DISTINCT e.user_id)  AS student_count,
                MAX(e.course_name)         AS course_name
            FROM enrollments e
            WHERE e.course_id IN (
                SELECT DISTINCT course_id FROM predictions WHERE is_latest = TRUE
            )
            GROUP BY e.course_id
            ORDER BY e.course_id
        """)
        return jsonify({"courses": rows, "total": len(rows)})
    except Exception as e:
        logger.exception("Error loading courses")
        return jsonify({"error": "Database error"}), 500
