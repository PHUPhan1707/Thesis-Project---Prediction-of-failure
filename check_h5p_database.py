"""
Kiểm tra dữ liệu H5P trong database
"""
import mysql.connector
from mysql.connector import Error

def check_h5p_data():
    """Kiểm tra dữ liệu trong bảng h5p_scores"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=4000,
            database='dropout_prediction_db',
            user='dropout_user',
            password='dropout_pass_123'
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # 1. Kiểm tra tổng số records
            print("=" * 80)
            print("1. TỔNG SỐ RECORDS TRONG h5p_scores")
            print("=" * 80)
            cursor.execute("SELECT COUNT(*) as total FROM h5p_scores")
            result = cursor.fetchone()
            print(f"Total records: {result['total']}")
            
            # 2. Kiểm tra các course_id có trong database
            print("\n" + "=" * 80)
            print("2. CÁC COURSE_ID CÓ TRONG DATABASE")
            print("=" * 80)
            cursor.execute("""
                SELECT course_id, COUNT(*) as count
                FROM h5p_scores
                GROUP BY course_id
            """)
            courses = cursor.fetchall()
            for course in courses:
                print(f"   - {course['course_id']}: {course['count']} records")
            
            # 3. Kiểm tra dữ liệu chi tiết cho mỗi content_id
            if courses:
                course_id = courses[0]['course_id']
                print(f"\n" + "=" * 80)
                print(f"3. CHI TIẾT H5P CONTENTS CHO COURSE: {course_id}")
                print("=" * 80)
                
                cursor.execute("""
                    SELECT 
                        content_id,
                        content_title,
                        COUNT(DISTINCT user_id) as total_students,
                        COUNT(DISTINCT CASE WHEN percentage < 100 THEN user_id END) as students_not_max,
                        ROUND(AVG(percentage), 2) as avg_score,
                        MIN(percentage) as min_score,
                        MAX(percentage) as max_score
                    FROM h5p_scores
                    WHERE course_id = %s
                    GROUP BY content_id, content_title
                    ORDER BY students_not_max DESC
                    LIMIT 10
                """, (course_id,))
                
                contents = cursor.fetchall()
                for i, content in enumerate(contents, 1):
                    print(f"\n   {i}. {content['content_title']}")
                    print(f"      Content ID: {content['content_id']}")
                    print(f"      Total students: {content['total_students']}")
                    print(f"      Students NOT max: {content['students_not_max']}")
                    print(f"      Avg score: {content['avg_score']}%")
                    print(f"      Min/Max: {content['min_score']}% / {content['max_score']}%")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    check_h5p_data()
