"""
Routes package - Flask Blueprints
"""
from .health import health_bp
from .courses import courses_bp
from .students import students_bp
from .dashboard import dashboard_bp
from .interventions import interventions_bp
from .predictions import predictions_bp
from .h5p_analytics import h5p_bp

__all__ = [
    'health_bp',
    'courses_bp', 
    'students_bp',
    'dashboard_bp',
    'interventions_bp',
    'predictions_bp',
    'h5p_bp',
]
