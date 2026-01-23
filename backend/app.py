"""
Teacher Dashboard Backend API
Flask REST API để cung cấp dữ liệu cho dashboard giảng viên
"""
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 4000,
    "database": "dropout_prediction_db",
    "user": "dropout_user",
    "password": "dropout_pass_123"
}

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend


# ============================================================
# Database Helper Functions
# ============================================================

def get_db_connection():
    """Tạo kết nối database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"Error connecting to database: {e}")
        return None


def execute_query(query: str, params: tuple = None) -> Optional[List[Dict]]:
    """Execute query và trả về results as list of dicts"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        return results
    except Error as e:
        logger.error(f"Error executing query: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


# ============================================================
# API Endpoints
# ============================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "Teacher Dashboard API"
    })


@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Lấy danh sách courses có trong database"""
    query = """
    SELECT DISTINCT course_id, COUNT(*) as student_count
    FROM raw_data
    GROUP BY course_id
    ORDER BY course_id
    """
    
    results = execute_query(query)
    
    if results is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    return jsonify({
        "courses": results,
        "total": len(results)
    })


@app.route('/api/students/<course_id>', methods=['GET'])
def get_students(course_id: str):
    """
    Lấy danh sách học viên trong course với risk scores
    Query params:
        - risk_level: HIGH, MEDIUM, LOW (optional)
        - sort_by: risk_score, name, grade (default: risk_score)
        - order: desc, asc (default: desc)
    """
    risk_level = request.args.get('risk_level', None)
    sort_by = request.args.get('sort_by', 'risk_score')
    order = request.args.get('order', 'desc')
    
    # Build base query
    query = """
    SELECT 
        r.user_id,
        e.email,
        e.full_name,
        r.fail_risk_score,
        r.mooc_grade_percentage,
        r.mooc_completion_rate,
        r.days_since_last_activity,
        r.last_activity,
        r.video_completion_rate,
        r.quiz_avg_score,
        r.discussion_total_interactions,
        r.h5p_completion_rate
    FROM raw_data r
    LEFT JOIN enrollments e ON r.user_id = e.user_id AND r.course_id = e.course_id
    WHERE r.course_id = %s
    """
    
    params = [course_id]
    
    # Add risk level filter if provided
    if risk_level:
        if risk_level == 'HIGH':
            query += " AND r.fail_risk_score >= 70"
        elif risk_level == 'MEDIUM':
            query += " AND r.fail_risk_score >= 40 AND r.fail_risk_score < 70"
        elif risk_level == 'LOW':
            query += " AND r.fail_risk_score < 40"
    
    # Add sorting
    sort_column_map = {
        'risk_score': 'r.fail_risk_score',
        'name': 'e.full_name',
        'grade': 'r.mooc_grade_percentage',
        'last_activity': 'r.last_activity'
    }
    
    sort_column = sort_column_map.get(sort_by, 'r.fail_risk_score')
    query += f" ORDER BY {sort_column} {order.upper()}"
    
    results = execute_query(query, tuple(params))
    
    if results is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    # Add risk_level classification
    for student in results:
        risk_score = student.get('fail_risk_score', 0)
        if risk_score >= 70:
            student['risk_level'] = 'HIGH'
        elif risk_score >= 40:
            student['risk_level'] = 'MEDIUM'
        else:
            student['risk_level'] = 'LOW'
        
        # Format datetime
        if student.get('last_activity'):
            student['last_activity'] = student['last_activity'].isoformat() if hasattr(student['last_activity'], 'isoformat') else str(student['last_activity'])
    
    return jsonify({
        "students": results,
        "total": len(results),
        "course_id": course_id
    })


@app.route('/api/student/<int:user_id>/<course_id>', methods=['GET'])
def get_student_detail(user_id: int, course_id: str):
    """Lấy chi tiết thông tin một học viên"""
    query = """
    SELECT 
        r.*,
        e.email,
        e.full_name,
        e.username,
        e.mssv,
        e.class_code,
        e.department,
        e.faculty,
        e.enrollment_id,
        e.mode,
        e.is_active,
        e.created as enrollment_date
    FROM raw_data r
    LEFT JOIN enrollments e ON r.user_id = e.user_id AND r.course_id = e.course_id
    WHERE r.user_id = %s AND r.course_id = %s
    """
    
    results = execute_query(query, (user_id, course_id))
    
    if results is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    if not results:
        return jsonify({"error": "Student not found"}), 404
    
    student = results[0]
    
    # Add risk_level classification
    risk_score = student.get('fail_risk_score', 0)
    if risk_score >= 70:
        student['risk_level'] = 'HIGH'
    elif risk_score >= 40:
        student['risk_level'] = 'MEDIUM'
    else:
        student['risk_level'] = 'LOW'
    
    # Format datetime fields
    for field in ['last_activity', 'enrollment_date', 'extracted_at']:
        if student.get(field) and hasattr(student[field], 'isoformat'):
            student[field] = student[field].isoformat()
    
    # Generate intervention suggestions
    suggestions = generate_suggestions(student)
    student['suggestions'] = suggestions
    
    return jsonify(student)


@app.route('/api/statistics/<course_id>', methods=['GET'])
def get_course_statistics(course_id: str):
    """Lấy thống kê tổng quan cho course"""
    query = """
    SELECT 
        COUNT(*) as total_students,
        AVG(fail_risk_score) as avg_risk_score,
        AVG(mooc_grade_percentage) as avg_grade,
        AVG(mooc_completion_rate) as avg_completion_rate,
        SUM(CASE WHEN fail_risk_score >= 70 THEN 1 ELSE 0 END) as high_risk_count,
        SUM(CASE WHEN fail_risk_score >= 40 AND fail_risk_score < 70 THEN 1 ELSE 0 END) as medium_risk_count,
        SUM(CASE WHEN fail_risk_score < 40 THEN 1 ELSE 0 END) as low_risk_count,
        SUM(CASE WHEN days_since_last_activity > 7 THEN 1 ELSE 0 END) as inactive_students,
        SUM(CASE WHEN mooc_grade_percentage < 40 THEN 1 ELSE 0 END) as failing_students
    FROM raw_data
    WHERE course_id = %s
    """
    
    results = execute_query(query, (course_id,))
    
    if results is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    if not results:
        return jsonify({"error": "Course not found"}), 404
    
    stats = results[0]
    
    # Calculate percentages
    total = stats['total_students'] or 1
    stats['high_risk_percentage'] = (stats['high_risk_count'] / total) * 100
    stats['medium_risk_percentage'] = (stats['medium_risk_count'] / total) * 100
    stats['low_risk_percentage'] = (stats['low_risk_count'] / total) * 100
    
    return jsonify({
        "course_id": course_id,
        "statistics": stats
    })


@app.route('/api/interventions/<int:user_id>/<course_id>', methods=['POST'])
def record_intervention(user_id: int, course_id: str):
    """Ghi nhận hành động can thiệp (for future implementation)"""
    data = request.get_json()
    action = data.get('action', '')
    notes = data.get('notes', '')
    
    # TODO: Store intervention in database
    # For now, just return success
    
    logger.info(f"Intervention recorded for user {user_id} in course {course_id}: {action}")
    
    return jsonify({
        "success": True,
        "message": "Intervention recorded successfully",
        "user_id": user_id,
        "course_id": course_id,
        "action": action
    })


# ============================================================
# Helper Functions
# ============================================================

def generate_suggestions(student_data: Dict) -> List[Dict]:
    """Tạo gợi ý can thiệp dựa trên student data"""
    suggestions = []
    
    # Check inactivity
    days_inactive = student_data.get('days_since_last_activity', 0)
    if days_inactive > 14:
        suggestions.append({
            "icon": "📞",
            "title": "Liên hệ khẩn cấp",
            "description": f"Sinh viên không hoạt động {days_inactive} ngày. Liên hệ trực tiếp qua điện thoại hoặc tin nhắn.",
            "priority": "high"
        })
    elif days_inactive > 7:
        suggestions.append({
            "icon": "📧",
            "title": "Gửi email nhắc nhở",
            "description": f"Sinh viên không hoạt động {days_inactive} ngày. Gửi email nhắc nhở quay lại học.",
            "priority": "medium"
        })
    
    # Check grade
    grade = student_data.get('mooc_grade_percentage', 100)
    if grade < 40:
        suggestions.append({
            "icon": "👨‍🏫",
            "title": "Tư vấn học tập 1-1",
            "description": f"Điểm số thấp ({grade:.1f}%). Tổ chức buổi ôn tập hoặc tư vấn cá nhân.",
            "priority": "high"
        })
        suggestions.append({
            "icon": "📚",
            "title": "Tài liệu bổ sung",
            "description": "Cung cấp tài liệu học tập bổ sung và bài tập luyện tập.",
            "priority": "medium"
        })
    
    # Check completion rate
    completion = student_data.get('mooc_completion_rate', 100)
    if completion < 30:
        suggestions.append({
            "icon": "⏰",
            "title": "Nhắc nhở lộ trình",
            "description": f"Tiến độ hoàn thành thấp ({completion:.1f}%). Nhắc nhở về deadline và lộ trình học tập.",
            "priority": "medium"
        })
    
    # Check discussion participation
    interactions = student_data.get('discussion_total_interactions', 1)
    if interactions == 0:
        suggestions.append({
            "icon": "💬",
            "title": "Khuyến khích thảo luận",
            "description": "Sinh viên chưa tham gia thảo luận. Khuyến khích tham gia forum và ghép nhóm học tập.",
            "priority": "low"
        })
    
    # Check video completion
    video_completion = student_data.get('video_completion_rate', 100)
    if video_completion < 30:
        suggestions.append({
            "icon": "🎥",
            "title": "Kiểm tra video",
            "description": f"Tỷ lệ xem video thấp ({video_completion:.1f}%). Kiểm tra vấn đề kỹ thuật hoặc cung cấp transcript.",
            "priority": "medium"
        })
    
    # Check quiz performance
    quiz_score = student_data.get('quiz_avg_score', 100)
    if quiz_score < 50:
        suggestions.append({
            "icon": "✍️",
            "title": "Hỗ trợ quiz",
            "description": f"Điểm quiz thấp ({quiz_score:.1f}%). Tổ chức buổi giải đáp thắc mắc.",
            "priority": "medium"
        })
    
    # General high risk
    risk_score = student_data.get('fail_risk_score', 0)
    if risk_score >= 70:
        suggestions.insert(0, {
            "icon": "🚨",
            "title": "Can thiệp ngay",
            "description": f"Nguy cơ rất cao ({risk_score:.1f}%). Ưu tiên can thiệp và lập kế hoạch học tập cá nhân hóa.",
            "priority": "high"
        })
    
    # Default if no issues
    if not suggestions:
        suggestions.append({
            "icon": "✅",
            "title": "Học tốt",
            "description": "Sinh viên đang học tốt. Tiếp tục theo dõi và khuyến khích.",
            "priority": "low"
        })
    
    return suggestions


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    logger.info("Starting Teacher Dashboard API...")
    logger.info(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    # Test database connection
    conn = get_db_connection()
    if conn:
        logger.info("✓ Database connection successful")
        conn.close()
    else:
        logger.error("✗ Database connection failed")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
