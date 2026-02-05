"""
Test H5P Performance API với metric students_not_max_score mới
"""
import requests
import json

BASE_URL = "http://localhost:5000"
COURSE_ID = "course-v1:DHQG-HCM+FM101+2025_S2"  # Course ID thực tế trong database

def test_h5p_low_performance():
    """Test API lấy H5P low performance với metric mới"""
    print("=" * 80)
    print("TEST: H5P Low Performance API (với students_not_max_score)")
    print("=" * 80)
    
    url = f"{BASE_URL}/api/h5p-analytics/{COURSE_ID}/low-performance"
    params = {
        "min_students": 3,  # Ít nhất 3 sinh viên
        "limit": 10  # Top 10 bài
    }
    
    print(f"\n📡 Calling: {url}")
    print(f"📝 Params: {params}")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("success"):
            print(f"\n✅ SUCCESS!")
            print(f"\n📊 Statistics:")
            stats = data.get("statistics", {})
            for key, value in stats.items():
                print(f"   - {key}: {value}")
            
            print(f"\n📋 Contents (Top {len(data.get('contents', []))}):")
            for i, content in enumerate(data.get("contents", []), 1):
                print(f"\n   {i}. {content['content_title']}")
                print(f"      📁 Folder: {content['folder_name']}")
                print(f"      👥 Total students: {content['total_students']}")
                print(f"      ❌ Students NOT max score: {content['students_not_max_score']} ({content['not_max_rate']}%)")
                print(f"      ✅ Completed: {content['completed_students']} ({content['completion_rate']}%)")
                print(f"      📊 Avg score: {content['avg_score']}%")
                print(f"      🎯 Difficulty: {content['difficulty_level']}")
                print(f"      ⚠️  Needs attention: {content['needs_attention']}")
        else:
            print(f"\n❌ API returned success=False")
            print(f"Message: {data.get('message', 'No message')}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request Error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_h5p_low_performance()
