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
