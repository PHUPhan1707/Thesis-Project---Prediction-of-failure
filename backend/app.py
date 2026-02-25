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


def create_app():
    """Factory function to create Flask app"""
    app = Flask(__name__)
    CORS(app)

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
    app.run(host="0.0.0.0", port=port, debug=True)
