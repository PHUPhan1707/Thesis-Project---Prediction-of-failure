# -*- coding: utf-8 -*-
"""
Populate student_features từ các bảng nguồn.

Ưu tiên lấy data theo thứ tự:
  1. Trực tiếp từ mooc_grades / mooc_progress / h5p_scores / video_progress_summary
  2. Fallback sang raw_data (nếu bảng chuyên biệt chưa có)

Điều này đảm bảo khóa học mới (lần đầu fetch) luôn có data hiển thị đúng,
ngay cả khi aggregate_raw_data chưa chạy hoặc bị lỗi giữa chừng.
"""
import sys
import os
import io
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.db import get_db_connection

def populate_student_features(course_id=None):
    """
    Populate student_features cho một course (hoặc tất cả).

    Thứ tự ưu tiên dữ liệu:
      - mooc_grade_percentage  : mooc_grades → raw_data → 0
      - mooc_completion_rate   : mooc_progress.completion_rate → raw_data → 0
      - overall_completion     : dashboard_summary → video_progress_summary → raw_data → 0
      - days_since_last_activity: mooc_progress.last_activity tính trực tiếp → raw_data → 999
      - H5P / video data       : h5p_scores aggregate → video_progress_summary → raw_data
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("=" * 80)
        print("POPULATE STUDENT_FEATURES TỪ CÁC BẢNG NGUỒN")
        print("=" * 80)

        # Filter by course
        course_filter = "AND e.course_id = %s" if course_id else ""
        params = (course_id,) if course_id else ()

        print(f"\n📊 Đang xử lý course: {course_id if course_id else 'ALL'}")

        query = f"""
        INSERT INTO student_features (
            user_id, course_id,
            enrollment_mode, is_active, weeks_since_enrollment,
            mooc_grade_percentage, mooc_letter_grade, mooc_is_passed,
            mooc_completion_rate, overall_completion,
            days_since_last_activity,
            h5p_total_contents, h5p_completed_contents,
            h5p_total_score, h5p_total_max_score,
            h5p_overall_percentage, h5p_total_time_spent,
            h5p_completion_rate,
            video_total_videos, video_completed_videos,
            video_total_duration, video_total_watched_time,
            video_completion_rate, video_watch_rate,
            discussion_threads_count, discussion_comments_count,
            discussion_total_interactions, discussion_questions_count,
            discussion_total_upvotes,
            quiz_attempts, h5p_avg_score, quiz_completion_rate,
            extraction_batch_id, updated_at
        )
        SELECT
            e.user_id,
            e.course_id,
            e.mode AS enrollment_mode,
            e.is_active,
            GREATEST(0, TIMESTAMPDIFF(WEEK, e.created, NOW())) AS weeks_since_enrollment,

            -- ── MOOC Grades ─────────────────────────────────────────
            -- Ưu tiên: mooc_grades → raw_data → 0
            COALESCE(
                NULLIF(mg.grade_percentage, 0),
                NULLIF(rd.mooc_grade_percentage, 0),
                0
            ) AS mooc_grade_percentage,

            COALESCE(mg.letter_grade, rd.mooc_letter_grade) AS mooc_letter_grade,
            COALESCE(mg.is_passed, rd.mooc_is_passed) AS mooc_is_passed,

            -- ── Completion (mooc_completion_rate từ mooc_progress) ───
            -- Ưu tiên: mooc_progress.completion_rate → raw_data → 0
            COALESCE(
                NULLIF(mp.completion_rate, 0),
                NULLIF(rd.mooc_completion_rate, 0),
                0
            ) AS mooc_completion_rate,

            -- overall_completion: dashboard_summary → video_progress_summary (proxy) → raw_data → 0
            COALESCE(
                NULLIF(ds.overall_completion, 0),
                NULLIF(rd.overall_completion, 0),
                -- Tính từ video progress nếu không có nguồn khác
                CASE
                    WHEN vps.total_videos > 0
                    THEN ROUND(vps.completed_videos * 100.0 / vps.total_videos, 2)
                    ELSE 0
                END
            ) AS overall_completion,

            -- ── Days since last activity ─────────────────────────────
            -- Tính trực tiếp từ mooc_progress.last_activity → raw_data → 999
            COALESCE(
                CASE
                    WHEN mp.last_activity IS NOT NULL
                    THEN DATEDIFF(NOW(), mp.last_activity)
                    ELSE NULL
                END,
                rd.days_since_last_activity,
                999
            ) AS days_since_last_activity,

            -- ── H5P aggregate từ h5p_scores ──────────────────────────
            COALESCE(h5p_agg.total_contents, rd.h5p_total_contents, 0)     AS h5p_total_contents,
            COALESCE(h5p_agg.completed_contents, rd.h5p_completed_contents, 0) AS h5p_completed_contents,
            COALESCE(h5p_agg.total_score, rd.h5p_total_score, 0)           AS h5p_total_score,
            COALESCE(h5p_agg.total_max_score, rd.h5p_total_max_score, 0)   AS h5p_total_max_score,
            COALESCE(h5p_agg.avg_percentage, rd.h5p_overall_percentage, 0) AS h5p_overall_percentage,
            COALESCE(h5p_agg.total_time_spent, rd.h5p_total_time_spent, 0) AS h5p_total_time_spent,
            CASE
                WHEN COALESCE(h5p_agg.total_contents, 0) > 0
                THEN ROUND(h5p_agg.completed_contents * 100.0 / h5p_agg.total_contents, 2)
                WHEN rd.h5p_completion_rate IS NOT NULL THEN rd.h5p_completion_rate
                ELSE 0
            END AS h5p_completion_rate,

            -- ── Video từ video_progress_summary ──────────────────────
            COALESCE(vps.total_videos, rd.video_total_videos, 0)               AS video_total_videos,
            COALESCE(vps.completed_videos, rd.video_completed_videos, 0)       AS video_completed_videos,
            COALESCE(vps.total_duration, rd.video_total_duration, 0)           AS video_total_duration,
            COALESCE(vps.total_watched_time, rd.video_total_watched_time, 0)   AS video_total_watched_time,
            CASE
                WHEN COALESCE(vps.total_videos, 0) > 0
                THEN ROUND(vps.completed_videos * 100.0 / vps.total_videos, 2)
                WHEN rd.video_completion_rate IS NOT NULL THEN rd.video_completion_rate
                ELSE 0
            END AS video_completion_rate,
            CASE
                WHEN COALESCE(vps.total_duration, 0) > 0
                THEN ROUND(vps.total_watched_time * 100.0 / vps.total_duration, 2)
                WHEN rd.video_watch_rate IS NOT NULL THEN rd.video_watch_rate
                ELSE 0
            END AS video_watch_rate,

            -- ── Discussion từ mooc_discussions ───────────────────────
            COALESCE(md.threads_count, rd.discussion_threads_count, 0)           AS discussion_threads_count,
            COALESCE(md.comments_count, rd.discussion_comments_count, 0)         AS discussion_comments_count,
            COALESCE(md.total_interactions, rd.discussion_total_interactions, 0) AS discussion_total_interactions,
            COALESCE(md.questions_count, rd.discussion_questions_count, 0)       AS discussion_questions_count,
            COALESCE(md.total_upvotes, rd.discussion_total_upvotes, 0)           AS discussion_total_upvotes,

            -- ── Quiz attempts + H5P avg score ────────────────────────
            COALESCE(h5p_agg.completed_contents, rd.quiz_attempts, 0)  AS quiz_attempts,
            COALESCE(h5p_agg.avg_percentage, rd.h5p_avg_score, 0)      AS h5p_avg_score,
            CASE
                WHEN COALESCE(h5p_agg.total_contents, 0) > 0
                THEN ROUND(h5p_agg.completed_contents * 100.0 / h5p_agg.total_contents, 2)
                WHEN rd.quiz_completion_rate IS NOT NULL THEN rd.quiz_completion_rate
                ELSE 0
            END AS quiz_completion_rate,

            CONCAT('populate_', DATE_FORMAT(NOW(), '%Y%m%d_%H%i%s')) AS extraction_batch_id,
            NOW() AS updated_at

        FROM enrollments e

        -- MOOC Grades (trực tiếp, source of truth)
        LEFT JOIN mooc_grades mg
            ON e.user_id = mg.user_id AND e.course_id = mg.course_id

        -- MOOC Progress (trực tiếp, source of truth cho completion/last_activity)
        LEFT JOIN mooc_progress mp
            ON e.user_id = mp.user_id AND e.course_id = mp.course_id

        -- Dashboard summary (overall_completion)
        LEFT JOIN dashboard_summary ds
            ON e.user_id = ds.user_id AND e.course_id = ds.course_id

        -- Video progress summary (video features + overall_completion proxy)
        LEFT JOIN video_progress_summary vps
            ON e.user_id = vps.user_id AND e.course_id = vps.course_id

        -- MOOC Discussions
        LEFT JOIN mooc_discussions md
            ON e.user_id = md.user_id AND e.course_id = md.course_id

        -- H5P aggregate
        LEFT JOIN (
            SELECT
                user_id,
                course_id,
                COUNT(DISTINCT content_id)                                              AS total_contents,
                COUNT(DISTINCT CASE WHEN percentage >= 70 THEN content_id END)          AS completed_contents,
                SUM(score)                                                              AS total_score,
                SUM(max_score)                                                          AS total_max_score,
                AVG(CASE WHEN finished > 0 THEN percentage ELSE NULL END)               AS avg_percentage,
                SUM(time_spent)                                                         AS total_time_spent
            FROM h5p_scores
            GROUP BY user_id, course_id
        ) h5p_agg
            ON e.user_id = h5p_agg.user_id AND e.course_id = h5p_agg.course_id

        -- raw_data làm fallback cuối cùng
        LEFT JOIN raw_data rd
            ON e.user_id = rd.user_id AND e.course_id = rd.course_id

        WHERE 1=1 {course_filter}

        ON DUPLICATE KEY UPDATE
            mooc_grade_percentage       = VALUES(mooc_grade_percentage),
            mooc_letter_grade           = VALUES(mooc_letter_grade),
            mooc_is_passed              = VALUES(mooc_is_passed),
            mooc_completion_rate        = VALUES(mooc_completion_rate),
            overall_completion          = VALUES(overall_completion),
            days_since_last_activity    = VALUES(days_since_last_activity),
            h5p_total_contents          = VALUES(h5p_total_contents),
            h5p_completed_contents      = VALUES(h5p_completed_contents),
            h5p_total_score             = VALUES(h5p_total_score),
            h5p_total_max_score         = VALUES(h5p_total_max_score),
            h5p_overall_percentage      = VALUES(h5p_overall_percentage),
            h5p_total_time_spent        = VALUES(h5p_total_time_spent),
            h5p_completion_rate         = VALUES(h5p_completion_rate),
            video_total_videos          = VALUES(video_total_videos),
            video_completed_videos      = VALUES(video_completed_videos),
            video_total_duration        = VALUES(video_total_duration),
            video_total_watched_time    = VALUES(video_total_watched_time),
            video_completion_rate       = VALUES(video_completion_rate),
            video_watch_rate            = VALUES(video_watch_rate),
            discussion_threads_count    = VALUES(discussion_threads_count),
            discussion_comments_count   = VALUES(discussion_comments_count),
            discussion_total_interactions = VALUES(discussion_total_interactions),
            discussion_questions_count  = VALUES(discussion_questions_count),
            discussion_total_upvotes    = VALUES(discussion_total_upvotes),
            quiz_attempts               = VALUES(quiz_attempts),
            h5p_avg_score               = VALUES(h5p_avg_score),
            quiz_completion_rate        = VALUES(quiz_completion_rate),
            weeks_since_enrollment      = VALUES(weeks_since_enrollment),
            updated_at                  = NOW()
        """

        cursor.execute(query, params)
        conn.commit()

        affected = cursor.rowcount
        print(f"   ✅ Populated/Updated {affected} records in student_features")

        # Verify
        if course_id:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN mooc_grade_percentage > 0 THEN 1 END) as with_grade,
                    COUNT(CASE WHEN mooc_completion_rate > 0 THEN 1 END) as with_completion,
                    COUNT(CASE WHEN days_since_last_activity < 999 THEN 1 END) as with_activity,
                    AVG(mooc_grade_percentage) as avg_grade,
                    AVG(mooc_completion_rate) as avg_completion
                FROM student_features
                WHERE course_id = %s
            """, (course_id,))

            result = cursor.fetchone()
            print(f"\n📊 Verification for {course_id}:")
            print(f"   - Total students      : {result[0]}")
            print(f"   - With grade > 0      : {result[1]}")
            print(f"   - With completion > 0 : {result[2]}")
            print(f"   - With activity < 999 : {result[3]}")
            if result[4] is not None:
                print(f"   - Avg grade           : {result[4]:.2f}%")
            if result[5] is not None:
                print(f"   - Avg completion      : {result[5]:.2f}%")

        print("\n✅ HOÀN THÀNH!")
        print("=" * 80)

        return affected

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Populate student_features')
    parser.add_argument('--course-id', type=str, help='Course ID (optional, populate all if not provided)')
    args = parser.parse_args()

    populate_student_features(args.course_id)
