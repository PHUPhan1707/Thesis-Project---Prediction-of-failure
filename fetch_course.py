"""
Script đơn giản để fetch môn học mới
Wrapper cho database/fetch_mooc_h5p_data.py
"""
import subprocess
import sys
from pathlib import Path

def main():
    print("=" * 80)
    print("🚀 FETCH MÔN HỌC MỚI")
    print("=" * 80)
    
    print("\n📚 Nhập Course ID:")
    print("   Format: course-v1:ORG+COURSE+RUN")
    print("   Ví dụ: course-v1:DHQG-HCM+CS101+2025_S2")
    print()
    
    course_id = input("Course ID: ").strip()
    
    if not course_id:
        print("❌ Course ID không được để trống!")
        return
    
    # Hỏi có cần sessionid không
    print("\n🔐 Bạn có cần sessionid không? (nếu API yêu cầu authentication)")
    need_session = input("Cần sessionid? (y/n, Enter = n): ").strip().lower()
    
    sessionid = ""
    if need_session == 'y':
        print("\n📝 Lấy sessionid:")
        print("   1. Đăng nhập vào https://mooc.vnuhcm.edu.vn")
        print("   2. Mở DevTools (F12) → Application → Cookies")
        print("   3. Copy giá trị của 'sessionid'")
        print()
        sessionid = input("Nhập sessionid (hoặc Enter để bỏ qua): ").strip()
    
    # Hỏi có muốn giới hạn số sinh viên không (để test)
    print("\n🧪 Giới hạn số sinh viên? (để test nhanh)")
    limit = input("Số sinh viên tối đa (Enter = tất cả): ").strip()
    
    # Xác nhận
    print("\n" + "=" * 80)
    print("📋 THÔNG TIN FETCH:")
    print("=" * 80)
    print(f"   Course ID: {course_id}")
    print(f"   Sessionid: {'Có' if sessionid else 'Không'}")
    print(f"   Giới hạn: {limit if limit else 'Không giới hạn'}")
    print()
    
    confirm = input("Tiếp tục? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Đã hủy!")
        return
    
    # Build command
    script_path = Path(__file__).parent / "database" / "fetch_mooc_h5p_data.py"
    
    cmd = [sys.executable, str(script_path), "--course-id", course_id]
    
    if sessionid:
        cmd.extend(["--sessionid", sessionid])
    
    if limit:
        cmd.extend(["--max-users", limit])
    
    print("\n" + "=" * 80)
    print("🚀 BẮT ĐẦU FETCH...")
    print("=" * 80)
    print(f"\nCommand: {' '.join(cmd)}\n")
    
    try:
        # Run script
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print("\n" + "=" * 80)
            print("✅ HOÀN TẤT!")
            print("=" * 80)
            print("\n💡 Kiểm tra kết quả:")
            print("   1. Chạy: python check_courses.py")
            print("   2. Mở dashboard: http://localhost:5173")
            print("   3. Refresh browser (Ctrl+Shift+R)")
            print("   4. Chọn môn học mới từ dropdown")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ LỖI: Script failed with exit code {e.returncode}")
        print("\n💡 Kiểm tra:")
        print("   1. Database có đang chạy không? (docker-compose ps)")
        print("   2. Check logs: logs/fetch_data_*.log")
        print("   3. Course ID có đúng không?")
    except Exception as e:
        print(f"\n❌ LỖI: {e}")

if __name__ == "__main__":
    main()
