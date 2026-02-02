# -*- coding: utf-8 -*-
"""
Debug: Tại sao student_features của NLTT có toàn 0 0 0?
"""
import sys
import os
import io
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.db import fetch_all, fetch_one

course_id = "course-v1:UEL+NLTT241225+2025_12"

print("=" * 80)
print("DEBUG: TẠI SAO STUDENT_FEATURES CỦA NLTT TOÀN 0?")
print("=" * 80)

# 1. Kiểm tra h5p_scores
print("\n1. Kiểm tra h5p_scores (Raw data từ H5P):")
h5p_check = fetch_one("""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT user_id) as unique_users,
        MIN(score) as min_score,
        MAX(score) as max_score,
        AVG(score) as avg_score
    FROM h5p_scores
    WHERE course_id = %s
""", (course_id,))

if h5p_check and h5p_check['total_records'] > 0:
    print(f"   ✅ Total records: {h5p_check['total_records']}")
    print(f"   ✅ Unique users: {h5p_check['unique_users']}")
    print(f"   ✅ Score range: {h5p_check['min_score']} - {h5p_check['max_score']}")
    print(f"   ✅ Avg score: {h5p_check['avg_score']:.2f}")
    
    # Sample data
    print("\n   📊 Sample h5p_scores (5 records):")
    samples = fetch_all("""
        SELECT user_id, content_id, score, max_score, created_at
        FROM h5p_scores
        WHERE course_id = %s
        LIMIT 5
    """, (course_id,))
    
    for s in samples:
        print(f"      - User {s['user_id']}: score={s['score']}/{s['max_score']} (at {s['created_at']})")
else:
    print("   ❌ KHÔNG có data trong h5p_scores!")

# 2. Kiểm tra các bảng data khác
print("\n2. Kiểm tra các bảng data nguồn khác:")

tables = [
    ('mooc_video_interactions', 'video_id'),
    ('mooc_quiz_attempts', 'quiz_id'),
    ('mooc_grades', 'grade_percentage'),
    ('h5p_interactions', 'interaction_type'),
]

for table, col in tables:
    try:
        result = fetch_one(f"""
            SELECT COUNT(*) as count
            FROM {table}
            WHERE course_id = %s
        """, (course_id,))
        
        if result and result['count'] > 0:
            print(f"   ✅ {table}: {result['count']} records")
        else:
            print(f"   ⚠️  {table}: 0 records")
    except Exception as e:
        print(f"   ❌ {table}: Error - {e}")

# 3. Kiểm tra student_features
print("\n3. Kiểm tra student_features (Processed features):")
sf_check = fetch_one("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN h5p_total_score > 0 THEN 1 END) as has_h5p,
        AVG(h5p_total_score) as avg_h5p_score,
        AVG(video_total_duration_seconds) as avg_video_duration,
        AVG(quiz_total_score) as avg_quiz_score,
        AVG(weeks_since_enrollment) as avg_weeks
    FROM student_features
    WHERE course_id = %s
""", (course_id,))

if sf_check:
    print(f"   Total students: {sf_check['total']}")
    print(f"   Students with H5P score > 0: {sf_check['has_h5p']}")
    print(f"   Avg H5P score: {sf_check['avg_h5p_score']}")
    print(f"   Avg video duration: {sf_check['avg_video_duration']}")
    print(f"   Avg quiz score: {sf_check['avg_quiz_score']}")
    print(f"   Avg weeks since enrollment: {sf_check['avg_weeks']}")

# 4. Chi tiết 3 students đầu tiên
print("\n4. Chi tiết student_features (3 students đầu):")
details = fetch_all("""
    SELECT 
        user_id,
        h5p_total_score,
        h5p_avg_score,
        video_total_duration_seconds,
        quiz_total_score,
        discussion_total_interactions,
        weeks_since_enrollment,
        updated_at
    FROM student_features
    WHERE course_id = %s
    LIMIT 3
""", (course_id,))

for d in details:
    print(f"\n   User {d['user_id']}:")
    print(f"      - h5p_total_score: {d['h5p_total_score']}")
    print(f"      - h5p_avg_score: {d['h5p_avg_score']}")
    print(f"      - video_duration: {d['video_total_duration_seconds']}")
    print(f"      - quiz_score: {d['quiz_total_score']}")
    print(f"      - discussion: {d['discussion_total_interactions']}")
    print(f"      - weeks_enrolled: {d['weeks_since_enrollment']}")
    print(f"      - updated_at: {d['updated_at']}")

# 5. So sánh: h5p_scores vs student_features cho 1 user cụ thể
print("\n5. So sánh h5p_scores vs student_features (1 user ngẫu nhiên):")

# Lấy 1 user có data trong h5p_scores
sample_user = fetch_one("""
    SELECT user_id
    FROM h5p_scores
    WHERE course_id = %s
    LIMIT 1
""", (course_id,))

if sample_user:
    uid = sample_user['user_id']
    
    # Data từ h5p_scores
    h5p_raw = fetch_all("""
        SELECT content_id, score, max_score, created_at
        FROM h5p_scores
        WHERE course_id = %s AND user_id = %s
        ORDER BY created_at
    """, (course_id, uid))
    
    print(f"\n   User {uid} - h5p_scores (raw):")
    total_score = 0
    for h in h5p_raw:
        print(f"      Content {h['content_id']}: {h['score']}/{h['max_score']}")
        total_score += float(h['score']) if h['score'] else 0
    print(f"      → Total score: {total_score}")
    
    # Data từ student_features
    sf_data = fetch_one("""
        SELECT h5p_total_score, h5p_avg_score, h5p_completion_rate
        FROM student_features
        WHERE course_id = %s AND user_id = %s
    """, (course_id, uid))
    
    if sf_data:
        print(f"\n   User {uid} - student_features (processed):")
        print(f"      h5p_total_score: {sf_data['h5p_total_score']}")
        print(f"      h5p_avg_score: {sf_data['h5p_avg_score']}")
        print(f"      h5p_completion_rate: {sf_data['h5p_completion_rate']}")
        
        if float(sf_data['h5p_total_score'] or 0) == 0 and total_score > 0:
            print("\n   ❌ PHÁT HIỆN VẤN ĐỀ:")
            print(f"      - h5p_scores có data (total={total_score})")
            print(f"      - student_features = 0")
            print("      → ETL script KHÔNG tính toán đúng!")

print("\n" + "=" * 80)
print("KẾT LUẬN:")
print("=" * 80)

# Tổng kết
if h5p_check and h5p_check['total_records'] > 0:
    if sf_check and sf_check['has_h5p'] == 0:
        print("❌ VẤN ĐỀ XÁC NHẬN:")
        print("   - h5p_scores CÓ data")
        print("   - student_features KHÔNG có (toàn 0)")
        print("\n🔍 NGUYÊN NHÂN CÓ THỂ:")
        print("   1. ETL script (fetch_mooc_h5p_data.py) KHÔNG populate student_features")
        print("   2. Migration V2 KHÔNG migrate h5p_scores → student_features")
        print("   3. Logic tính toán trong migration bị lỗi")
        print("\n💡 GIẢI PHÁP:")
        print("   1. Kiểm tra file: database/migrate_to_v2.py")
        print("   2. Kiểm tra logic: Cách tính h5p_total_score trong migration")
        print("   3. Re-run migration hoặc update student_features manually")
    else:
        print("✅ Có vẻ OK, student_features có data từ h5p_scores")
else:
    print("⚠️  h5p_scores KHÔNG có data → student_features đúng là phải = 0")

print("=" * 80)
