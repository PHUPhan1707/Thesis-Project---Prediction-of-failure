"""Debug statistics API response"""
import requests
import json

url = "http://localhost:5000/api/statistics/course-v1:DHQG-HCM+FM101+2025_S2"

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    
    print("=" * 80)
    print("API /api/statistics Response:")
    print("=" * 80)
    print(json.dumps(data, indent=2))
    
    stats = data.get('statistics', {})
    
    print("\n" + "=" * 80)
    print("Parsed Values:")
    print("=" * 80)
    print(f"total_students: {stats.get('total_students')} (type: {type(stats.get('total_students')).__name__})")
    print(f"completed_count: {stats.get('completed_count')} (type: {type(stats.get('completed_count')).__name__})")
    print(f"high_risk_count: {stats.get('high_risk_count')} (type: {type(stats.get('high_risk_count')).__name__})")
    print(f"medium_risk_count: {stats.get('medium_risk_count')} (type: {type(stats.get('medium_risk_count')).__name__})")
    print(f"low_risk_count: {stats.get('low_risk_count')} (type: {type(stats.get('low_risk_count')).__name__})")
    
    # Check if completed_count is truthy
    completed = stats.get('completed_count')
    print(f"\nCompleted count truthy check:")
    print(f"  completed_count || 0 = {completed or 0}")
    print(f"  bool(completed_count) = {bool(completed)}")
    
    # Calculate percentage like frontend
    total = stats.get('total_students', 0)
    if total > 0:
        percentage = (((completed or 0) / total) * 100)
        print(f"\nPercentage calculation:")
        print(f"  ({completed or 0} / {total}) * 100 = {percentage:.1f}%")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
