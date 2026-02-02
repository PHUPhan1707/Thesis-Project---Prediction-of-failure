# -*- coding: utf-8 -*-
"""
Sync predictions từ raw_data → predictions table (V2)
Dùng cho trường hợp model_v4_service.py (V1) đã ghi vào raw_data
"""
import sys
import os
import io
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.db import get_db_connection

course_id = "course-v1:UEL+NLTT241225+2025_12"

print("=" * 80)
print("SYNC PREDICTIONS: raw_data → predictions (V2)")
print("=" * 80)

conn = get_db_connection()
cursor = conn.cursor()

try:
    # 1. Mark old predictions as not latest
    print("\n1. Marking old predictions as not latest...")
    cursor.execute("""
        UPDATE predictions
        SET is_latest = 0
        WHERE course_id = %s
    """, (course_id,))
    conn.commit()
    print(f"   ✅ Updated {cursor.rowcount} old predictions")
    
    # 2. Insert/Update from raw_data
    print("\n2. Syncing from raw_data...")
    cursor.execute("""
        INSERT INTO predictions (
            user_id, course_id,
            model_name, model_version, model_path,
            fail_risk_score, risk_level,
            snapshot_grade, snapshot_completion_rate, snapshot_days_inactive,
            predicted_at, is_latest
        )
        SELECT 
            user_id, 
            course_id,
            'fm101_v4' as model_name,
            'v4.0.0' as model_version,
            './models/fm101_model_v4.cbm' as model_path,
            fail_risk_score,
            CASE 
                WHEN fail_risk_score >= 70 THEN 'HIGH'
                WHEN fail_risk_score >= 40 THEN 'MEDIUM'
                ELSE 'LOW'
            END as risk_level,
            mooc_grade_percentage as snapshot_grade,
            mooc_completion_rate as snapshot_completion_rate,
            days_since_last_activity as snapshot_days_inactive,
            extracted_at as predicted_at,
            TRUE as is_latest
        FROM raw_data
        WHERE course_id = %s
        ON DUPLICATE KEY UPDATE
            fail_risk_score = VALUES(fail_risk_score),
            risk_level = VALUES(risk_level),
            predicted_at = VALUES(predicted_at),
            is_latest = VALUES(is_latest)
    """, (course_id,))
    conn.commit()
    
    print(f"   ✅ Synced {cursor.rowcount} predictions")
    
    # 3. Verify
    print("\n3. Verification:")
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(fail_risk_score) as min_risk,
            MAX(fail_risk_score) as max_risk,
            AVG(fail_risk_score) as avg_risk,
            COUNT(DISTINCT fail_risk_score) as unique_scores
        FROM predictions
        WHERE course_id = %s AND is_latest = 1
    """, (course_id,))
    
    result = cursor.fetchone()
    print(f"   Total predictions: {result[0]}")
    print(f"   Risk range: {result[1]:.2f}% - {result[2]:.2f}%")
    print(f"   Avg risk: {result[3]:.2f}%")
    print(f"   Unique scores: {result[4]}")
    
    # Sample
    cursor.execute("""
        SELECT user_id, fail_risk_score, risk_level
        FROM predictions
        WHERE course_id = %s AND is_latest = 1
        ORDER BY fail_risk_score DESC
        LIMIT 5
    """, (course_id,))
    
    print("\n   📊 Top 5 risk students:")
    for row in cursor.fetchall():
        print(f"      User {row[0]}: {row[1]:.2f}% ({row[2]})")
    
    print("\n✅ SYNC HOÀN THÀNH!")
    print("=" * 80)
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
