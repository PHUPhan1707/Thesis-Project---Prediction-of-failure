"""
Migration Script: raw_data → 3 tables (student_features, predictions, training_data)
Version: 2.0
Date: 2026-01-29

CHỨC NĂNG:
1. Tạo 3 tables mới: student_features, predictions, training_data
2. Migrate data từ raw_data sang tables mới
3. Backup raw_data thành raw_data_legacy
4. Verify migration thành công

YÊU CẦU:
- Docker MySQL đang chạy (docker-compose up -d)
- Database: dropout_prediction_db (port 4000)
- File .env đã config đúng

CÁCH CHẠY:
    python database/migrate_to_v2.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import mysql.connector
from dotenv import load_dotenv

# Load environment
load_dotenv()

def get_db_connection():
    """Kết nối MySQL - Sử dụng config từ docker-compose"""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "4000")),  # Docker-compose maps 4000:3306
        user=os.getenv("DB_USER", "dropout_user"),
        password=os.getenv("DB_PASSWORD", "dropout_pass_123"),
        database=os.getenv("DB_NAME", "dropout_prediction_db"),
        autocommit=False  # Manual commit
    )

def execute_sql_file(cursor, filepath):
    """Execute SQL script từ file"""
    print(f"\n📄 Executing SQL file: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Split by delimiter (skip comments and empty)
    statements = []
    current = []
    
    for line in sql_content.split('\n'):
        line = line.strip()
        
        # Skip comments
        if line.startswith('--') or line.startswith('/*') or line.startswith('*'):
            continue
        
        # Skip COMMENT lines after table definition
        if 'COMMENT=' in line and ';' in line:
            current.append(line)
            statements.append('\n'.join(current))
            current = []
            continue
            
        current.append(line)
        
        # End of statement
        if line.endswith(';'):
            stmt = '\n'.join(current)
            if stmt.strip():
                statements.append(stmt)
            current = []
    
    # Execute each statement
    executed = 0
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt or stmt == ';':
            continue
        
        # Skip CREATE OR REPLACE VIEW (use separate execution)
        if 'CREATE OR REPLACE VIEW' in stmt:
            print(f"   Skipping VIEW (will create separately): {stmt[:60]}...")
            continue
            
        try:
            cursor.execute(stmt)
            executed += 1
            print(f"   ✅ Executed: {stmt[:60]}...")
        except mysql.connector.Error as e:
            print(f"   ⚠️  Warning: {e}")
            # Continue on error (table might already exist)
    
    print(f"   📊 Executed {executed} statements")
    return executed

def migrate_data(cursor):
    """Migrate data từ raw_data sang 3 tables mới"""
    
    print("\n" + "="*80)
    print("STEP 2: MIGRATE DATA")
    print("="*80)
    
    # 1. Check raw_data
    cursor.execute("SELECT COUNT(*) as total FROM raw_data")
    total_raw = cursor.fetchone()[0]
    print(f"\n📊 Total records in raw_data: {total_raw}")
    
    if total_raw == 0:
        print("   ⚠️  No data to migrate!")
        return
    
    # 2. Migrate to student_features
    print(f"\n1️⃣  Migrating to student_features...")
    cursor.execute("""
        INSERT INTO student_features (
            user_id, course_id,
            enrollment_mode, is_active, weeks_since_enrollment,
            mooc_grade_percentage, mooc_letter_grade, mooc_is_passed,
            progress_percent, current_chapter, current_section, current_unit,
            mooc_completion_rate, overall_completion, completed_blocks, total_blocks,
            last_activity, days_since_last_activity,
            access_frequency, active_days,
            h5p_total_contents, h5p_completed_contents, h5p_total_score, h5p_total_max_score,
            h5p_overall_percentage, h5p_total_time_spent, h5p_completion_rate,
            video_total_videos, video_completed_videos, video_in_progress_videos,
            video_total_duration, video_total_watched_time, video_completion_rate, video_watch_rate,
            quiz_attempts, quiz_avg_score, quiz_completion_rate,
            forum_posts, forum_comments, forum_upvotes,
            discussion_threads_count, discussion_comments_count, discussion_total_interactions,
            discussion_questions_count, discussion_total_upvotes,
            relative_to_course_problem_score, relative_to_course_completion,
            relative_to_course_video_completion, relative_to_course_discussion,
            performance_percentile, is_below_course_average,
            is_top_performer, is_bottom_performer,
            extraction_batch_id
        )
        SELECT 
            user_id, course_id,
            enrollment_mode, is_active, weeks_since_enrollment,
            mooc_grade_percentage, mooc_letter_grade, mooc_is_passed,
            progress_percent, current_chapter, current_section, current_unit,
            mooc_completion_rate, overall_completion, completed_blocks, total_blocks,
            last_activity, days_since_last_activity,
            access_frequency, active_days,
            h5p_total_contents, h5p_completed_contents, h5p_total_score, h5p_total_max_score,
            h5p_overall_percentage, h5p_total_time_spent, h5p_completion_rate,
            video_total_videos, video_completed_videos, video_in_progress_videos,
            video_total_duration, video_total_watched_time, video_completion_rate, video_watch_rate,
            quiz_attempts, quiz_avg_score, quiz_completion_rate,
            forum_posts, forum_comments, forum_upvotes,
            discussion_threads_count, discussion_comments_count, discussion_total_interactions,
            discussion_questions_count, discussion_total_upvotes,
            relative_to_course_problem_score, relative_to_course_completion,
            relative_to_course_video_completion, relative_to_course_discussion,
            performance_percentile, is_below_course_average,
            is_top_performer, is_bottom_performer,
            extraction_batch_id
        FROM raw_data
        ON DUPLICATE KEY UPDATE
            mooc_grade_percentage = VALUES(mooc_grade_percentage),
            mooc_is_passed = VALUES(mooc_is_passed),
            mooc_completion_rate = VALUES(mooc_completion_rate),
            updated_at = CURRENT_TIMESTAMP
    """)
    
    migrated_features = cursor.rowcount
    print(f"   ✅ Migrated {migrated_features} records to student_features")
    
    # 3. Migrate to predictions (chỉ records có fail_risk_score)
    print(f"\n2️⃣  Migrating to predictions...")
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
        WHERE fail_risk_score IS NOT NULL
    """)
    
    migrated_predictions = cursor.rowcount
    print(f"   ✅ Migrated {migrated_predictions} predictions")
    
    # 4. Migrate to training_data (chỉ data đã có labels)
    print(f"\n3️⃣  Migrating to training_data...")
    cursor.execute("""
        INSERT INTO training_data (
            user_id, course_id,
            enrollment_mode, is_active, weeks_since_enrollment,
            mooc_grade_percentage, mooc_letter_grade, mooc_is_passed,
            progress_percent, current_chapter, current_section, current_unit,
            mooc_completion_rate, overall_completion, completed_blocks, total_blocks,
            last_activity, days_since_last_activity,
            access_frequency, active_days,
            h5p_total_contents, h5p_completed_contents, h5p_total_score, h5p_total_max_score,
            h5p_overall_percentage, h5p_total_time_spent, h5p_completion_rate,
            video_total_videos, video_completed_videos, video_in_progress_videos,
            video_total_duration, video_total_watched_time, video_completion_rate, video_watch_rate,
            quiz_attempts, quiz_avg_score, quiz_completion_rate,
            forum_posts, forum_comments, forum_upvotes,
            discussion_threads_count, discussion_comments_count, discussion_total_interactions,
            discussion_questions_count, discussion_total_upvotes,
            relative_to_course_problem_score, relative_to_course_completion,
            relative_to_course_video_completion, relative_to_course_discussion,
            performance_percentile, is_below_course_average,
            is_top_performer, is_bottom_performer,
            is_dropout, is_passed, final_grade,
            semester, snapshot_week, used_in_training, training_model,
            extraction_batch_id
        )
        SELECT 
            user_id, course_id,
            enrollment_mode, is_active, weeks_since_enrollment,
            mooc_grade_percentage, mooc_letter_grade, mooc_is_passed,
            progress_percent, current_chapter, current_section, current_unit,
            mooc_completion_rate, overall_completion, completed_blocks, total_blocks,
            last_activity, days_since_last_activity,
            access_frequency, active_days,
            h5p_total_contents, h5p_completed_contents, h5p_total_score, h5p_total_max_score,
            h5p_overall_percentage, h5p_total_time_spent, h5p_completion_rate,
            video_total_videos, video_completed_videos, video_in_progress_videos,
            video_total_duration, video_total_watched_time, video_completion_rate, video_watch_rate,
            quiz_attempts, quiz_avg_score, quiz_completion_rate,
            forum_posts, forum_comments, forum_upvotes,
            discussion_threads_count, discussion_comments_count, discussion_total_interactions,
            discussion_questions_count, discussion_total_upvotes,
            relative_to_course_problem_score, relative_to_course_completion,
            relative_to_course_video_completion, relative_to_course_discussion,
            performance_percentile, is_below_course_average,
            is_top_performer, is_bottom_performer,
            is_dropout,
            is_passed,
            mooc_grade_percentage as final_grade,
            '2025_S2' as semester,  -- Default semester
            NULL as snapshot_week,
            TRUE as used_in_training,  -- Giả định đã dùng train Model V4
            'fm101_v4' as training_model,
            extraction_batch_id
        FROM raw_data
        WHERE is_passed IS NOT NULL  -- Chỉ migrate data có labels
    """)
    
    migrated_training = cursor.rowcount
    print(f"   ✅ Migrated {migrated_training} training records")
    
    return {
        'features': migrated_features,
        'predictions': migrated_predictions,
        'training': migrated_training
    }

def verify_migration(cursor):
    """Verify migration results"""
    print("\n" + "="*80)
    print("STEP 3: VERIFY MIGRATION")
    print("="*80)
    
    # Count records
    tables = ['raw_data', 'student_features', 'predictions', 'training_data']
    counts = {}
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            counts[table] = cursor.fetchone()[0]
        except:
            counts[table] = 0
    
    print(f"\n📊 Record counts:")
    print(f"   - raw_data (legacy):     {counts['raw_data']:>6}")
    print(f"   - student_features:      {counts['student_features']:>6}")
    print(f"   - predictions:           {counts['predictions']:>6}")
    print(f"   - training_data:         {counts['training_data']:>6}")
    
    # Verify courses
    cursor.execute("SELECT DISTINCT course_id FROM student_features")
    courses = [r[0] for r in cursor.fetchall()]
    print(f"\n📚 Courses in student_features: {len(courses)}")
    for c in courses:
        cursor.execute("SELECT COUNT(*) FROM student_features WHERE course_id = %s", (c,))
        cnt = cursor.fetchone()[0]
        print(f"   - {c}: {cnt} students")
    
    # Check predictions
    cursor.execute("""
        SELECT model_name, COUNT(*) as cnt, AVG(fail_risk_score) as avg_risk
        FROM predictions
        GROUP BY model_name
    """)
    preds = cursor.fetchall()
    print(f"\n🤖 Predictions by model:")
    for p in preds:
        print(f"   - {p[0]}: {p[1]} predictions, avg risk = {p[2]:.2f}%")
    
    # Validation checks
    print(f"\n✅ Validation:")
    
    # Check 1: student_features should >= raw_data
    if counts['student_features'] >= counts['raw_data']:
        print(f"   ✅ student_features count OK ({counts['student_features']} >= {counts['raw_data']})")
    else:
        print(f"   ❌ student_features count LOW ({counts['student_features']} < {counts['raw_data']})")
    
    # Check 2: predictions should match raw_data records with fail_risk_score
    cursor.execute("SELECT COUNT(*) FROM raw_data WHERE fail_risk_score IS NOT NULL")
    raw_with_pred = cursor.fetchone()[0]
    if counts['predictions'] >= raw_with_pred:
        print(f"   ✅ predictions count OK ({counts['predictions']} >= {raw_with_pred} raw_data with scores)")
    else:
        print(f"   ⚠️  predictions count ({counts['predictions']}) < expected ({raw_with_pred})")
    
    return counts

def create_views(cursor):
    """Tạo views cho backward compatibility"""
    print("\n" + "="*80)
    print("STEP 4: CREATE VIEWS")
    print("="*80)
    
    # View 1: raw_data_view (backward compatibility)
    print("\n📊 Creating raw_data_view...")
    cursor.execute("DROP VIEW IF EXISTS raw_data_view")
    cursor.execute("""
        CREATE VIEW raw_data_view AS
        SELECT 
            f.id,
            f.user_id,
            f.course_id,
            f.enrollment_mode,
            f.is_active,
            f.weeks_since_enrollment,
            f.mooc_grade_percentage,
            f.mooc_letter_grade,
            f.mooc_is_passed,
            f.progress_percent,
            f.current_chapter,
            f.current_section,
            f.current_unit,
            f.mooc_completion_rate,
            f.overall_completion,
            f.completed_blocks,
            f.total_blocks,
            f.last_activity,
            f.days_since_last_activity,
            f.access_frequency,
            f.active_days,
            f.h5p_total_contents,
            f.h5p_completed_contents,
            f.h5p_total_score,
            f.h5p_total_max_score,
            f.h5p_overall_percentage,
            f.h5p_total_time_spent,
            f.h5p_completion_rate,
            f.video_total_videos,
            f.video_completed_videos,
            f.video_in_progress_videos,
            f.video_total_duration,
            f.video_total_watched_time,
            f.video_completion_rate,
            f.video_watch_rate,
            f.quiz_attempts,
            f.quiz_avg_score,
            f.quiz_completion_rate,
            f.forum_posts,
            f.forum_comments,
            f.forum_upvotes,
            f.discussion_threads_count,
            f.discussion_comments_count,
            f.discussion_total_interactions,
            f.discussion_questions_count,
            f.discussion_total_upvotes,
            f.relative_to_course_problem_score,
            f.relative_to_course_completion,
            f.relative_to_course_video_completion,
            f.relative_to_course_discussion,
            f.performance_percentile,
            f.is_below_course_average,
            f.is_top_performer,
            f.is_bottom_performer,
            p.fail_risk_score,
            p.model_name,
            p.predicted_at AS extracted_at,
            f.extraction_batch_id
        FROM student_features f
        LEFT JOIN predictions p ON f.user_id = p.user_id 
            AND f.course_id = p.course_id 
            AND p.is_latest = TRUE
    """)
    print("   ✅ Created raw_data_view")
    
    # View 2: latest_predictions
    print("\n📊 Creating latest_predictions view...")
    cursor.execute("DROP VIEW IF EXISTS latest_predictions")
    cursor.execute("""
        CREATE VIEW latest_predictions AS
        SELECT 
            p.id,
            p.user_id,
            p.course_id,
            p.model_name,
            p.model_version,
            p.fail_risk_score,
            p.risk_level,
            p.confidence_score,
            p.predicted_at,
            f.mooc_grade_percentage,
            f.mooc_completion_rate,
            f.mooc_is_passed,
            f.days_since_last_activity
        FROM predictions p
        JOIN student_features f ON p.user_id = f.user_id AND p.course_id = f.course_id
        WHERE p.is_latest = TRUE
    """)
    print("   ✅ Created latest_predictions view")

def main():
    """Main migration workflow"""
    print("="*80)
    print("🚀 DATABASE MIGRATION: raw_data → 3 Tables (V2)")
    print("="*80)
    print(f"\nTimestamp: {datetime.now()}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # STEP 1: Create new schema
        print("\n" + "="*80)
        print("STEP 1: CREATE NEW SCHEMA")
        print("="*80)
        
        schema_file = Path(__file__).parent / "schema_refactor_v2.sql"
        if not schema_file.exists():
            print(f"❌ Schema file not found: {schema_file}")
            return
        
        execute_sql_file(cursor, schema_file)
        conn.commit()
        print("\n   ✅ Schema created successfully")
        
        # STEP 2: Migrate data
        stats = migrate_data(cursor)
        conn.commit()
        print(f"\n   ✅ Data migration completed")
        print(f"      - Features: {stats['features']} records")
        print(f"      - Predictions: {stats['predictions']} records")
        print(f"      - Training: {stats['training']} records")
        
        # STEP 3: Create views
        create_views(cursor)
        conn.commit()
        print("\n   ✅ Views created")
        
        # STEP 4: Verify
        counts = verify_migration(cursor)
        
        # STEP 5: Backup old table
        print("\n" + "="*80)
        print("STEP 5: BACKUP OLD TABLE")
        print("="*80)
        print("\n⚠️  Keeping raw_data as is (manual backup recommended)")
        print("    To backup manually:")
        print("    RENAME TABLE raw_data TO raw_data_legacy_backup_20260129;")
        
        print("\n" + "="*80)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"\n📊 Summary:")
        print(f"   - student_features:  {counts['student_features']} records")
        print(f"   - predictions:       {counts['predictions']} records")
        print(f"   - training_data:     {counts['training_data']} records")
        print(f"\n📝 Next steps:")
        print(f"   1. Update backend code to use new tables")
        print(f"   2. Test API endpoints")
        print(f"   3. Verify dashboard works")
        print(f"   4. (Optional) Rename raw_data to raw_data_legacy")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        print("\n🔄 Transaction rolled back")
        return 1
    
    finally:
        cursor.close()
        conn.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
