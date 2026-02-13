"""
Shared helper functions for backend routes
"""
from typing import List, Dict, Any

# Risk threshold constants
RISK_HIGH_THRESHOLD = 70
RISK_MEDIUM_THRESHOLD = 40

# Allowed sort parameters (whitelist for SQL injection prevention)
ALLOWED_SORT_COLUMNS = {
    "risk_score": "p.fail_risk_score",
    "name": "full_name",
    "grade": "f.mooc_grade_percentage",
    "last_activity": "f.days_since_last_activity",
}
ALLOWED_SORT_ORDERS = {"asc", "desc"}


def classify_risk_level(score: float) -> str:
    """
    Classify risk level từ score
    
    Args:
        score: Risk score (0-100)
        
    Returns:
        'HIGH', 'MEDIUM', or 'LOW'
    """
    if score >= RISK_HIGH_THRESHOLD:
        return "HIGH"
    elif score >= RISK_MEDIUM_THRESHOLD:
        return "MEDIUM"
    else:
        return "LOW"


def get_completion_status(mooc_is_passed) -> str:
    """
    Get completion status from mooc_is_passed value
    
    Args:
        mooc_is_passed: Can be True/False, 1/0, "1"/"0", or None
        
    Returns:
        'completed', 'not_passed', or 'in_progress'
    """
    if mooc_is_passed in (True, 1, "1"):
        return "completed"
    elif mooc_is_passed in (False, 0, "0"):
        return "not_passed"
    else:
        return "in_progress"
