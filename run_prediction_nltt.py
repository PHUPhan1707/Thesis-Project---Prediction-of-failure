# -*- coding: utf-8 -*-
"""
Chạy prediction cho môn NLTT sử dụng Model V4
(Tự động lưu vào CẢ raw_data VÀ predictions table)
"""
import sys
import os
import io
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.inference_service import InferenceService
from backend.db import fetch_one

course_id = "course-v1:UEL+NLTT241225+2025_12"

print("=" * 80)
print(f"CHẠY PREDICTION CHO MÔN NLTT")
print("=" * 80)

# 1. Check current state
print("\n1. Kiểm tra student_features:")
stats = fetch_one("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN h5p_total_score > 0 THEN 1 END) as has_h5p,
        AVG(h5p_total_score) as avg_h5p,
        AVG(weeks_since_enrollment) as avg_weeks
    FROM student_features
    WHERE course_id = %s
""", (course_id,))

if stats:
    print(f"   Total students: {stats['total']}")
    print(f"   Students with H5P: {stats['has_h5p']}")
    print(f"   Avg H5P score: {stats['avg_h5p']:.2f}")
    print(f"   Avg weeks enrolled: {stats['avg_weeks']:.2f}")
else:
    print("   ❌ Không có data!")
    sys.exit(1)

# 2. Load model và predict
print("\n2. Loading Model V4...")
try:
    service = InferenceService()
    print(f"   ✅ Model loaded: {service.model_path}")
except Exception as e:
    print(f"   ❌ Error loading model: {e}")
    sys.exit(1)

# 3. Run prediction
print("\n3. Chạy prediction...")
print("   ✅ Tự động lưu vào CẢ 'raw_data' VÀ 'predictions' table")
print("   (Có thể mất 10-60 giây...)")

try:
    result_df = service.predict_course(course_id, save_db=True)
    
    print(f"\n✅ HOÀN THÀNH!")
    print(f"   Predicted: {len(result_df)} students")
    
    # Show risk distribution
    if len(result_df) > 0:
        print(f"\n📊 Phân bố risk score:")
        high = len(result_df[result_df['fail_risk_score'] >= 70])
        medium = len(result_df[(result_df['fail_risk_score'] >= 40) & (result_df['fail_risk_score'] < 70)])
        low = len(result_df[result_df['fail_risk_score'] < 40])
        
        print(f"   - HIGH (>=70%): {high} students")
        print(f"   - MEDIUM (40-69%): {medium} students")
        print(f"   - LOW (<40%): {low} students")
        print(f"   - Avg risk: {result_df['fail_risk_score'].mean():.1f}%")
        
        # Top 5 at-risk
        print(f"\n⚠️  Top 5 sinh viên nguy cơ cao:")
        top5 = result_df.nlargest(5, 'fail_risk_score')[['user_id', 'fail_risk_score']]
        for idx, row in top5.iterrows():
            print(f"      - User {row['user_id']}: {row['fail_risk_score']:.1f}%")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ Predictions đã được lưu vào database!")
print("   Bạn có thể xem trên dashboard hoặc query từ bảng 'predictions'")
print("=" * 80)
