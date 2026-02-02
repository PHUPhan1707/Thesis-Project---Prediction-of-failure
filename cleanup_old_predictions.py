# -*- coding: utf-8 -*-
"""
Dọn dẹp bảng predictions: xóa bản ghi cũ, chỉ giữ 1 bản ghi mới nhất cho mỗi (user_id, course_id).
Chạy 1 lần để xóa các bản ghi trùng (50% cũ, v.v.)
"""
import sys
import os
import io
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.db import get_db_connection

def cleanup_old_predictions(course_id=None):
    """
    Xóa các bản ghi prediction cũ, chỉ giữ 1 bản ghi có id lớn nhất (mới nhất) cho mỗi (user_id, course_id).
    
    Args:
        course_id: Nếu có, chỉ cleanup course đó; không thì cleanup toàn bộ.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("=" * 80)
        print("DỌN DẸP BẢNG PREDICTIONS (chỉ giữ 1 bản ghi mới nhất / user / course)")
        print("=" * 80)
        
        course_filter = f"AND course_id = %s" if course_id else ""
        params = (course_id,) if course_id else ()
        
        # Đếm trước khi xóa
        cursor.execute(f"""
            SELECT COUNT(*) as total
            FROM predictions
            WHERE 1=1 {course_filter}
        """, params)
        total_before = cursor.fetchone()[0]
        
        # Xóa các bản ghi KHÔNG phải là bản ghi có id lớn nhất cho mỗi (user_id, course_id)
        # Giữ lại bản ghi có id = MAX(id) cho mỗi (user_id, course_id)
        if course_id:
            cursor.execute("""
                DELETE p FROM predictions p
                INNER JOIN (
                    SELECT user_id, course_id, MAX(id) as keep_id
                    FROM predictions
                    WHERE course_id = %s
                    GROUP BY user_id, course_id
                ) latest ON p.user_id = latest.user_id AND p.course_id = latest.course_id
                WHERE p.id != latest.keep_id AND p.course_id = %s
            """, (course_id, course_id))
        else:
            cursor.execute("""
                DELETE p FROM predictions p
                INNER JOIN (
                    SELECT user_id, course_id, MAX(id) as keep_id
                    FROM predictions
                    GROUP BY user_id, course_id
                ) latest ON p.user_id = latest.user_id AND p.course_id = latest.course_id
                WHERE p.id != latest.keep_id
            """)
        
        deleted = cursor.rowcount
        conn.commit()
        
        # Đếm sau khi xóa
        cursor.execute(f"""
            SELECT COUNT(*) as total
            FROM predictions
            WHERE 1=1 {course_filter}
        """, params)
        total_after = cursor.fetchone()[0]
        
        print(f"\n   Trước: {total_before} bản ghi")
        print(f"   Đã xóa: {deleted} bản ghi cũ/trùng")
        print(f"   Sau: {total_after} bản ghi (1 bản ghi / user / course)")
        print("\n✅ Dọn dẹp xong!")
        print("=" * 80)
        
        return deleted
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Cleanup old predictions')
    parser.add_argument('--course-id', type=str, help='Chỉ cleanup course này (optional)')
    args = parser.parse_args()
    
    cleanup_old_predictions(args.course_id)
