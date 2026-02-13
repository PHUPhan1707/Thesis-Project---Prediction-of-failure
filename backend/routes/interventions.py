"""
Interventions routes - Record teacher interventions
"""
import logging
from flask import Blueprint, jsonify, request

from ..db import execute

logger = logging.getLogger(__name__)

interventions_bp = Blueprint('interventions', __name__, url_prefix='/api')


@interventions_bp.post("/interventions/<int:user_id>/<path:course_id>")
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
