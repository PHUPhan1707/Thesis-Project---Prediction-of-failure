"""
Test API response để xem kiểu dữ liệu của statistics
"""
import requests
import json

BASE_URL = "http://localhost:5000"
COURSE_ID = "course-v1:DHQG-HCM+FM101+2025_S2"

def test_h5p_response_types():
    """Kiểm tra kiểu dữ liệu của response"""
    
    url = f"{BASE_URL}/api/h5p-analytics/{requests.utils.quote(COURSE_ID, safe='')}/low-performance"
    params = {"min_students": 3, "limit": 10}
    
    print("=" * 80)
    print("KIỂM TRA KIỂU DỮ LIỆU CỦA H5P API RESPONSE")
    print("=" * 80)
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            stats = data.get('statistics', {})
            
            print("\n📊 Statistics object:")
            print(json.dumps(stats, indent=2))
            
            print("\n🔍 Kiểu dữ liệu của từng field:")
            for key, value in stats.items():
                print(f"  - {key}: {type(value).__name__} = {value}")
            
            print("\n⚠️  Kiểm tra các giá trị có phải number không:")
            for key in ['avg_score_all', 'avg_completion_rate']:
                value = stats.get(key)
                print(f"\n  {key}:")
                print(f"    Value: {value}")
                print(f"    Type: {type(value).__name__}")
                print(f"    Is number: {isinstance(value, (int, float))}")
                print(f"    Has toFixed: {hasattr(value, 'toFixed') if value else 'N/A'}")
                
                # Test conversion
                try:
                    num_value = float(value) if value is not None else 0
                    print(f"    Float conversion: {num_value} (success)")
                    print(f"    toFixed equivalent: {num_value:.1f}")
                except Exception as e:
                    print(f"    Float conversion: FAILED - {e}")
                    
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_h5p_response_types()
