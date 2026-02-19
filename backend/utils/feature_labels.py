"""
Vietnamese labels for model features.
Maps technical feature names to human-readable Vietnamese descriptions.
"""

FEATURE_LABELS_VI: dict[str, str] = {
    # Activity / Engagement
    "days_since_last_activity": "Số ngày không hoạt động",
    "max_inactive_gap_days": "Khoảng nghỉ dài nhất (ngày)",
    "access_frequency": "Tần suất truy cập",
    "activity_recency": "Mức độ hoạt động gần đây",
    "activity_consistency": "Tính nhất quán hoạt động",
    "is_inactive": "Không hoạt động (>7 ngày)",
    "is_highly_inactive": "Không hoạt động (>14 ngày)",

    # Completion / Progress
    "mooc_completion_rate": "Tỷ lệ hoàn thành khóa học",
    "overall_completion": "Hoàn thành tổng thể",
    "completion_consistency": "Độ đồng đều hoàn thành",
    "relative_completion": "Hoàn thành so với lớp",
    "relative_to_course_completion": "Hoàn thành tương đối (lớp)",
    "progress_rate": "Tốc độ tiến độ",
    "progress_velocity": "Gia tốc tiến độ",
    "weeks_to_complete_estimate": "Số tuần dự kiến hoàn thành",
    "is_struggling": "Đang gặp khó khăn",
    "is_at_risk": "Có nguy cơ",

    # Video
    "video_completion_rate": "Tỷ lệ hoàn thành video",
    "video_total_duration": "Tổng thời gian xem video",
    "video_views": "Số lượt xem video",
    "video_total_videos": "Tổng số video đã xem",
    "video_engagement_rate": "Mức độ tương tác video",

    # Quiz / Problem
    "problem_avg_score": "Điểm trung bình bài tập",
    "quiz_attempts": "Số lần làm quiz",
    "quiz_avg_score": "Điểm trung bình quiz",
    "relative_to_course_problem_score": "Điểm bài tập so với lớp",

    # H5P
    "h5p_total_time_spent": "Thời gian làm H5P",
    "h5p_overall_percentage": "Tỷ lệ hoàn thành H5P",
    "h5p_completion_rate": "Tỷ lệ hoàn thành H5P",
    "h5p_engagement_rate": "Mức độ tương tác H5P",

    # Discussion
    "discussion_engagement_rate": "Mức độ tham gia thảo luận",
    "has_no_discussion": "Không tham gia thảo luận",
    "discussion_total_interactions": "Tổng tương tác thảo luận",

    # Grade
    "mooc_grade_percentage": "Điểm tổng kết (%)",

    # Time / Enrollment
    "enrollment_phase": "Giai đoạn đăng ký",
    "weeks_remaining": "Số tuần còn lại",
    "weeks_since_enrollment": "Số tuần đã học",

    # Composite scores
    "engagement_score": "Điểm tương tác tổng hợp",
    "interaction_score": "Điểm tương tác",
}


def get_vi_label(feature_name: str) -> str:
    """Return Vietnamese label for a feature, or the raw name if not mapped."""
    return FEATURE_LABELS_VI.get(feature_name, feature_name)
