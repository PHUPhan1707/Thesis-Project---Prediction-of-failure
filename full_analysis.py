"""
PHÂN TÍCH TOÀN BỘ: Tìm lỗi hiển thị completion status
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from backend.db import fetch_all

print("=" * 100)
print("PHÂN TÍCH TOÀN BỘ HỆ THỐNG - TÌM LỖI COMPLETION STATUS")
print("=" * 100)

# ============================================================================
# BƯỚC 1: KIỂM TRA DATABASE
# ============================================================================
print("\n" + "=" * 100)
print("BƯỚC 1: KIỂM TRA DATABASE")
print("=" * 100)

query_stats = """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN mooc_is_passed = 1 THEN 1 ELSE 0 END) as completed,
        SUM(CASE WHEN mooc_is_passed = 0 THEN 1 ELSE 0 END) as not_passed,
        SUM(CASE WHEN mooc_is_passed IS NULL THEN 1 ELSE 0 END) as in_progress
    FROM raw_data
    WHERE course_id = 'course-v1:DHQG-HCM+FM101+2025_S2'
"""

db_stats = fetch_all(query_stats)[0]
total = int(db_stats['total'] or 0)
completed = int(db_stats['completed'] or 0)
not_passed = int(db_stats['not_passed'] or 0)
in_progress = int(db_stats['in_progress'] or 0)

print(f"\n📊 DATABASE Statistics:")
print(f"   Total:        {total:4d}")
print(f"   Completed:    {completed:4d} ({completed/total*100:.1f}%)")
print(f"   Not Passed:   {not_passed:4d} ({not_passed/total*100:.1f}%)")
print(f"   In Progress:  {in_progress:4d} ({in_progress/total*100:.1f}%)")

# Sample completed students
query_sample = """
    SELECT user_id, mooc_is_passed, fail_risk_score, mooc_grade_percentage
    FROM raw_data
    WHERE course_id = 'course-v1:DHQG-HCM+FM101+2025_S2'
      AND mooc_is_passed = 1
    ORDER BY fail_risk_score DESC
    LIMIT 5
"""

completed_samples = fetch_all(query_sample)
print(f"\n✅ Sample 5 COMPLETED students từ DB:")
for s in completed_samples:
    print(f"   User {s['user_id']:5d}: mooc_is_passed={s['mooc_is_passed']}, risk={s['fail_risk_score']:.1f}%, grade={s['mooc_grade_percentage']:.1f}%")

# ============================================================================
# BƯỚC 2: KIỂM TRA BACKEND API
# ============================================================================
print("\n" + "=" * 100)
print("BƯỚC 2: KIỂM TRA BACKEND API")
print("=" * 100)

try:
    # Test students endpoint
    response = requests.get(
        "http://localhost:5000/api/students/course-v1:DHQG-HCM+FM101+2025_S2",
        params={"sort_by": "risk_score", "order": "desc"},
        timeout=10
    )
    students_data = response.json()
    students = students_data.get("students", [])
    
    print(f"\n📡 API /api/students response:")
    print(f"   Total students: {len(students)}")
    
    # Count by completion_status from API
    completed_api = [s for s in students if s.get('completion_status') == 'completed']
    not_passed_api = [s for s in students if s.get('completion_status') == 'not_passed']
    in_progress_api = [s for s in students if s.get('completion_status') == 'in_progress']
    
    print(f"\n📊 API Statistics (by completion_status):")
    print(f"   Completed:    {len(completed_api):4d} ({len(completed_api)/len(students)*100:.1f}%)")
    print(f"   Not Passed:   {len(not_passed_api):4d} ({len(not_passed_api)/len(students)*100:.1f}%)")
    print(f"   In Progress:  {len(in_progress_api):4d} ({len(in_progress_api)/len(students)*100:.1f}%)")
    
    # Compare với DB
    print(f"\n🔍 SO SÁNH DB vs API:")
    db_completed = completed
    api_completed = len(completed_api)
    
    if db_completed == api_completed:
        print(f"   ✅ MATCH: DB={db_completed}, API={api_completed}")
    else:
        print(f"   ❌ MISMATCH: DB={db_completed}, API={api_completed} (Chênh lệch: {abs(db_completed - api_completed)})")
    
    # Sample API response
    print(f"\n✅ Sample 5 COMPLETED students từ API:")
    for s in completed_api[:5]:
        print(f"   User {s['user_id']:5d}: mooc_is_passed={s.get('mooc_is_passed')} (type={type(s.get('mooc_is_passed')).__name__}), "
              f"completion_status={s.get('completion_status')}, risk={s.get('fail_risk_score'):.1f}%")
    
    # Check if any completed student missing completion_status
    wrong_status = [
        s for s in students 
        if s.get('mooc_is_passed') == 1 and s.get('completion_status') != 'completed'
    ]
    
    if wrong_status:
        print(f"\n❌ FOUND {len(wrong_status)} students với SAI completion_status!")
        for s in wrong_status[:3]:
            print(f"   User {s['user_id']}: mooc_is_passed={s.get('mooc_is_passed')}, completion_status={s.get('completion_status')}")
    else:
        print(f"\n✅ All students có ĐÚNG completion_status!")
    
    # Test statistics endpoint
    stats_response = requests.get(
        "http://localhost:5000/api/statistics/course-v1:DHQG-HCM+FM101+2025_S2",
        timeout=10
    )
    stats_data = stats_response.json()
    stats = stats_data.get("statistics", {})
    
    print(f"\n📡 API /api/statistics response:")
    print(f"   Total:        {stats.get('total_students')}")
    print(f"   Completed:    {stats.get('completed_count')}")
    print(f"   Not Passed:   {stats.get('not_passed_count')}")
    print(f"   In Progress:  {stats.get('in_progress_count')}")
    print(f"   High Risk:    {stats.get('high_risk_count')}")
    print(f"   Medium Risk:  {stats.get('medium_risk_count')}")
    print(f"   Low Risk:     {stats.get('low_risk_count')}")
    
except Exception as e:
    print(f"\n❌ API Error: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# BƯỚC 3: PHÂN TÍCH FRONTEND LOGIC
# ============================================================================
print("\n" + "=" * 100)
print("BƯỚC 3: PHÂN TÍCH FRONTEND LOGIC")
print("=" * 100)

print("\n📝 Frontend StudentList.tsx logic:")
print("   Code hiện tại:")
print("   ```typescript")
print("   const isCompleted = student.completion_status === 'completed' ||")
print("                       student.mooc_is_passed === true ||")
print("                       student.mooc_is_passed === 1;")
print("   ```")

# Simulate frontend logic
print("\n🧪 Test Frontend Logic với API data:")
for s in completed_api[:3]:
    mooc_is_passed = s.get('mooc_is_passed')
    completion_status = s.get('completion_status')
    
    # Simulate frontend check
    isCompleted = (completion_status == 'completed' or 
                   mooc_is_passed == True or 
                   mooc_is_passed == 1)
    
    print(f"\n   User {s['user_id']}:")
    print(f"      mooc_is_passed: {mooc_is_passed} (type: {type(mooc_is_passed).__name__})")
    print(f"      completion_status: {completion_status}")
    print(f"      isCompleted: {isCompleted}")
    print(f"      Should hide risk score: {isCompleted}")
    print(f"      Result: {'✅ CORRECT' if isCompleted else '❌ WRONG'}")

# ============================================================================
# BƯỚC 4: TÌM VẤN ĐỀ
# ============================================================================
print("\n" + "=" * 100)
print("BƯỚC 4: CHẨN ĐOÁN VẤN ĐỀ")
print("=" * 100)

issues = []

# Check 1: DB vs API count
if completed != len(completed_api):
    issues.append(f"❌ Backend không trả đúng số lượng completed students (DB: {completed}, API: {len(completed_api)})")

# Check 2: completion_status field
if any(s.get('completion_status') != 'completed' for s in completed_api):
    issues.append("❌ Một số completed students không có completion_status='completed'")

# Check 3: mooc_is_passed type
mooc_types = set(type(s.get('mooc_is_passed')).__name__ for s in completed_api[:10])
if 'int' in mooc_types:
    issues.append(f"⚠️  mooc_is_passed trả về kiểu int (cần check === 1 trong frontend)")

# Check 4: Statistics API
if stats.get('completed_count') != completed:
    issues.append(f"❌ Statistics API sai: completed_count={stats.get('completed_count')}, DB={completed}")

if not issues:
    print("\n✅ KHÔNG TÌM THẤY VẤN ĐỀ trong Backend!")
    print("\n💡 Vấn đề có thể ở:")
    print("   1. Frontend chưa reload code mới (Ctrl+Shift+R)")
    print("   2. Browser cache (Clear cache hoặc Incognito mode)")
    print("   3. Vite HMR chưa update (Restart dev server)")
else:
    print("\n❌ TÌM THẤY CÁC VẤN ĐỀ:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")

# ============================================================================
# BƯỚC 5: KIỂM TRA FILTER LOGIC
# ============================================================================
print("\n" + "=" * 100)
print("BƯỚC 5: KIỂM TRA FILTER LOGIC")
print("=" * 100)

print("\n🔍 Kiểm tra xem filter có ẩn completed students không:")

# Check if filter is hiding completed students
high_risk_students = [s for s in students if s.get('fail_risk_score', 0) >= 70]
high_risk_completed = [s for s in high_risk_students if s.get('completion_status') == 'completed']

print(f"\n   Total HIGH risk (>= 70%): {len(high_risk_students)}")
print(f"   HIGH risk + COMPLETED: {len(high_risk_completed)}")

if high_risk_completed:
    print(f"\n   ⚠️  CÓ {len(high_risk_completed)} sinh viên COMPLETED nhưng vẫn có HIGH risk score!")
    print("   Đây là BÌNH THƯỜNG (model dự đoán trước khi họ pass)")
    print("   Những sinh viên này KHÔNG NÊN hiển thị risk score trên UI")
    print("\n   Sample:")
    for s in high_risk_completed[:3]:
        print(f"      User {s['user_id']}: risk={s['fail_risk_score']:.1f}%, grade={s['mooc_grade_percentage']:.1f}%, status={s['completion_status']}")

# ============================================================================
# KẾT LUẬN
# ============================================================================
print("\n" + "=" * 100)
print("KẾT LUẬN VÀ KHUYẾN NGHỊ")
print("=" * 100)

print(f"\n📊 TÓM TẮT:")
print(f"   - Database: {completed} completed students")
print(f"   - API: {len(completed_api)} completed students")
print(f"   - Statistics API: {stats.get('completed_count')} completed students")

if completed == len(completed_api) == stats.get('completed_count'):
    print(f"\n✅ Backend hoạt động ĐÚNG!")
    print(f"\n💡 Nếu UI vẫn hiển thị sai, vấn đề ở FRONTEND:")
    print(f"   1. Clear browser cache")
    print(f"   2. Hard reload (Ctrl+Shift+R)")
    print(f"   3. Restart Vite dev server")
    print(f"   4. Check browser console for errors")
else:
    print(f"\n❌ Backend có VẤN ĐỀ!")
    print(f"\n🔧 CẦN SỬA:")
    for issue in issues:
        print(f"   - {issue}")

print("\n" + "=" * 100)
