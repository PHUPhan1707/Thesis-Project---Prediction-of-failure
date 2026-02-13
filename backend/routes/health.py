"""
Health check routes
"""
import logging
from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)


@health_bp.get("/")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "2.0",
        "schema": "refactored",
        "message": "Teacher Dashboard Backend API V2"
    })
