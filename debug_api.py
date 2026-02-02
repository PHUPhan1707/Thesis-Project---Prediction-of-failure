"""Debug API response để kiểm tra completion_status"""
import requests
import json

url = "http://localhost:5000/api/students/course-v1:DHQG-HCM+FM101+2025_S2"

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    
    print("=" * 80)
    print("API Response Debug")
    print("=" * 80)
    
    students = data.get("students", [])
    print(f"\nTotal students: {len(students)}")
    
    # Lấy 5 sinh viên đầu tiên có mooc_is_passed = 1
    completed_students = [s for s in students if s.get("mooc_is_passed") in (1, True)][:5]
    
    print(f"\nCompleted students (mooc_is_passed = 1): {len([s for s in students if s.get('mooc_is_passed') in (1, True)])}")
    print("\nFirst 5 completed students:")
    print("-" * 80)
    
    for s in completed_students:
        print(f"\nUser ID: {s.get('user_id')}")
        print(f"  mooc_is_passed: {s.get('mooc_is_passed')} (type: {type(s.get('mooc_is_passed')).__name__})")
        print(f"  completion_status: {s.get('completion_status')}")
        print(f"  fail_risk_score: {s.get('fail_risk_score')}")
        print(f"  full_name: {s.get('full_name')}")
        
        # Check logic
        is_passed = s.get('mooc_is_passed')
        if is_passed in (True, 1, "1"):
            expected = "completed"
        elif is_passed in (False, 0, "0"):
            expected = "not_passed"
        else:
            expected = "in_progress"
        
        actual = s.get('completion_status')
        status = "✅ OK" if actual == expected else f"❌ WRONG (expected: {expected})"
        print(f"  Status check: {status}")
    
    print("\n" + "=" * 80)
    
    # Check nếu có sinh viên completed nhưng completion_status sai
    wrong_status = [
        s for s in students 
        if s.get('mooc_is_passed') in (1, True) and s.get('completion_status') != 'completed'
    ]
    
    if wrong_status:
        print(f"\n❌ FOUND {len(wrong_status)} students with WRONG completion_status!")
        print("These students have mooc_is_passed=1 but completion_status != 'completed'")
        for s in wrong_status[:3]:
            print(f"  - User {s.get('user_id')}: mooc_is_passed={s.get('mooc_is_passed')}, completion_status={s.get('completion_status')}")
    else:
        print("\n✅ All completed students have correct completion_status!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
