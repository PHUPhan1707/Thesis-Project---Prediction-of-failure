"""
Test statistics fix - Risk counts không nên bao gồm completed students
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from backend.db import fetch_all

print("=" * 100)
print("TEST: Statistics Fix - Risk Counts")
print("=" * 100)

course_id = 'course-v1:DHQG-HCM+FM101+2025_S2'

# Get DB stats
query = """
    SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN mooc_is_passed = 1 THEN 1 ELSE 0 END) AS completed,
        SUM(CASE WHEN mooc_is_passed != 1 THEN 1 ELSE 0 END) AS not_completed,
        -- OLD logic (WRONG): Count all students
        SUM(CASE WHEN fail_risk_score >= 70 THEN 1 ELSE 0 END) AS high_risk_all,
        SUM(CASE WHEN fail_risk_score >= 40 AND fail_risk_score < 70 THEN 1 ELSE 0 END) AS medium_risk_all,
        SUM(CASE WHEN fail_risk_score < 40 THEN 1 ELSE 0 END) AS low_risk_all,
        -- NEW logic (CORRECT): Only count not completed students
        SUM(CASE WHEN fail_risk_score >= 70 AND mooc_is_passed != 1 THEN 1 ELSE 0 END) AS high_risk_new,
        SUM(CASE WHEN fail_risk_score >= 40 AND fail_risk_score < 70 AND mooc_is_passed != 1 THEN 1 ELSE 0 END) AS medium_risk_new,
        SUM(CASE WHEN fail_risk_score < 40 AND mooc_is_passed != 1 THEN 1 ELSE 0 END) AS low_risk_new
    FROM raw_data
    WHERE course_id = %s
"""

db_stats = fetch_all(query, (course_id,))[0]

print(f"\n📊 DATABASE Comparison:")
print(f"   Total students: {db_stats['total']}")
print(f"   Completed: {db_stats['completed']}")
print(f"   Not completed: {db_stats['not_completed']}")
print()
print(f"   OLD Logic (Count ALL students):")
print(f"      High risk:   {db_stats['high_risk_all']:4d}")
print(f"      Medium risk: {db_stats['medium_risk_all']:4d}")
print(f"      Low risk:    {db_stats['low_risk_all']:4d}")
print(f"      Total:       {db_stats['high_risk_all'] + db_stats['medium_risk_all'] + db_stats['low_risk_all']:4d}")
print()
print(f"   NEW Logic (Only NOT completed):")
print(f"      High risk:   {db_stats['high_risk_new']:4d}")
print(f"      Medium risk: {db_stats['medium_risk_new']:4d}")
print(f"      Low risk:    {db_stats['low_risk_new']:4d}")
print(f"      Total:       {db_stats['high_risk_new'] + db_stats['medium_risk_new'] + db_stats['low_risk_new']:4d}")
print()
print(f"   Difference:")
print(f"      High risk:   {db_stats['high_risk_all'] - db_stats['high_risk_new']:4d} completed students removed")
print(f"      Medium risk: {db_stats['medium_risk_all'] - db_stats['medium_risk_new']:4d} completed students removed")
print(f"      Low risk:    {db_stats['low_risk_all'] - db_stats['low_risk_new']:4d} completed students removed")

# Verify: new total should equal not_completed
new_total = db_stats['high_risk_new'] + db_stats['medium_risk_new'] + db_stats['low_risk_new']
if new_total == db_stats['not_completed']:
    print(f"\n   ✅ CORRECT: Risk counts total ({new_total}) = Not completed ({db_stats['not_completed']})")
else:
    print(f"\n   ❌ ERROR: Risk counts total ({new_total}) != Not completed ({db_stats['not_completed']})")

# Test API
print("\n" + "=" * 100)
print("API Response After Fix:")
print("=" * 100)

try:
    response = requests.get(f"http://localhost:5000/api/statistics/{course_id}", timeout=10)
    stats = response.json()['statistics']
    
    print(f"\n📡 /api/statistics response:")
    print(f"   Total students:  {stats['total_students']}")
    print(f"   Completed:       {stats['completed_count']}")
    print(f"   Not passed:      {stats['not_passed_count']}")
    print(f"   In progress:     {stats['in_progress_count']}")
    print()
    print(f"   High risk:       {stats['high_risk_count']}")
    print(f"   Medium risk:     {stats['medium_risk_count']}")
    print(f"   Low risk:        {stats['low_risk_count']}")
    print(f"   Risk total:      {stats['high_risk_count'] + stats['medium_risk_count'] + stats['low_risk_count']}")
    
    # Verify
    not_completed_total = stats['not_passed_count'] + stats['in_progress_count']
    risk_total = stats['high_risk_count'] + stats['medium_risk_count'] + stats['low_risk_count']
    
    print(f"\n🔍 Verification:")
    print(f"   Not completed (not_passed + in_progress): {not_completed_total}")
    print(f"   Risk counts total: {risk_total}")
    
    if risk_total == not_completed_total:
        print(f"   ✅ CORRECT: Risk counts chỉ tính sinh viên chưa hoàn thành!")
    else:
        print(f"   ❌ ERROR: Risk counts vẫn sai! Chênh lệch: {abs(risk_total - not_completed_total)}")
    
    # Check completed count
    if stats['completed_count'] == db_stats['completed']:
        print(f"   ✅ Completed count đúng: {stats['completed_count']}")
    else:
        print(f"   ❌ Completed count sai: API={stats['completed_count']}, DB={db_stats['completed']}")
        
except Exception as e:
    print(f"\n❌ API Error: {e}")

print("\n" + "=" * 100)
print("✅ TEST COMPLETED")
print("=" * 100)
