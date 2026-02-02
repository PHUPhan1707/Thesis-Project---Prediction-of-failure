# -*- coding: utf-8 -*-
"""
Populate student_features từ các bảng nguồn:
- enrollments
- mooc_grades  
- h5p_scores
- mooc_video_interactions (if exists)
- mooc_quiz_attempts (if exists)
"""
import sys
import os
import io
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.db import get_db_connection

def populate_student_features(course_id=None):
    """
    Populate student_features cho một course (hoặc tất cả)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("=" * 80)
        print("POPULATE STUDENT_FEATURES TỪ CÁC BẢNG NGUỒN")
        print("=" * 80)
        
        # Filter by course
        course_filter = f"AND e.course_id = '{course_id}'" if course_id else ""
        
        print(f"\n📊 Đang xử lý course: {course_id if course_id else 'ALL'}")
        
        # Populate student_features
        query = f"""
        INSERT INTO student_features (
            user_id, course_id,
            enrollment_mode, is_active, weeks_since_enrollment,
            mooc_grade_percentage, mooc_letter_grade, mooc_is_passed,
            h5p_total_contents, h5p_completed_contents, 
            h5p_total_score, h5p_total_max_score,
            h5p_overall_percentage, h5p_total_time_spent,
            h5p_completion_rate,
            extraction_batch_id, updated_at
        )
        SELECT 
            e.user_id,
            e.course_id,
            e.mode as enrollment_mode,
            e.is_active,
            GREATEST(0, TIMESTAMPDIFF(WEEK, e.created, NOW())) as weeks_since_enrollment,
            
            -- MOOC Grades
            COALESCE(mg.grade_percentage, 0) as mooc_grade_percentage,
            mg.letter_grade as mooc_letter_grade,
            COALESCE(mg.is_passed, 0) as mooc_is_passed,
            
            -- H5P aggregated data
            COALESCE(h5p_agg.total_contents, 0) as h5p_total_contents,
            COALESCE(h5p_agg.completed_contents, 0) as h5p_completed_contents,
            COALESCE(h5p_agg.total_score, 0) as h5p_total_score,
            COALESCE(h5p_agg.total_max_score, 0) as h5p_total_max_score,
            COALESCE(h5p_agg.avg_percentage, 0) as h5p_overall_percentage,
            COALESCE(h5p_agg.total_time_spent, 0) as h5p_total_time_spent,
            CASE 
                WHEN h5p_agg.total_contents > 0 THEN (h5p_agg.completed_contents * 100.0 / h5p_agg.total_contents)
                ELSE 0 
            END as h5p_completion_rate,
            
            CONCAT('populate_', DATE_FORMAT(NOW(), '%Y%m%d_%H%i%s')) as extraction_batch_id,
            NOW() as updated_at
            
        FROM enrollments e
        
        -- LEFT JOIN mooc_grades
        LEFT JOIN mooc_grades mg 
            ON e.user_id = mg.user_id AND e.course_id = mg.course_id
        
        -- LEFT JOIN h5p aggregated
        LEFT JOIN (
            SELECT 
                user_id,
                course_id,
                COUNT(DISTINCT content_id) as total_contents,
                COUNT(DISTINCT CASE WHEN percentage >= 70 THEN content_id END) as completed_contents,
                SUM(score) as total_score,
                SUM(max_score) as total_max_score,
                AVG(percentage) as avg_percentage,
                SUM(time_spent) as total_time_spent
            FROM h5p_scores
            GROUP BY user_id, course_id
        ) h5p_agg
            ON e.user_id = h5p_agg.user_id AND e.course_id = h5p_agg.course_id
        
        WHERE 1=1 {course_filter}
        
        ON DUPLICATE KEY UPDATE
            mooc_grade_percentage = VALUES(mooc_grade_percentage),
            mooc_letter_grade = VALUES(mooc_letter_grade),
            mooc_is_passed = VALUES(mooc_is_passed),
            h5p_total_contents = VALUES(h5p_total_contents),
            h5p_completed_contents = VALUES(h5p_completed_contents),
            h5p_total_score = VALUES(h5p_total_score),
            h5p_total_max_score = VALUES(h5p_total_max_score),
            h5p_overall_percentage = VALUES(h5p_overall_percentage),
            h5p_total_time_spent = VALUES(h5p_total_time_spent),
            h5p_completion_rate = VALUES(h5p_completion_rate),
            weeks_since_enrollment = VALUES(weeks_since_enrollment),
            updated_at = NOW()
        """
        
        cursor.execute(query)
        conn.commit()
        
        affected = cursor.rowcount
        print(f"   ✅ Populated/Updated {affected} records in student_features")
        
        # Verify
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN h5p_total_score > 0 THEN 1 END) as with_h5p,
                AVG(h5p_total_score) as avg_h5p_score
            FROM student_features
            WHERE course_id = '{course_id}' 
        """)
        
        result = cursor.fetchone()
        print(f"\n📊 Verification:")
        print(f"   - Total students: {result[0]}")
        print(f"   - Students with H5P score > 0: {result[1]}")
        print(f"   - Avg H5P score: {result[2]:.2f}" if result[2] else "   - Avg H5P score: 0")
        
        print("\n✅ HOÀN THÀNH!")
        print("=" * 80)
        
        return affected
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Populate student_features')
    parser.add_argument('--course-id', type=str, help='Course ID (optional, populate all if not provided)')
    args = parser.parse_args()
    
    populate_student_features(args.course_id)
