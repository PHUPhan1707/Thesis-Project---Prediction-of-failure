"""
Script kiểm tra xem query có lấy được tên sinh viên từ database không
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from backend.db import fetch_all

def test_query_names():
    """Test query to check if student names are being retrieved correctly"""
    
    print("=" * 80)
    print("TEST 1: Check raw_data table")
    print("=" * 80)
    
    # Get sample data from raw_data
    raw_data = fetch_all("""
        SELECT user_id, course_id, fail_risk_score
        FROM raw_data
        LIMIT 3
    """)
    
    if not raw_data:
        print("⚠️  WARNING: raw_data table is EMPTY!")
        return
    
    print(f"✅ Found {len(raw_data)} records in raw_data")
    for row in raw_data:
        print(f"   - user_id: {row['user_id']}, course_id: {row['course_id']}")
    
    print("\n" + "=" * 80)
    print("TEST 2: Check enrollments table")
    print("=" * 80)
    
    # Check enrollments table
    enrollments = fetch_all("""
        SELECT user_id, course_id, full_name, full_name_vn, email, username, mssv
        FROM enrollments
        LIMIT 5
    """)
    
    if not enrollments:
        print("⚠️  WARNING: enrollments table is EMPTY!")
    else:
        print(f"✅ Found {len(enrollments)} records in enrollments")
        for row in enrollments:
            print(f"   - user_id: {row['user_id']}, full_name_vn: {row.get('full_name_vn')}, full_name: {row.get('full_name')}")
    
    print("\n" + "=" * 80)
    print("TEST 3: Check mooc_grades table")
    print("=" * 80)
    
    # Check mooc_grades table
    mooc_grades = fetch_all("""
        SELECT user_id, course_id, full_name, email
        FROM mooc_grades
        LIMIT 5
    """)
    
    if not mooc_grades:
        print("⚠️  WARNING: mooc_grades table is EMPTY or doesn't have full_name column!")
    else:
        print(f"✅ Found {len(mooc_grades)} records in mooc_grades")
        for row in mooc_grades:
            print(f"   - user_id: {row['user_id']}, full_name: {row.get('full_name')}")
    
    print("\n" + "=" * 80)
    print("TEST 4: Test actual JOIN query (like API endpoint)")
    print("=" * 80)
    
    # Get a sample course_id
    if raw_data:
        sample_course_id = raw_data[0]['course_id']
        print(f"Testing with course_id: {sample_course_id}")
        
        students = fetch_all("""
            SELECT
                r.user_id,
                COALESCE(NULLIF(e.email, ''), g.email) AS email,
                COALESCE(NULLIF(e.full_name_vn, ''), NULLIF(e.full_name, ''), NULLIF(g.full_name, '')) AS full_name,
                e.username,
                e.mssv,
                r.fail_risk_score,
                r.mooc_grade_percentage,
                r.mooc_completion_rate,
                r.days_since_last_activity
            FROM raw_data r
            LEFT JOIN enrollments e
                ON r.user_id = e.user_id AND r.course_id = e.course_id
            LEFT JOIN mooc_grades g
                ON r.user_id = g.user_id AND r.course_id = g.course_id
            WHERE r.course_id = %s
            LIMIT 5
        """, (sample_course_id,))
        
        if not students:
            print("⚠️  WARNING: JOIN query returned EMPTY result!")
        else:
            print(f"✅ JOIN query returned {len(students)} students")
            print("\nStudent details:")
            for i, student in enumerate(students, 1):
                print(f"\n  Student {i}:")
                print(f"    - user_id: {student['user_id']}")
                print(f"    - full_name: {student.get('full_name')} {'❌ NULL' if not student.get('full_name') else '✅'}")
                print(f"    - email: {student.get('email')} {'❌ NULL' if not student.get('email') else '✅'}")
                print(f"    - username: {student.get('username')}")
                print(f"    - mssv: {student.get('mssv')}")
                print(f"    - fail_risk_score: {student.get('fail_risk_score')}")
    
    print("\n" + "=" * 80)
    print("TEST 5: Check if user_id and course_id match between tables")
    print("=" * 80)
    
    # Check for matching user_id and course_id
    if raw_data:
        sample_user_id = raw_data[0]['user_id']
        sample_course_id = raw_data[0]['course_id']
        
        print(f"Checking for user_id={sample_user_id}, course_id={sample_course_id}")
        
        # Check in enrollments
        enrollment_match = fetch_all("""
            SELECT * FROM enrollments
            WHERE user_id = %s AND course_id = %s
        """, (sample_user_id, sample_course_id))
        
        if enrollment_match:
            print(f"  ✅ Found in enrollments: {enrollment_match[0].get('full_name_vn') or enrollment_match[0].get('full_name')}")
        else:
            print(f"  ❌ NOT found in enrollments")
        
        # Check in mooc_grades
        grade_match = fetch_all("""
            SELECT * FROM mooc_grades
            WHERE user_id = %s AND course_id = %s
        """, (sample_user_id, sample_course_id))
        
        if grade_match:
            print(f"  ✅ Found in mooc_grades: {grade_match[0].get('full_name')}")
        else:
            print(f"  ❌ NOT found in mooc_grades")
    
    print("\n" + "=" * 80)
    print("DIAGNOSIS SUMMARY")
    print("=" * 80)
    
    if not raw_data:
        print("❌ ISSUE: raw_data table is empty. You need to populate it first.")
    elif not enrollments and not mooc_grades:
        print("❌ ISSUE: Both enrollments and mooc_grades tables are empty.")
        print("   Solution: Run data fetch scripts to populate these tables.")
    elif students and all(not s.get('full_name') for s in students):
        print("❌ ISSUE: JOIN is working but no full_name data exists.")
        print("   Solution: Check if enrollments/mooc_grades have full_name populated.")
    elif students and any(s.get('full_name') for s in students):
        print("✅ SUCCESS: Some students have names! The query is working.")
    else:
        print("⚠️  UNKNOWN: Check the detailed output above.")

if __name__ == "__main__":
    test_query_names()

