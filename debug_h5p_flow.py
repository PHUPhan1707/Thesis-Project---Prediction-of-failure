"""
Debug script: Kiểm tra API H5P với course_id từ API /api/courses
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def debug_h5p_flow():
    """Debug toàn bộ flow từ /api/courses đến /api/h5p-analytics"""
    
    print("=" * 80)
    print("STEP 1: Lấy danh sách courses từ /api/courses")
    print("=" * 80)
    
    try:
        response = requests.get(f"{BASE_URL}/api/courses")
        response.raise_for_status()
        courses_data = response.json()
        
        print(f"\n✅ SUCCESS! Total courses: {courses_data.get('total', 0)}")
        
        if not courses_data.get('courses'):
            print("❌ Không có course nào!")
            return
        
        for i, course in enumerate(courses_data.get('courses', []), 1):
            course_id = course['course_id']
            student_count = course['student_count']
            
            print(f"\n{i}. Course: {course_id}")
            print(f"   Students: {student_count}")
            
            # Test H5P API cho course này
            print(f"\n   Testing H5P API...")
            h5p_url = f"{BASE_URL}/api/h5p-analytics/{requests.utils.quote(course_id, safe='')}/low-performance"
            h5p_params = {"min_students": 3, "limit": 10}
            
            print(f"   URL: {h5p_url}")
            print(f"   Params: {h5p_params}")
            
            try:
                h5p_response = requests.get(h5p_url, params=h5p_params)
                h5p_response.raise_for_status()
                h5p_data = h5p_response.json()
                
                if h5p_data.get('success'):
                    contents_count = len(h5p_data.get('contents', []))
                    print(f"   ✅ H5P API SUCCESS! Contents: {contents_count}")
                    
                    if contents_count > 0:
                        print(f"\n   📊 Statistics:")
                        stats = h5p_data.get('statistics', {})
                        for key, value in stats.items():
                            print(f"      - {key}: {value}")
                        
                        print(f"\n   📋 Top 3 contents:")
                        for j, content in enumerate(h5p_data.get('contents', [])[:3], 1):
                            print(f"      {j}. {content['content_title']}")
                            print(f"         - Students not max: {content['students_not_max_score']}/{content['total_students']}")
                            print(f"         - Avg score: {content['avg_score']}%")
                    else:
                        print(f"   ⚠️  H5P API trả về success=True nhưng không có contents")
                else:
                    print(f"   ❌ H5P API trả về success=False")
                    print(f"   Message: {h5p_data.get('message', 'No message')}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ H5P API Error: {e}")
            
            print("\n" + "-" * 80)
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Courses API Error: {e}")

if __name__ == "__main__":
    debug_h5p_flow()
