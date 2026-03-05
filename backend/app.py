"""
Flask Backend API V2 - Refactored with Blueprints
Sử dụng student_features + predictions thay vì raw_data
"""
import os
import sys
import logging
from pathlib import Path
from flask import Flask
from flask_cors import CORS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add parent directory to path for direct execution
if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))


def _get_allowed_origins() -> list:
    """
    Đọc danh sách CORS origins từ biến môi trường CORS_ORIGINS.
    Mặc định chỉ cho phép localhost (development).
    Production: set CORS_ORIGINS=https://your-domain.com,https://dashboard.your-domain.com
    """
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


def create_app():
    """Factory function to create Flask app"""
    app = Flask(__name__)

    allowed_origins = _get_allowed_origins()
    CORS(app, origins=allowed_origins, supports_credentials=True)
    logger.info(f"CORS allowed origins: {allowed_origins}")

    # Initialize Inference Service (default model)
    model_service = None
    try:
        if __package__ in (None, ""):
            from backend.inference_service import InferenceService
        else:
            from .inference_service import InferenceService

        model_service = InferenceService()
        logger.info("InferenceService initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize InferenceService: {e}")
        model_service = None
    
    # Store model service in app config for access by blueprints
    app.config['model_service'] = model_service

    # ------------------------------------------------------------------
    # Register Blueprints
    # ------------------------------------------------------------------
    if __package__ in (None, ""):
        from backend.routes import (
            health_bp,
            courses_bp,
            students_bp,
            dashboard_bp,
            interventions_bp,
            predictions_bp,
            h5p_bp,
        )
    else:
        from .routes import (
            health_bp,
            courses_bp,
            students_bp,
            dashboard_bp,
            interventions_bp,
            predictions_bp,
            h5p_bp,
        )

    app.register_blueprint(health_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(interventions_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(h5p_bp)

    logger.info("All blueprints registered successfully")

    return app


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
