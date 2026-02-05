"""
Debug script to check H5P data
"""
import mysql.connector
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent / "backend"))

print("Starting H5P debug...")
print("Using direct connection...")
# Direct connection
DB_CONFIG = {
        "host": "localhost",
        "port": 4000,
        "database": "dropout_prediction_db",
        "user": "dropout_user",
        "password": "dropout_pass_123"
}

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    print("[OK] Connected to database directly")
    
    # Check h5p_scores data
    print("\n" + "="*60)
    print("1. CHECK H5P_SCORES TABLE")
    print("="*60)
    
    cursor.execute("""
        SELECT COUNT(*) as total_records,
                   COUNT(DISTINCT course_id) as total_courses,
                   COUNT(DISTINCT user_id) as total_users,
                   COUNT(DISTINCT content_id) as total_contents
            FROM h5p_scores
        """)
        result = cursor.fetchone()
        print(f"Total records: {result['total_records']}")
        print(f"Total courses: {result['total_courses']}")
        print(f"Total users: {result['total_users']}")
        print(f"Total contents: {result['total_contents']}")
        
        # List all courses with H5P data
        print("\n" + "="*60)
        print("2. COURSES WITH H5P DATA")
        print("="*60)
        
        cursor.execute("""
            SELECT course_id,
                   COUNT(DISTINCT user_id) as total_students,
                   COUNT(DISTINCT content_id) as total_contents,
                   COUNT(*) as total_records
            FROM h5p_scores
            GROUP BY course_id
            ORDER BY total_records DESC
        """)
        
        courses = cursor.fetchall()
        for i, course in enumerate(courses, 1):
            print(f"\n{i}. Course ID: {course['course_id']}")
            print(f"   Students: {course['total_students']}")
            print(f"   Contents: {course['total_contents']}")
            print(f"   Records: {course['total_records']}")
        
        # Sample data
        print("\n" + "="*60)
        print("3. SAMPLE H5P DATA (First 5 records)")
        print("="*60)
        
        cursor.execute("""
            SELECT user_id, course_id, content_id, content_title,
                   score, max_score, percentage, finished
            FROM h5p_scores
            LIMIT 5
        """)
        
        samples = cursor.fetchall()
        for i, sample in enumerate(samples, 1):
            print(f"\n{i}. User: {sample['user_id']}, Course: {sample['course_id']}")
            print(f"   Content: {sample['content_title']}")
            print(f"   Score: {sample['score']}/{sample['max_score']} ({sample['percentage']}%)")
            print(f"   Finished: {'Yes' if sample['finished'] > 0 else 'No'}")
        
        # Test the query that API uses
        if courses:
            test_course_id = courses[0]['course_id']
            print("\n" + "="*60)
            print(f"4. TEST API QUERY FOR COURSE: {test_course_id}")
            print("="*60)
            
            query = """
                SELECT 
                    content_id,
                    content_title,
                    folder_name,
                    COUNT(DISTINCT user_id) as total_students,
                    COUNT(DISTINCT CASE WHEN finished > 0 THEN user_id END) as completed_students,
                    ROUND(COUNT(DISTINCT CASE WHEN finished > 0 THEN user_id END) * 100.0 / COUNT(DISTINCT user_id), 2) as completion_rate,
                    ROUND(AVG(percentage), 2) as avg_score,
                    ROUND(AVG(CASE WHEN finished > 0 THEN percentage END), 2) as avg_score_completed,
                    MIN(percentage) as min_score,
                    MAX(percentage) as max_score
                FROM h5p_scores
                WHERE course_id = %s
                GROUP BY content_id, content_title, folder_name
                HAVING total_students >= 3
                ORDER BY avg_score ASC
                LIMIT 10
            """
            
            cursor.execute(query, (test_course_id,))
            results = cursor.fetchall()
            
            print(f"Found {len(results)} contents with at least 3 students")
            
            for i, row in enumerate(results[:5], 1):
                print(f"\n{i}. {row['content_title']}")
                print(f"   Avg Score: {row['avg_score']}%")
                print(f"   Completion Rate: {row['completion_rate']}%")
                print(f"   Students: {row['completed_students']}/{row['total_students']}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("[OK] DEBUG COMPLETED")
        print("="*60)
        
    except mysql.connector.Error as e:
        print(f"[ERROR] Database error: {e}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
