"""
Script test để kiểm tra H5P Analytics APIs
"""
import requests
from urllib.parse import quote
import json

# Configuration
BASE_URL = "http://localhost:5000"
COURSE_ID = "course-v1:VNUHCM+FM101+2024_T1"  # Thay bằng course_id thực tế của bạn

def test_low_performance_contents():
    """Test API lấy danh sách bài H5P có performance thấp"""
    print("\n" + "="*80)
    print("TEST 1: Lấy danh sách bài H5P có performance thấp")
    print("="*80)
    
    encoded_course_id = quote(COURSE_ID, safe='')
    url = f"{BASE_URL}/api/h5p-analytics/{encoded_course_id}/low-performance"
    
    params = {
        'limit': 10,
        'min_students': 3
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('success'):
            print(f"✅ Success!")
            print(f"\nStatistics:")
            stats = data.get('statistics', {})
            print(f"  - Tổng số bài phân tích: {stats.get('total_contents_analyzed')}")
            print(f"  - Tỉ lệ hoàn thành TB: {stats.get('avg_completion_rate')}%")
            print(f"  - Điểm TB tất cả bài: {stats.get('avg_score_all')}")
            print(f"  - Số bài khó (HIGH): {stats.get('high_difficulty_count')}")
            print(f"  - Số bài cần chú ý: {stats.get('needs_attention_count')}")
            
            print(f"\nTop 5 bài khó nhất:")
            for i, content in enumerate(data.get('contents', [])[:5], 1):
                print(f"\n  {i}. {content['content_title']}")
                print(f"     Folder: {content['folder_name']}")
                print(f"     Điểm TB: {content['avg_score']}% | Tỉ lệ hoàn thành: {content['completion_rate']}%")
                print(f"     Sinh viên: {content['completed_students']}/{content['total_students']}")
                print(f"     Mức độ khó: {content['difficulty_level']}")
                print(f"     Cần chú ý: {'CÓ ⚠️' if content['needs_attention'] else 'Không'}")
        else:
            print(f"❌ Failed: {data}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_content_detail(content_id=None):
    """Test API lấy chi tiết một bài H5P"""
    print("\n" + "="*80)
    print("TEST 2: Chi tiết performance của một bài H5P")
    print("="*80)
    
    if content_id is None:
        # Lấy content_id đầu tiên từ API low-performance
        encoded_course_id = quote(COURSE_ID, safe='')
        url = f"{BASE_URL}/api/h5p-analytics/{encoded_course_id}/low-performance"
        try:
            response = requests.get(url, params={'limit': 1})
            data = response.json()
            if data.get('success') and data.get('contents'):
                content_id = data['contents'][0]['content_id']
                print(f"📝 Sử dụng content_id: {content_id}")
            else:
                print("❌ Không tìm thấy content_id nào. Vui lòng cung cấp content_id.")
                return
        except Exception as e:
            print(f"❌ Error lấy content_id: {e}")
            return
    
    encoded_course_id = quote(COURSE_ID, safe='')
    url = f"{BASE_URL}/api/h5p-analytics/{encoded_course_id}/content/{content_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('success'):
            print(f"✅ Success!")
            
            content = data.get('content', {})
            print(f"\nThông tin bài H5P:")
            print(f"  - Tên: {content['content_title']}")
            print(f"  - Folder: {content['folder_name']}")
            print(f"  - Điểm TB: {content['avg_score']}%")
            print(f"  - Tỉ lệ hoàn thành: {content['completion_rate']}%")
            print(f"  - Sinh viên: {content['completed_students']}/{content['total_students']}")
            
            dist = data.get('score_distribution', {})
            print(f"\nPhân bố điểm:")
            print(f"  - Xuất sắc (90-100): {dist.get('excellent')} SV")
            print(f"  - Tốt (80-89): {dist.get('good')} SV")
            print(f"  - Trung bình (70-79): {dist.get('average')} SV")
            print(f"  - Dưới TB (50-69): {dist.get('below_average')} SV")
            print(f"  - Kém (<50): {dist.get('poor')} SV")
            print(f"  - Chưa làm: {dist.get('not_attempted')} SV")
            
            perf = data.get('student_performance', {})
            print(f"\nPhân loại sinh viên:")
            print(f"  - High performers (>=80%): {len(perf.get('high_performers', []))} SV")
            print(f"  - Medium performers (50-79%): {len(perf.get('medium_performers', []))} SV")
            print(f"  - Low performers (<50%): {len(perf.get('low_performers', []))} SV")
            print(f"  - Not attempted: {len(perf.get('not_attempted', []))} SV")
            
            # Hiển thị 3 sinh viên làm kém nhất
            low_performers = perf.get('low_performers', [])
            if low_performers:
                print(f"\n  📉 Top 3 sinh viên cần hỗ trợ:")
                for i, student in enumerate(low_performers[:3], 1):
                    print(f"     {i}. {student['full_name']} ({student['mssv']})")
                    print(f"        Email: {student['email']}")
                    print(f"        Điểm: {student['percentage']}% ({student['score']}/{student['max_score']})")
                    print(f"        Thời gian làm: {student['time_spent_minutes']} phút")
        else:
            print(f"❌ Failed: {data}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_student_performance(user_id=None):
    """Test API lấy performance H5P của một sinh viên"""
    print("\n" + "="*80)
    print("TEST 3: Performance H5P của một sinh viên")
    print("="*80)
    
    if user_id is None:
        # Lấy user_id đầu tiên từ API content detail
        encoded_course_id = quote(COURSE_ID, safe='')
        
        # Thử lấy từ low-performance trước
        url = f"{BASE_URL}/api/h5p-analytics/{encoded_course_id}/low-performance"
        try:
            response = requests.get(url, params={'limit': 1})
            data = response.json()
            if data.get('success') and data.get('contents'):
                content_id = data['contents'][0]['content_id']
                
                # Lấy chi tiết content để có user_id
                url2 = f"{BASE_URL}/api/h5p-analytics/{encoded_course_id}/content/{content_id}"
                response2 = requests.get(url2)
                data2 = response2.json()
                
                if data2.get('success'):
                    perf = data2.get('student_performance', {})
                    # Ưu tiên lấy low performer để test
                    if perf.get('low_performers'):
                        user_id = perf['low_performers'][0]['user_id']
                    elif perf.get('high_performers'):
                        user_id = perf['high_performers'][0]['user_id']
                    
                    if user_id:
                        print(f"👤 Sử dụng user_id: {user_id}")
                    else:
                        print("❌ Không tìm thấy user_id nào. Vui lòng cung cấp user_id.")
                        return
        except Exception as e:
            print(f"❌ Error lấy user_id: {e}")
            return
    
    encoded_course_id = quote(COURSE_ID, safe='')
    url = f"{BASE_URL}/api/h5p-analytics/{encoded_course_id}/student/{user_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('success'):
            print(f"✅ Success!")
            
            student = data.get('student', {})
            print(f"\nThông tin sinh viên:")
            print(f"  - Họ tên: {student['full_name']}")
            print(f"  - MSSV: {student['mssv']}")
            print(f"  - Email: {student['email']}")
            
            stats = data.get('statistics', {})
            print(f"\nThống kê H5P:")
            print(f"  - Tổng bài đã làm: {stats.get('total_attempted')}")
            print(f"  - Bài đang làm: {stats.get('total_in_progress')}")
            print(f"  - Điểm TB: {stats.get('avg_score')}%")
            print(f"  - Xuất sắc: {stats.get('excellent_count')} bài")
            print(f"  - Tốt: {stats.get('good_count')} bài")
            print(f"  - Cần cải thiện: {stats.get('needs_improvement_count')} bài")
            print(f"  - Kém: {stats.get('poor_count')} bài")
            
            perf = data.get('performance', {})
            
            # Hiển thị bài làm kém
            poor = perf.get('poor', [])
            if poor:
                print(f"\n  📉 Các bài làm kém (<50%):")
                for i, content in enumerate(poor, 1):
                    print(f"     {i}. {content['content_title']}")
                    print(f"        Folder: {content['folder_name']}")
                    print(f"        Điểm: {content['percentage']}% ({content['score']}/{content['max_score']})")
            
            # Hiển thị bài cần cải thiện
            needs = perf.get('needs_improvement', [])
            if needs:
                print(f"\n  ⚠️ Các bài cần cải thiện (50-79%):")
                for i, content in enumerate(needs[:3], 1):  # Top 3
                    print(f"     {i}. {content['content_title']}")
                    print(f"        Điểm: {content['percentage']}%")
            
            # Hiển thị bài đang làm
            in_progress = perf.get('in_progress', [])
            if in_progress:
                print(f"\n  🔄 Các bài đang làm dở:")
                for i, content in enumerate(in_progress, 1):
                    print(f"     {i}. {content['content_title']}")
                    print(f"        Thời gian đã dùng: {content['time_spent_minutes']} phút")
        else:
            print(f"❌ Failed: {data}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """Chạy tất cả tests"""
    print("\n" + "="*80)
    print("H5P ANALYTICS APIs - TEST SUITE")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Course ID: {COURSE_ID}")
    
    # Test 1: Low performance contents
    test_low_performance_contents()
    
    # Test 2: Content detail
    test_content_detail()
    
    # Test 3: Student performance
    test_student_performance()
    
    print("\n" + "="*80)
    print("HOÀN THÀNH TẤT CẢ TESTS")
    print("="*80)


if __name__ == "__main__":
    # Kiểm tra server có chạy không
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ Server đang chạy tại {BASE_URL}")
            main()
        else:
            print(f"❌ Server không phản hồi đúng (status: {response.status_code})")
    except requests.exceptions.RequestException:
        print(f"❌ Không thể kết nối đến server tại {BASE_URL}")
        print(f"   Hãy chạy: python app.py")
