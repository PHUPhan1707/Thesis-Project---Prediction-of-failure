"""
Pipeline API Routes — SSE streaming, trigger, status.
"""
import logging
from flask import Blueprint, Response, jsonify, request, stream_with_context

logger = logging.getLogger(__name__)

pipeline_bp = Blueprint("pipeline", __name__, url_prefix="/api/pipeline")


@pipeline_bp.post("/start")
def start_pipeline():
    """
    Bắt đầu chạy full pipeline (background thread).

    Body (optional):
        {"session_id": "..."}   → MOOC session ID (nếu không dùng auto-login)
    """
    try:
        from ..pipeline_service import get_pipeline_service

        service = get_pipeline_service()

        if service.is_running:
            return jsonify({
                "success": False,
                "message": "Pipeline đang chạy, vui lòng đợi.",
            }), 409

        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id", "")

        service.start(session_id=session_id)

        return jsonify({
            "success": True,
            "message": "Pipeline đã bắt đầu",
        })

    except Exception:
        logger.exception("Error starting pipeline")
        return jsonify({"error": "Failed to start pipeline"}), 500


@pipeline_bp.get("/stream")
def stream_events():
    """
    SSE endpoint — stream real-time events từ pipeline.
    Frontend dùng EventSource để kết nối.
    """
    try:
        from ..pipeline_service import get_pipeline_service

        service = get_pipeline_service()

        def generate():
            for event_str in service.get_events():
                yield event_str

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            },
        )

    except Exception:
        logger.exception("Error streaming pipeline events")
        return jsonify({"error": "Stream failed"}), 500


@pipeline_bp.get("/status")
def pipeline_status():
    """Trạng thái hiện tại của pipeline."""
    try:
        from ..pipeline_service import get_pipeline_service
        from ..mooc_auth_service import get_mooc_auth

        service = get_pipeline_service()
        auth = get_mooc_auth()

        return jsonify({
            "running": service.is_running,
            "summary": service.summary,
            "mooc_auth": auth.status,
        })

    except Exception:
        logger.exception("Error getting pipeline status")
        return jsonify({"error": "Failed to get status"}), 500


@pipeline_bp.post("/stop")
def stop_pipeline():
    """Dừng pipeline đang chạy."""
    try:
        from ..pipeline_service import get_pipeline_service

        service = get_pipeline_service()
        if not service.is_running:
            return jsonify({
                "success": False,
                "message": "Pipeline không đang chạy.",
            }), 400

        service.stop()
        return jsonify({
            "success": True,
            "message": "Đã gửi lệnh dừng pipeline.",
        })

    except Exception:
        logger.exception("Error stopping pipeline")
        return jsonify({"error": "Failed to stop pipeline"}), 500


@pipeline_bp.post("/login-mooc")
def login_mooc():
    """Thủ công trigger MOOC login."""
    try:
        from ..mooc_auth_service import get_mooc_auth

        auth = get_mooc_auth()

        if not auth.is_configured:
            return jsonify({
                "success": False,
                "message": "MOOC_EMAIL và MOOC_PASSWORD chưa cấu hình trong .env",
            }), 400

        success = auth.login()

        return jsonify({
            "success": success,
            "message": "Login thành công" if success else "Login thất bại",
            "status": auth.status,
        })

    except Exception:
        logger.exception("Error logging in to MOOC")
        return jsonify({"error": "Login failed"}), 500
