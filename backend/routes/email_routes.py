"""
Email routes - Gửi email nhắc nhở hàng loạt cho sinh viên
"""
import logging
import threading
from flask import Blueprint, jsonify, request
from ..db import fetch_all
from ..email_notifier import _send_email, _get_smtp_config

logger = logging.getLogger(__name__)

email_bp = Blueprint('email', __name__, url_prefix='/api/email')


def _build_student_email(student: dict, course_name: str, custom_message: str) -> str:
    name = student.get('full_name') or student.get('email', 'Sinh viên')
    risk_level_map = {'HIGH': 'Cao', 'MEDIUM': 'Trung bình', 'LOW': 'Thấp'}
    risk_vn = risk_level_map.get(student.get('risk_level', 'MEDIUM'), 'Trung bình')
    risk_color = {'HIGH': '#dc3545', 'MEDIUM': '#fd7e14', 'LOW': '#28a745'}.get(
        student.get('risk_level', 'MEDIUM'), '#fd7e14'
    )
    days_inactive = int(student.get('days_since_last_activity') or 0)
    quiz_score = float(student.get('h5p_avg_score') or 0)
    completion = float(student.get('mooc_completion_rate') or 0)

    personalized_msg = custom_message.replace('{name}', name).replace('{course}', course_name)

    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;
                border:1px solid #e9ecef;border-radius:12px;overflow:hidden;">

        <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                    color:white;padding:28px 32px;">
            <h2 style="margin:0;font-size:1.4rem;">Thông báo học tập</h2>
            <p style="margin:6px 0 0;opacity:0.85;font-size:0.95rem;">{course_name}</p>
        </div>

        <div style="padding:28px 32px;background:#fff;">
            <p style="font-size:1rem;color:#333;">Xin chào <strong>{name}</strong>,</p>

            <p style="color:#555;line-height:1.7;">{personalized_msg}</p>

            <div style="background:#f8f9fa;border-radius:8px;padding:16px;margin:20px 0;">
                <p style="margin:0 0 12px;font-weight:600;color:#333;">Tình trạng học tập của bạn:</p>
                <table style="width:100%;border-collapse:collapse;">
                    <tr>
                        <td style="padding:6px 0;color:#666;">Mức độ rủi ro:</td>
                        <td style="padding:6px 0;font-weight:600;color:{risk_color};">{risk_vn}</td>
                    </tr>
                    <tr>
                        <td style="padding:6px 0;color:#666;">Điểm quiz trung bình:</td>
                        <td style="padding:6px 0;font-weight:600;color:#333;">{quiz_score:.1f}%</td>
                    </tr>
                    <tr>
                        <td style="padding:6px 0;color:#666;">Tiến độ hoàn thành:</td>
                        <td style="padding:6px 0;font-weight:600;color:#333;">{completion:.1f}%</td>
                    </tr>
                    <tr>
                        <td style="padding:6px 0;color:#666;">Ngày chưa hoạt động:</td>
                        <td style="padding:6px 0;font-weight:600;
                                   color:{'#dc3545' if days_inactive > 14 else '#333'};">
                            {days_inactive} ngày
                        </td>
                    </tr>
                </table>
            </div>

            <p style="color:#555;line-height:1.7;">
                Nếu bạn gặp khó khăn trong học tập, hãy liên hệ với giảng viên để được hỗ trợ kịp thời.
            </p>
        </div>

        <div style="background:#f8f9fa;padding:16px 32px;border-top:1px solid #e9ecef;
                    color:#999;font-size:12px;text-align:center;">
            Email này được gửi tự động từ hệ thống Teacher Dashboard.
        </div>
    </div>
    """


@email_bp.post('/send-bulk/<path:course_id>')
def send_bulk_email(course_id: str):
    """
    Gửi email nhắc nhở hàng loạt cho sinh viên của một khóa học.

    Body JSON:
        target:  "HIGH" | "HIGH_MEDIUM" | "ALL"   (mặc định: HIGH)
        subject: Tiêu đề email
        message: Nội dung tùy chỉnh (hỗ trợ {name}, {course})
    """
    data = request.get_json() or {}
    target = data.get('target', 'HIGH')
    subject = data.get('subject', 'Nhắc nhở học tập - Hãy tiếp tục cố gắng!')
    message = data.get('message',
        'Chúng tôi nhận thấy bạn chưa hoạt động gần đây trên khóa học. '
        'Hãy đăng nhập và tiếp tục học để không bỏ lỡ nội dung quan trọng nhé!'
    )

    # Build risk filter
    if target == 'HIGH':
        risk_filter = "AND p.risk_level = 'HIGH'"
    elif target == 'HIGH_MEDIUM':
        risk_filter = "AND p.risk_level IN ('HIGH', 'MEDIUM')"
    else:
        risk_filter = ""

    try:
        students = fetch_all(
            f"""
            SELECT
                f.user_id,
                COALESCE(NULLIF(e.email,''), g.email) AS email,
                COALESCE(NULLIF(e.full_name_vn,''), NULLIF(e.full_name,''), g.full_name) AS full_name,
                p.risk_level,
                f.days_since_last_activity,
                f.h5p_avg_score,
                f.mooc_completion_rate,
                e.course_name
            FROM student_features f
            LEFT JOIN enrollments e ON f.user_id = e.user_id AND f.course_id = e.course_id
            LEFT JOIN mooc_grades g ON f.user_id = g.user_id AND f.course_id = g.course_id
            LEFT JOIN predictions p ON f.user_id = p.user_id AND f.course_id = p.course_id
                      AND p.is_latest = TRUE
            WHERE f.course_id = %s
              AND COALESCE(NULLIF(e.email,''), g.email) IS NOT NULL
              AND f.mooc_is_passed IS NOT TRUE
              {risk_filter}
            ORDER BY p.risk_level DESC, f.days_since_last_activity DESC
            """,
            (course_id,)
        )
    except Exception as e:
        logger.error(f"DB error fetching students for bulk email: {e}")
        return jsonify({"error": "Database error"}), 500

    if not students:
        return jsonify({"success": True, "sent": 0, "failed": 0, "message": "Không có sinh viên phù hợp"}), 200

    course_name = students[0].get('course_name') or course_id
    smtp_config = _get_smtp_config()
    if not smtp_config['user'] or not smtp_config['password']:
        return jsonify({"error": "SMTP chưa được cấu hình. Vui lòng thêm SMTP_USER và SMTP_PASSWORD vào .env"}), 400

    # Send emails in background thread to avoid blocking
    results = {"sent": 0, "failed": 0, "failed_emails": []}

    def _send_all():
        for student in students:
            email = student.get('email')
            if not email:
                results['failed'] += 1
                continue
            html = _build_student_email(student, course_name, message)
            ok = _send_email(subject, html, [email])
            if ok:
                results['sent'] += 1
            else:
                results['failed'] += 1
                results['failed_emails'].append(email)

    thread = threading.Thread(target=_send_all, daemon=True)
    thread.start()
    thread.join(timeout=60)  # Wait max 60s

    logger.info(f"Bulk email: {results['sent']} sent, {results['failed']} failed for course {course_id}")

    return jsonify({
        "success": True,
        "sent": results['sent'],
        "failed": results['failed'],
        "failed_emails": results['failed_emails'][:5],  # return max 5 failed for display
        "total": len(students),
    })


@email_bp.get('/preview/<path:course_id>')
def preview_recipients(course_id: str):
    """Xem trước danh sách người nhận theo target."""
    target = request.args.get('target', 'HIGH')

    if target == 'HIGH':
        risk_filter = "AND p.risk_level = 'HIGH'"
    elif target == 'HIGH_MEDIUM':
        risk_filter = "AND p.risk_level IN ('HIGH', 'MEDIUM')"
    else:
        risk_filter = ""

    try:
        rows = fetch_all(
            f"""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN COALESCE(NULLIF(e.email,''), g.email) IS NOT NULL THEN 1 ELSE 0 END) as has_email
            FROM student_features f
            LEFT JOIN enrollments e ON f.user_id = e.user_id AND f.course_id = e.course_id
            LEFT JOIN mooc_grades g ON f.user_id = g.user_id AND f.course_id = g.course_id
            LEFT JOIN predictions p ON f.user_id = p.user_id AND f.course_id = p.course_id
                      AND p.is_latest = TRUE
            WHERE f.course_id = %s
              AND f.mooc_is_passed IS NOT TRUE
              {risk_filter}
            """,
            (course_id,)
        )
        d = dict(rows[0]) if rows else {}
        return jsonify({"total": int(d.get('total') or 0), "has_email": int(d.get('has_email') or 0)})
    except Exception as e:
        logger.error(f"Preview error: {e}")
        return jsonify({"error": "Database error"}), 500


@email_bp.get('/recipients/<path:course_id>')
def get_recipients(course_id: str):
    """Lấy danh sách email sinh viên theo target để mở mailto."""
    target = request.args.get('target', 'HIGH')

    if target == 'HIGH':
        risk_filter = "AND p.risk_level = 'HIGH'"
    elif target == 'HIGH_MEDIUM':
        risk_filter = "AND p.risk_level IN ('HIGH', 'MEDIUM')"
    else:
        risk_filter = ""

    try:
        rows = fetch_all(
            f"""
            SELECT
                COALESCE(NULLIF(e.email,''), g.email) AS email,
                COALESCE(NULLIF(e.full_name_vn,''), NULLIF(e.full_name,''), g.full_name) AS full_name,
                p.risk_level,
                f.days_since_last_activity,
                f.h5p_avg_score,
                f.mooc_completion_rate
            FROM student_features f
            LEFT JOIN enrollments e ON f.user_id = e.user_id AND f.course_id = e.course_id
            LEFT JOIN mooc_grades g ON f.user_id = g.user_id AND f.course_id = g.course_id
            LEFT JOIN predictions p ON f.user_id = p.user_id AND f.course_id = p.course_id
                      AND p.is_latest = TRUE
            WHERE f.course_id = %s
              AND COALESCE(NULLIF(e.email,''), g.email) IS NOT NULL
              AND f.mooc_is_passed IS NOT TRUE
              {risk_filter}
            ORDER BY p.risk_level DESC, f.days_since_last_activity DESC
            """,
            (course_id,)
        )
        emails = [r['email'] for r in rows if r.get('email')]
        return jsonify({"emails": emails, "total": len(emails)})
    except Exception as e:
        logger.error(f"Get recipients error: {e}")
        return jsonify({"error": "Database error"}), 500
