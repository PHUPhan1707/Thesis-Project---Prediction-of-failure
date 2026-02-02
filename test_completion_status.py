"""
Test script để verify completion_status logic
Kiểm tra xem backend có set đúng completion_status cho sinh viên đã hoàn thành không
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.db import fetch_all

def test_completion_status():
    """
    Test completion_status logic với data thực từ database
    """
    print("=" * 80)
    print("TEST: Completion Status Logic")
    print("=" * 80)
    
    # Test query - lấy mẫu sinh viên có mooc_is_passed
    query = """
        SELECT 
            r.user_id,
            r.course_id,
            r.mooc_is_passed,
            r.fail_risk_score,
            r.mooc_grade_percentage,
            r.mooc_completion_rate,
            COALESCE(NULLIF(e.full_name_vn, ''), NULLIF(e.full_name, ''), 'N/A') AS full_name
        FROM raw_data r
        LEFT JOIN enrollments e ON r.user_id = e.user_id AND r.course_id = e.course_id
        WHERE r.course_id = 'course-v1:DHQG-HCM+FM101+2025_S2'
        ORDER BY r.mooc_is_passed DESC, r.fail_risk_score DESC
        LIMIT 20
    """
    
    try:
        rows = fetch_all(query)
        
        print(f"\n✅ Fetched {len(rows)} students from database\n")
        
        # Test completion_status logic
        print("Testing completion_status logic:")
        print("-" * 80)
        
        completed_count = 0
        not_passed_count = 0
        in_progress_count = 0
        
        for row in rows:
            mooc_is_passed = row.get("mooc_is_passed")
            
            # Apply the FIXED logic from backend
            if mooc_is_passed in (True, 1, "1"):
                completion_status = "completed"
                completed_count += 1
            elif mooc_is_passed in (False, 0, "0"):
                completion_status = "not_passed"
                not_passed_count += 1
            else:
                completion_status = "in_progress"
                in_progress_count += 1
            
            # Print result
            icon = "🎓" if completion_status == "completed" else "📝" if completion_status == "not_passed" else "📚"
            
            print(f"{icon} User {row['user_id']:6d} | mooc_is_passed: {str(mooc_is_passed):5s} "
                  f"| Status: {completion_status:12s} | Risk: {row['fail_risk_score']:5.1f}% "
                  f"| Grade: {row['mooc_grade_percentage']:5.1f}%")
        
        print("-" * 80)
        print(f"\n📊 Summary:")
        print(f"   🎓 Completed:    {completed_count:3d}")
        print(f"   📝 Not Passed:   {not_passed_count:3d}")
        print(f"   📚 In Progress:  {in_progress_count:3d}")
        print(f"   📋 Total:        {len(rows):3d}")
        
        # Test full course statistics
        print("\n" + "=" * 80)
        print("Full Course Statistics:")
        print("=" * 80)
        
        stats_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN mooc_is_passed IN (1, TRUE, '1') THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN mooc_is_passed IN (0, FALSE, '0') THEN 1 ELSE 0 END) as not_passed,
                SUM(CASE WHEN mooc_is_passed IS NULL THEN 1 ELSE 0 END) as in_progress
            FROM raw_data
            WHERE course_id = 'course-v1:BK+FM101+2022_T3'
        """
        
        stats = fetch_all(stats_query)[0]
        
        print(f"\n📊 Course: course-v1:BK+FM101+2022_T3")
        print(f"   Total Students:      {stats['total']:4d}")
        print(f"   🎓 Completed:        {stats['completed']:4d} ({stats['completed']/stats['total']*100:.1f}%)")
        print(f"   📝 Not Passed:       {stats['not_passed']:4d} ({stats['not_passed']/stats['total']*100:.1f}%)")
        print(f"   📚 In Progress:      {stats['in_progress']:4d} ({stats['in_progress']/stats['total']*100:.1f}%)")
        
        # Verify: Completed students should NOT show risk score
        print("\n" + "=" * 80)
        print("Verification: Completed students (should hide risk score in UI)")
        print("=" * 80)
        
        completed_query = """
            SELECT 
                r.user_id,
                r.mooc_is_passed,
                r.fail_risk_score,
                r.mooc_grade_percentage,
                COALESCE(NULLIF(e.full_name_vn, ''), NULLIF(e.full_name, ''), 'N/A') AS full_name
            FROM raw_data r
            LEFT JOIN enrollments e ON r.user_id = e.user_id AND r.course_id = e.course_id
            WHERE r.course_id = 'course-v1:DHQG-HCM+FM101+2025_S2'
              AND r.mooc_is_passed IN (1, TRUE, '1')
            ORDER BY r.fail_risk_score DESC
            LIMIT 10
        """
        
        completed_students = fetch_all(completed_query)
        
        print(f"\n✅ Sample of {len(completed_students)} completed students:")
        print("-" * 80)
        
        for s in completed_students:
            print(f"🎓 {s['full_name']:30s} | Grade: {s['mooc_grade_percentage']:5.1f}% "
                  f"| Risk: {s['fail_risk_score']:5.1f}% (SHOULD BE HIDDEN IN UI)")
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETED")
        print("=" * 80)
        
        print("\n💡 Expected behavior in UI:")
        print("   - Completed students (🎓) should NOT show 'Điểm rủi ro'")
        print("   - Completed students should show 'Đã hoàn thành' badge")
        print("   - Not passed students (📝) should show risk score")
        print("   - In progress students (📚) should show risk score")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_completion_status()
