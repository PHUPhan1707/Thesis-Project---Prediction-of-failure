"""
Email Notification Service cho MLOps Scheduler.
Gửi email thông báo khi auto-train, retrain, hoặc predict hoàn thành.
"""
import os
import ssl
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


def _get_smtp_config() -> Dict[str, str]:
    """Lấy SMTP config từ environment variables."""
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "admin_email": os.getenv("ADMIN_EMAIL", "phanan.phu17@gmail.com"),
    }


def _send_email(subject: str, html_body: str, recipients: List[str]) -> bool:
    """
    Gửi email qua Gmail SMTP.

    Args:
        subject:    Tiêu đề email
        html_body:  Nội dung HTML
        recipients: Danh sách email nhận

    Returns:
        True nếu gửi thành công
    """
    config = _get_smtp_config()
    if not config["user"] or not config["password"]:
        logger.warning(
            "SMTP credentials chưa cấu hình (SMTP_USER / SMTP_PASSWORD). "
            "Bỏ qua gửi email."
        )
        return False

    if not recipients:
        logger.warning("Không có recipients — bỏ qua gửi email.")
        return False

    # Loại bỏ None và empty strings
    recipients = [r for r in recipients if r and r.strip()]
    if not recipients:
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config["user"]
        msg["To"] = ", ".join(recipients)

        msg.attach(MIMEText(html_body, "html", "utf-8"))

        context = ssl.create_default_context()
        with smtplib.SMTP(config["host"], config["port"]) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(config["user"], config["password"])
            server.sendmail(config["user"], recipients, msg.as_string())

        logger.info(f"✅ Email sent to {recipients}: {subject}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return False


def send_training_notification(
    base_name: str,
    model_name: str,
    action: str,
    metrics: Dict,
    student_count: int,
    recipients: Optional[List[str]] = None,
) -> bool:
    """
    Gửi email khi auto-train hoặc retrain hoàn thành.

    Args:
        base_name:     Tên môn (VD: "Kinh tế vĩ mô")
        model_name:    Tên model
        action:        "initial_train" hoặc "retrain"
        metrics:       Dict metrics (accuracy, f1, auc)
        student_count: Số SV dùng để train
        recipients:    Danh sách email (admin + teacher)
    """
    config = _get_smtp_config()
    if recipients is None:
        recipients = [config["admin_email"]]

    action_vn = "Training lần đầu" if action == "initial_train" else "Retrain"

    subject = f"[MLOps] {action_vn} hoàn thành — {base_name}"

    accuracy = metrics.get("accuracy", 0) * 100
    f1 = metrics.get("f1_score", 0) * 100
    auc = metrics.get("auc_roc", 0) * 100

    html_body = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 24px; border-radius: 12px 12px 0 0;">
            <h2 style="margin: 0;">🤖 MLOps Scheduler</h2>
            <p style="margin: 8px 0 0; opacity: 0.9;">{action_vn} hoàn thành</p>
        </div>

        <div style="background: #f8f9fa; padding: 24px; border: 1px solid #e9ecef;">
            <h3 style="color: #333; margin-top: 0;">📚 {base_name}</h3>

            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        <strong>Model</strong></td>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        {model_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        <strong>Số sinh viên</strong></td>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        {student_count:,}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        <strong>Accuracy</strong></td>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        {accuracy:.1f}%</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        <strong>F1 Score</strong></td>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        {f1:.1f}%</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        <strong>AUC-ROC</strong></td>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        {auc:.1f}%</td>
                </tr>
            </table>
        </div>

        <div style="background: #fff; padding: 16px 24px; border: 1px solid #e9ecef;
                    border-top: none; border-radius: 0 0 12px 12px; color: #6c757d;
                    font-size: 13px;">
            Model đã được tự động gán cho tất cả khóa học trong nhóm này.
            Truy cập dashboard để xem chi tiết.
        </div>
    </div>
    """

    return _send_email(subject, html_body, recipients)


def send_prediction_notification(
    base_name: str,
    predicted_count: int,
    avg_risk: float,
    high_risk_count: int,
    recipients: Optional[List[str]] = None,
) -> bool:
    """
    Gửi email khi auto-predict hoàn thành.
    """
    config = _get_smtp_config()
    if recipients is None:
        recipients = [config["admin_email"]]

    subject = f"[MLOps] Predict hoàn thành — {base_name} ({predicted_count} SV)"

    html_body = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                    color: white; padding: 24px; border-radius: 12px 12px 0 0;">
            <h2 style="margin: 0;">📊 Kết Quả Dự Đoán</h2>
            <p style="margin: 8px 0 0; opacity: 0.9;">{base_name}</p>
        </div>

        <div style="background: #f8f9fa; padding: 24px; border: 1px solid #e9ecef;">
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        <strong>Tổng SV dự đoán</strong></td>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        {predicted_count:,}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        <strong>Risk trung bình</strong></td>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">
                        {avg_risk:.1f}%</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;
                            color: #dc3545;">
                        <strong>🚨 SV nguy cơ cao</strong></td>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;
                            color: #dc3545; font-weight: bold;">
                        {high_risk_count}</td>
                </tr>
            </table>
        </div>

        <div style="background: #fff; padding: 16px 24px; border: 1px solid #e9ecef;
                    border-top: none; border-radius: 0 0 12px 12px; color: #6c757d;
                    font-size: 13px;">
            Kết quả đã được cập nhật lên dashboard.
            Truy cập hệ thống để xem chi tiết từng sinh viên.
        </div>
    </div>
    """

    return _send_email(subject, html_body, recipients)


def send_test_email(recipient: Optional[str] = None) -> bool:
    """Gửi email test để kiểm tra cấu hình SMTP."""
    config = _get_smtp_config()
    to = recipient or config["admin_email"]
    return _send_email(
        subject="[MLOps] Test Email — Cấu hình thành công ✅",
        html_body="""
        <div style="font-family: Arial, sans-serif; padding: 24px;">
            <h2>✅ Email notification hoạt động!</h2>
            <p>Scheduler sẽ gửi email thông báo mỗi khi train/retrain/predict hoàn thành.</p>
        </div>
        """,
        recipients=[to],
    )
