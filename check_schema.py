# -*- coding: utf-8 -*-
"""
Kiểm tra schema của các bảng
"""
import sys
import os
import io
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.db import fetch_all

print("=" * 80)
print("KIỂM TRA DATABASE SCHEMA")
print("=" * 80)

# 1. Kiểm tra cấu trúc h5p_scores
print("\n1. Cấu trúc bảng h5p_scores:")
h5p_cols = fetch_all("DESCRIBE h5p_scores")
for col in h5p_cols:
    print(f"   - {col['Field']}: {col['Type']}")

# 2. Kiểm tra cấu trúc student_features
print("\n2. Cấu trúc bảng student_features:")
sf_cols = fetch_all("DESCRIBE student_features")
for col in sf_cols:
    print(f"   - {col['Field']}: {col['Type']}")

# 3. Sample data từ h5p_scores
print("\n3. Sample data h5p_scores (3 records):")
samples = fetch_all("""
    SELECT *
    FROM h5p_scores
    WHERE course_id = 'course-v1:UEL+NLTT241225+2025_12'
    LIMIT 3
""")

for s in samples:
    print(f"\n   Record:")
    for key, val in s.items():
        print(f"      {key}: {val}")

# 4. Sample data từ student_features
print("\n4. Sample data student_features (3 records):")
sf_samples = fetch_all("""
    SELECT *
    FROM student_features
    WHERE course_id = 'course-v1:UEL+NLTT241225+2025_12'
    LIMIT 3
""")

for s in sf_samples:
    print(f"\n   User {s.get('user_id', 'N/A')}:")
    # Chỉ hiển thị các fields quan trọng
    important_fields = [
        'h5p_total_score', 'h5p_unique_content_accessed',
        'video_total_views', 'quiz_total_score',
        'discussion_total_interactions', 'weeks_since_enrollment'
    ]
    for field in important_fields:
        if field in s:
            print(f"      {field}: {s[field]}")

print("\n" + "=" * 80)
