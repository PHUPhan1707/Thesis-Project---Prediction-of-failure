"""
Test API /api/courses sau khi sửa
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_courses_api():
    """Test API lấy danh sách courses"""
    print("=" * 80)
    print("TEST: /api/courses")
    print("=" * 80)
    
    url = f"{BASE_URL}/api/courses"
    
    print(f"\n📡 Calling: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n✅ SUCCESS!")
        print(f"\nTotal courses: {data.get('total', 0)}")
        print(f"\nCourses:")
        for course in data.get('courses', []):
            print(f"  - {course['course_id']} ({course['student_count']} students)")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request Error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_courses_api()
