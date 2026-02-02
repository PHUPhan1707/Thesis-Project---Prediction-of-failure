# -*- coding: utf-8 -*-
"""
Kiểm tra predictions của môn NLTT - tại sao dashboard hiện 50%?
"""
import sys
import os
import io
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.db import fetch_all, fetch_one

course_id = "course-v1:UEL+NLTT241225+2025_12"

print("=" * 80)
print("KIỂM TRA PREDICTIONS CỦA MÔN NLTT")
print("=" * 80)

# 1. Check raw_data (V1)
print("\n1. Kiểm tra raw_data (V1 - cũ):")
raw_stats = fetch_one("""
    SELECT 
        COUNT(*) as total,
        MIN(fail_risk_score) as min_risk,
        MAX(fail_risk_score) as max_risk,
        AVG(fail_risk_score) as avg_risk,
        COUNT(DISTINCT fail_risk_score) as unique_scores
    FROM raw_data
    WHERE course_id = %s
""", (course_id,))

if raw_stats and raw_stats['total'] > 0:
    print(f"   Total records: {raw_stats['total']}")
    print(f"   Risk score range: {raw_stats['min_risk']} - {raw_stats['max_risk']}")
    print(f"   Avg risk: {raw_stats['avg_risk']:.2f}%")
    print(f"   Unique scores: {raw_stats['unique_scores']}")
    
    # Sample
    samples = fetch_all("""
        SELECT user_id, fail_risk_score, extracted_at
        FROM raw_data
        WHERE course_id = %s
        ORDER BY extracted_at DESC
        LIMIT 5
    """, (course_id,))
    
    print("\n   📊 Sample (5 latest records):")
    for s in samples:
        print(f"      User {s['user_id']}: {s['fail_risk_score']}% at {s['extracted_at']}")

# 2. Check predictions (V2)
print("\n2. Kiểm tra predictions (V2 - mới):")
pred_stats = fetch_one("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN is_latest = 1 THEN 1 END) as latest_count,
        MIN(CASE WHEN is_latest = 1 THEN fail_risk_score END) as min_risk,
        MAX(CASE WHEN is_latest = 1 THEN fail_risk_score END) as max_risk,
        AVG(CASE WHEN is_latest = 1 THEN fail_risk_score END) as avg_risk,
        COUNT(DISTINCT CASE WHEN is_latest = 1 THEN fail_risk_score END) as unique_scores
    FROM predictions
    WHERE course_id = %s
""", (course_id,))

if pred_stats and pred_stats['total'] > 0:
    print(f"   Total predictions: {pred_stats['total']}")
    print(f"   Latest predictions: {pred_stats['latest_count']}")
    print(f"   Risk score range: {pred_stats['min_risk']} - {pred_stats['max_risk']}")
    print(f"   Avg risk: {pred_stats['avg_risk']:.2f}%")
    print(f"   Unique scores: {pred_stats['unique_scores']}")
    
    # Sample latest
    samples = fetch_all("""
        SELECT user_id, fail_risk_score, model_name, predicted_at, is_latest
        FROM predictions
        WHERE course_id = %s
        ORDER BY predicted_at DESC
        LIMIT 5
    """, (course_id,))
    
    print("\n   📊 Sample (5 latest predictions):")
    for s in samples:
        latest = "✅" if s['is_latest'] else "❌"
        print(f"      {latest} User {s['user_id']}: {s['fail_risk_score']}% ({s['model_name']}) at {s['predicted_at']}")

# 3. Check conflict: cả raw_data VÀ predictions có data khác nhau?
print("\n3. So sánh raw_data vs predictions:")

# Lấy 1 user để so sánh
sample_user = fetch_one("""
    SELECT user_id 
    FROM raw_data 
    WHERE course_id = %s 
    LIMIT 1
""", (course_id,))

if sample_user:
    uid = sample_user['user_id']
    
    # Từ raw_data
    raw_score = fetch_one("""
        SELECT fail_risk_score, extracted_at
        FROM raw_data
        WHERE course_id = %s AND user_id = %s
        ORDER BY extracted_at DESC
        LIMIT 1
    """, (course_id, uid))
    
    # Từ predictions
    pred_score = fetch_one("""
        SELECT fail_risk_score, predicted_at, is_latest
        FROM predictions
        WHERE course_id = %s AND user_id = %s AND is_latest = 1
        LIMIT 1
    """, (course_id, uid))
    
    print(f"\n   User {uid}:")
    if raw_score:
        print(f"      raw_data: {raw_score['fail_risk_score']}% (at {raw_score['extracted_at']})")
    else:
        print(f"      raw_data: KHÔNG có")
    
    if pred_score:
        print(f"      predictions: {pred_score['fail_risk_score']}% (at {pred_score['predicted_at']})")
    else:
        print(f"      predictions: KHÔNG có")
    
    if raw_score and pred_score:
        if raw_score['fail_risk_score'] != pred_score['fail_risk_score']:
            print(f"\n   ⚠️  CONFLICT: raw_data ({raw_score['fail_risk_score']}%) != predictions ({pred_score['fail_risk_score']}%)")

# 4. Check backend đang dùng bảng nào?
print("\n4. Backend API query từ bảng nào?")
print("   📝 Kiểm tra file: backend/app.py")
print("   Nếu query từ 'raw_data' → hiện 50%")
print("   Nếu query từ 'predictions' JOIN 'student_features' → hiện 70.3%")

print("\n" + "=" * 80)
print("KẾT LUẬN:")
print("=" * 80)

# Determine issue
if raw_stats and raw_stats['avg_risk'] == 50.0:
    print("❌ VẤN ĐỀ: raw_data có placeholder 50%")
    if pred_stats and pred_stats['avg_risk'] != 50.0:
        print("✅ predictions có risk score thật từ Model V4")
        print("\n💡 NGUYÊN NHÂN:")
        print("   Backend/Frontend đang query từ 'raw_data' thay vì 'predictions'")
        print("\n🔧 GIẢI PHÁP:")
        print("   1. Update backend/app.py: query từ 'predictions' (V2)")
        print("   2. Hoặc update raw_data với predictions mới")
        print("   3. Hoặc xóa raw_data để force dùng predictions")
    else:
        print("⚠️  Cả raw_data VÀ predictions đều = 50%")
        print("   → Cần chạy lại prediction thật")
elif pred_stats and pred_stats['avg_risk'] == 50.0:
    print("❌ VẤN ĐỀ: predictions cũng là placeholder 50%")
    print("   → Script run_prediction_nltt.py có thể CHƯA ghi đúng vào DB")
else:
    print("✅ Data có vẻ OK, check frontend/API logic")

print("=" * 80)
