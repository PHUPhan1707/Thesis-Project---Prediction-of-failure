"""
H5P Analytics routes - H5P content performance analysis
"""
import logging
from flask import Blueprint, jsonify, request

from ..db import fetch_one, fetch_all

logger = logging.getLogger(__name__)

h5p_bp = Blueprint('h5p_analytics', __name__, url_prefix='/api/h5p-analytics')


@h5p_bp.get("/<path:course_id>/low-performance")
def get_low_performance_h5p_contents(course_id: str):
    """
    Lấy danh sách các bài H5P có điểm trung bình thấp và tỉ lệ hoàn thành kém
    trong một khóa học
    """
    try:
        min_students = int(request.args.get('min_students', 5))
        limit = int(request.args.get('limit', 20))
        
        query = """
            SELECT 
                content_id,
                content_title,
                folder_name,
                COUNT(DISTINCT user_id) as total_students,
                COUNT(DISTINCT CASE WHEN finished > 0 THEN user_id END) as completed_students,
                COUNT(DISTINCT CASE WHEN percentage < 100 THEN user_id END) as students_not_max_score,
                ROUND(COUNT(DISTINCT CASE WHEN percentage < 100 THEN user_id END) * 100.0 / COUNT(DISTINCT user_id), 2) as not_max_rate,
                ROUND(COUNT(DISTINCT CASE WHEN finished > 0 THEN user_id END) * 100.0 / COUNT(DISTINCT user_id), 2) as completion_rate,
                ROUND(AVG(percentage), 2) as avg_score,
                ROUND(AVG(CASE WHEN finished > 0 THEN percentage END), 2) as avg_score_completed,
                MIN(percentage) as min_score,
                MAX(percentage) as max_score,
                SUM(score) as total_score,
                SUM(max_score) as total_max_score,
                ROUND(AVG(time_spent), 0) as avg_time_spent_seconds
            FROM h5p_scores
            WHERE course_id = %s
            GROUP BY content_id, content_title, folder_name
            HAVING total_students >= %s
            ORDER BY students_not_max_score DESC, not_max_rate DESC, avg_score ASC
            LIMIT %s
        """
        
        results = fetch_all(query, (course_id, min_students, limit))
        
        if not results:
            return jsonify({
                "success": True,
                "course_id": course_id,
                "contents": [],
                "message": "No H5P content data found"
            })
        
        contents = []
        for row in results:
            avg_score = float(row.get("avg_score") or 0)
            completion_rate = float(row.get("completion_rate") or 0)
            not_max_rate = float(row.get("not_max_rate") or 0)
            
            # Phân loại mức độ khó khăn
            if not_max_rate > 80 or avg_score < 50 or completion_rate < 50:
                difficulty_level = "HIGH"
            elif not_max_rate > 60 or avg_score < 70 or completion_rate < 70:
                difficulty_level = "MEDIUM"
            else:
                difficulty_level = "LOW"
            
            contents.append({
                "content_id": row["content_id"],
                "content_title": row["content_title"],
                "folder_name": row["folder_name"],
                "total_students": row["total_students"],
                "completed_students": row["completed_students"],
                "students_not_max_score": row["students_not_max_score"],
                "not_max_rate": row["not_max_rate"],
                "completion_rate": row["completion_rate"],
                "avg_score": row["avg_score"],
                "avg_score_completed": row["avg_score_completed"],
                "min_score": row["min_score"],
                "max_score": row["max_score"],
                "avg_time_spent_minutes": round(float(row.get("avg_time_spent_seconds") or 0) / 60, 1),
                "difficulty_level": difficulty_level,
                "needs_attention": not_max_rate > 70 or avg_score < 60 or completion_rate < 60
            })
        
        stats = {
            "total_contents_analyzed": len(contents),
            "avg_completion_rate": round(sum(c["completion_rate"] for c in contents) / len(contents), 2) if contents else 0,
            "avg_score_all": round(sum(c["avg_score"] for c in contents) / len(contents), 2) if contents else 0,
            "high_difficulty_count": sum(1 for c in contents if c["difficulty_level"] == "HIGH"),
            "needs_attention_count": sum(1 for c in contents if c["needs_attention"])
        }
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "statistics": stats,
            "contents": contents
        })
        
    except Exception:
        logger.exception(f"Error analyzing H5P performance for course {course_id}")
        return jsonify({"error": "Failed to analyze H5P content performance"}), 500


@h5p_bp.get("/<path:course_id>/content/<int:content_id>")
def get_h5p_content_detail(course_id: str, content_id: int):
    """
    Lấy chi tiết performance của một bài H5P cụ thể
    """
    try:
        summary_query = """
            SELECT 
                content_id,
                content_title,
                folder_name,
                COUNT(DISTINCT user_id) as total_students,
                COUNT(DISTINCT CASE WHEN finished > 0 THEN user_id END) as completed_students,
                ROUND(AVG(percentage), 2) as avg_score,
                MIN(percentage) as min_score,
                MAX(percentage) as max_score
            FROM h5p_scores
            WHERE course_id = %s AND content_id = %s
            GROUP BY content_id, content_title, folder_name
        """
        
        summary = fetch_one(summary_query, (course_id, content_id))
        
        if not summary:
            return jsonify({"success": False, "error": "Content not found"}), 404
        
        students_query = """
            SELECT 
                h.user_id,
                e.full_name,
                e.email,
                e.mssv,
                h.score,
                h.max_score,
                h.percentage,
                h.finished,
                h.opened,
                h.time_spent,
                FROM_UNIXTIME(h.opened) as opened_time,
                FROM_UNIXTIME(h.finished) as finished_time
            FROM h5p_scores h
            LEFT JOIN enrollments e ON h.user_id = e.user_id AND h.course_id = e.course_id
            WHERE h.course_id = %s AND h.content_id = %s
            ORDER BY h.percentage DESC, h.finished DESC
        """
        
        students_data = fetch_all(students_query, (course_id, content_id))
        
        high_performers = []
        medium_performers = []
        low_performers = []
        not_attempted = []
        
        for student in students_data:
            student_info = {
                "user_id": student["user_id"],
                "full_name": student["full_name"],
                "email": student["email"],
                "mssv": student["mssv"],
                "score": student["score"],
                "max_score": student["max_score"],
                "percentage": float(student["percentage"]),
                "is_completed": student["finished"] > 0,
                "time_spent_minutes": round(float(student.get("time_spent") or 0) / 60, 1),
                "opened_time": student["opened_time"].isoformat() if student["opened_time"] else None,
                "finished_time": student["finished_time"].isoformat() if student["finished_time"] else None
            }
            
            if student["finished"] == 0:
                not_attempted.append(student_info)
            elif student["percentage"] >= 80:
                high_performers.append(student_info)
            elif student["percentage"] >= 50:
                medium_performers.append(student_info)
            else:
                low_performers.append(student_info)
        
        score_distribution = {
            "excellent": len([s for s in students_data if s["percentage"] >= 90]),
            "good": len([s for s in students_data if 80 <= s["percentage"] < 90]),
            "average": len([s for s in students_data if 70 <= s["percentage"] < 80]),
            "below_average": len([s for s in students_data if 50 <= s["percentage"] < 70]),
            "poor": len([s for s in students_data if 0 < s["percentage"] < 50]),
            "not_attempted": len([s for s in students_data if s["finished"] == 0])
        }
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "content": {
                "content_id": summary["content_id"],
                "content_title": summary["content_title"],
                "folder_name": summary["folder_name"],
                "total_students": summary["total_students"],
                "completed_students": summary["completed_students"],
                "completion_rate": round(summary["completed_students"] * 100.0 / summary["total_students"], 2),
                "avg_score": summary["avg_score"],
                "min_score": summary["min_score"],
                "max_score": summary["max_score"]
            },
            "score_distribution": score_distribution,
            "student_performance": {
                "high_performers": high_performers,
                "medium_performers": medium_performers,
                "low_performers": low_performers,
                "not_attempted": not_attempted
            }
        })
        
    except Exception:
        logger.exception(f"Error getting H5P content detail for content {content_id}")
        return jsonify({"error": "Failed to get content detail"}), 500


@h5p_bp.get("/<path:course_id>/student/<int:user_id>")
def get_student_h5p_performance(course_id: str, user_id: int):
    """
    Lấy chi tiết performance H5P của một sinh viên
    """
    try:
        student_query = """
            SELECT user_id, full_name, email, mssv
            FROM enrollments
            WHERE course_id = %s AND user_id = %s
        """
        student = fetch_one(student_query, (course_id, user_id))
        
        if not student:
            return jsonify({"success": False, "error": "Student not found"}), 404
        
        completed_query = """
            SELECT 
                content_id,
                content_title,
                folder_name,
                score,
                max_score,
                percentage,
                time_spent,
                FROM_UNIXTIME(opened) as opened_time,
                FROM_UNIXTIME(finished) as finished_time
            FROM h5p_scores
            WHERE course_id = %s AND user_id = %s
            ORDER BY percentage ASC
        """
        
        completed = fetch_all(completed_query, (course_id, user_id))
        
        excellent = []
        good = []
        needs_improvement = []
        poor = []
        in_progress = []
        
        for item in completed:
            content_info = {
                "content_id": item["content_id"],
                "content_title": item["content_title"],
                "folder_name": item["folder_name"],
                "score": item["score"],
                "max_score": item["max_score"],
                "percentage": float(item["percentage"]),
                "time_spent_minutes": round(float(item.get("time_spent") or 0) / 60, 1),
                "opened_time": item["opened_time"].isoformat() if item["opened_time"] else None,
                "finished_time": item["finished_time"].isoformat() if item["finished_time"] else None
            }
            
            if item["finished_time"] is None:
                in_progress.append(content_info)
            elif item["percentage"] >= 90:
                excellent.append(content_info)
            elif item["percentage"] >= 80:
                good.append(content_info)
            elif item["percentage"] >= 50:
                needs_improvement.append(content_info)
            else:
                poor.append(content_info)
        
        total_attempted = len([c for c in completed if c["finished_time"]])
        avg_score = sum(c["percentage"] for c in completed if c["finished_time"]) / total_attempted if total_attempted > 0 else 0
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "student": {
                "user_id": student["user_id"],
                "full_name": student["full_name"],
                "email": student["email"],
                "mssv": student["mssv"]
            },
            "statistics": {
                "total_attempted": total_attempted,
                "total_in_progress": len(in_progress),
                "avg_score": round(avg_score, 2),
                "excellent_count": len(excellent),
                "good_count": len(good),
                "needs_improvement_count": len(needs_improvement),
                "poor_count": len(poor)
            },
            "performance": {
                "excellent": excellent,
                "good": good,
                "needs_improvement": needs_improvement,
                "poor": poor,
                "in_progress": in_progress
            }
        })
        
    except Exception:
        logger.exception(f"Error getting student H5P performance for user {user_id}")
        return jsonify({"error": "Failed to get student H5P performance"}), 500
