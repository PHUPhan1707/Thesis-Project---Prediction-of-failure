"""
Script kiểm tra backend API có hoạt động không
"""
import requests
import json
import sys

API_BASE_URL = "http://localhost:5000"

def test_endpoint(endpoint, method="GET", data=None):
    """Test một endpoint"""
    url = f"{API_BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {method} {endpoint}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            print(f"❌ Method {method} not supported")
            return False
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Success!")
                print(f"Response (first 500 chars):")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                return True
            except:
                print(f"✅ Success! (Non-JSON response)")
                print(f"Response: {response.text[:200]}")
                return True
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"Error text: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Không thể kết nối đến {url}")
        print(f"   → Hãy kiểm tra backend có đang chạy không (python backend/app.py)")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Timeout: Request quá lâu")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("="*60)
    print("KIỂM TRA BACKEND API")
    print("="*60)
    
    # Test health check
    health_ok = test_endpoint("/api/health")
    
    if not health_ok:
        print("\n" + "="*60)
        print("❌ Backend không hoạt động!")
        print("="*60)
        print("\nHãy chạy backend trước:")
        print("  cd backend")
        print("  python app.py")
        sys.exit(1)
    
    # Test courses endpoint
    courses_ok = test_endpoint("/api/courses")
    
    if courses_ok:
        # Test statistics endpoint (cần course_id)
        test_endpoint("/api/statistics/course-v1:DHQG-HCM+FM101+2025_S2")
        
        # Test students endpoint
        test_endpoint("/api/students/course-v1:DHQG-HCM+FM101+2025_S2")
    
    print("\n" + "="*60)
    print("KẾT QUẢ KIỂM TRA")
    print("="*60)
    print(f"Health Check: {'✅ OK' if health_ok else '❌ FAILED'}")
    print(f"Courses API: {'✅ OK' if courses_ok else '❌ FAILED'}")
    
    if health_ok and courses_ok:
        print("\n✅ Backend hoạt động tốt!")
    else:
        print("\n❌ Có lỗi với backend API")

if __name__ == "__main__":
    main()

