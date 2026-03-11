"""
MLOps Background Scheduler Service.

Chạy mỗi 30 ngày, tự động:
1. Discover nhóm khóa học theo tên (base_name)
2. Check số SV có is_passed — nếu ≥500 → auto-train model
3. Predict cho SV mới — nếu thêm ≥100 labeled SV → retrain

Dùng APScheduler tích hợp trong Flask app.
"""
import os
import sys
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Đảm bảo project root trong sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class CourseLifecycleManager:
    """
    State machine quản lý vòng đời ML cho mỗi nhóm khóa học:

        WAITING_FOR_DATA  →  đếm labeled SV, chờ ≥ threshold
        INITIAL_TRAINING  →  gom data, train CatBoost, register model
        ACTIVE_PREDICTING →  predict cho SV mới, check retrain
    """

    def __init__(self):
        self.min_students = int(os.getenv("MIN_STUDENTS_FOR_TRAINING", "500"))
        self.retrain_threshold = int(os.getenv("RETRAIN_THRESHOLD", "100"))
        self._lock = threading.Lock()

    # ── Public entry point ──────────────────────────────────────

    def check_and_process_all(self, dry_run: bool = False):
        """
        Entry point — gọi mỗi 30 ngày (hoặc trigger thủ công).

        Args:
            dry_run: Nếu True, chỉ log actions mà không train/predict thật.
        """
        with self._lock:
            self._run(dry_run=dry_run)

    # ── Private implementation ──────────────────────────────────

    def _run(self, dry_run: bool = False):
        from backend.db import (
            discover_course_groups,
            count_labeled_students,
            get_model_for_courses,
            get_last_training_record,
            save_training_record,
        )

        logger.info("=" * 70)
        logger.info("🤖 MLOps Scheduler — bắt đầu chu kỳ kiểm tra")
        logger.info("=" * 70)

        groups = discover_course_groups()
        if not groups:
            logger.warning("Không tìm thấy khóa học nào trong enrollments.")
            return

        logger.info(f"Phát hiện {len(groups)} nhóm môn học:")
        for name, cids in groups.items():
            logger.info(f"  • {name}: {len(cids)} course(s)")

        for base_name, course_ids in groups.items():
            logger.info("-" * 60)
            logger.info(f"📚 Xử lý nhóm: {base_name}")
            try:
                model_info = get_model_for_courses(course_ids)

                if model_info is None:
                    # ── WAITING_FOR_DATA → có thể chuyển INITIAL_TRAINING
                    self._handle_no_model(
                        base_name, course_ids, dry_run=dry_run
                    )
                else:
                    # ── ACTIVE_PREDICTING → predict + check retrain
                    self._handle_has_model(
                        base_name, course_ids, model_info, dry_run=dry_run
                    )

            except Exception:
                logger.exception(f"Lỗi khi xử lý nhóm {base_name}")
                started = datetime.now().isoformat()
                save_training_record(
                    base_name=base_name,
                    course_ids=course_ids,
                    model_name=None,
                    action="check",
                    status="failed",
                    message=f"Exception khi xử lý",
                    started_at=started,
                    completed_at=datetime.now().isoformat(),
                )

        logger.info("=" * 70)
        logger.info("✅ MLOps Scheduler — hoàn thành chu kỳ")
        logger.info("=" * 70)

    # ── Trạng thái 1: Chưa có model ────────────────────────────

    def _handle_no_model(self, base_name, course_ids, dry_run=False):
        from backend.db import (
            count_labeled_students,
            save_training_record,
            register_model_for_courses,
        )
        from backend.email_notifier import send_training_notification

        labeled = count_labeled_students(course_ids)
        logger.info(
            f"  Chưa có model. Labeled students: {labeled}/{self.min_students}"
        )

        started = datetime.now().isoformat()

        if labeled < self.min_students:
            logger.info(f"  ⏭ Chưa đủ data — skip (cần thêm {self.min_students - labeled} SV)")
            save_training_record(
                base_name=base_name,
                course_ids=course_ids,
                model_name=None,
                action="check",
                labeled_student_count=labeled,
                status="skipped",
                message=f"Chưa đủ threshold: {labeled}/{self.min_students}",
                started_at=started,
                completed_at=datetime.now().isoformat(),
            )
            return

        # ── Đủ data → INITIAL TRAINING ──
        logger.info(f"  ✅ Đủ {labeled} labeled students — bắt đầu INITIAL TRAINING")

        if dry_run:
            logger.info("  [DRY RUN] Sẽ train model nhưng bỏ qua vì dry_run=True")
            save_training_record(
                base_name=base_name,
                course_ids=course_ids,
                model_name=None,
                action="initial_train",
                labeled_student_count=labeled,
                status="skipped",
                message="Dry run — không train thật",
                started_at=started,
                completed_at=datetime.now().isoformat(),
            )
            return

        # Train thật
        from ml.train_model import train_for_courses

        result = train_for_courses(base_name, course_ids)

        if result is None:
            logger.error(f"  ❌ Training thất bại cho {base_name}")
            save_training_record(
                base_name=base_name,
                course_ids=course_ids,
                model_name=None,
                action="initial_train",
                labeled_student_count=labeled,
                status="failed",
                message="train_for_courses returned None",
                started_at=started,
                completed_at=datetime.now().isoformat(),
            )
            return

        # Register model cho tất cả courses
        register_model_for_courses(
            model_name=result["model_name"],
            model_version=result["model_version"],
            model_path=result["model_path"],
            features_csv_path=result["features_csv_path"],
            course_ids=course_ids,
        )

        save_training_record(
            base_name=base_name,
            course_ids=course_ids,
            model_name=result["model_name"],
            action="initial_train",
            labeled_student_count=result["student_count"],
            accuracy=result["accuracy"],
            f1_score=result["f1_score"],
            auc_roc=result["auc_roc"],
            status="success",
            message=f"Model {result['model_name']} trained successfully",
            started_at=started,
            completed_at=datetime.now().isoformat(),
        )

        # Email notification
        admin_email = os.getenv("ADMIN_EMAIL", "phanan.phu17@gmail.com")
        send_training_notification(
            base_name=base_name,
            model_name=result["model_name"],
            action="initial_train",
            metrics=result,
            student_count=result["student_count"],
            recipients=[admin_email],
        )

        logger.info(f"  🎉 INITIAL TRAINING hoàn thành: {result['model_name']}")

    # ── Trạng thái 2: Đã có model → predict + check retrain ───

    def _handle_has_model(self, base_name, course_ids, model_info, dry_run=False):
        from backend.db import (
            count_labeled_students,
            get_last_training_record,
            save_training_record,
            register_model_for_courses,
        )
        from backend.email_notifier import (
            send_prediction_notification,
            send_training_notification,
        )

        model_name = model_info["model_name"]
        logger.info(f"  Đã có model: {model_name}")

        started = datetime.now().isoformat()

        # ── A: Predict ──
        predicted_count = 0
        avg_risk = 0.0
        high_risk_count = 0

        if not dry_run:
            try:
                from backend.inference_service import InferenceService

                service = InferenceService(
                    model_path=model_info.get("model_path"),
                    features_csv=model_info.get("features_csv_path"),
                )

                for cid in course_ids:
                    logger.info(f"  🤖 Predicting course: {cid}")
                    result_df = service.predict_course(cid, save_db=True)
                    if result_df is not None and not result_df.empty:
                        predicted_count += len(result_df)
                        avg_risk += float(result_df["fail_risk_score"].sum())
                        high_risk_count += int(
                            (result_df["fail_risk_score"] >= 70).sum()
                        )

                if predicted_count > 0:
                    avg_risk = avg_risk / predicted_count

                logger.info(
                    f"  📊 Predicted {predicted_count} students, "
                    f"avg risk {avg_risk:.1f}%, high risk {high_risk_count}"
                )

                save_training_record(
                    base_name=base_name,
                    course_ids=course_ids,
                    model_name=model_name,
                    action="predict",
                    predicted_student_count=predicted_count,
                    status="success",
                    message=f"Predicted {predicted_count} students, avg risk {avg_risk:.1f}%",
                    started_at=started,
                    completed_at=datetime.now().isoformat(),
                )

                # Email prediction results
                if predicted_count > 0:
                    admin_email = os.getenv("ADMIN_EMAIL", "phanan.phu17@gmail.com")
                    send_prediction_notification(
                        base_name=base_name,
                        predicted_count=predicted_count,
                        avg_risk=avg_risk,
                        high_risk_count=high_risk_count,
                        recipients=[admin_email],
                    )

            except Exception:
                logger.exception(f"  ❌ Prediction thất bại cho {base_name}")
                save_training_record(
                    base_name=base_name,
                    course_ids=course_ids,
                    model_name=model_name,
                    action="predict",
                    status="failed",
                    message="Prediction exception",
                    started_at=started,
                    completed_at=datetime.now().isoformat(),
                )
        else:
            logger.info("  [DRY RUN] Sẽ predict nhưng bỏ qua")

        # ── B: Check retrain ──
        labeled = count_labeled_students(course_ids)
        last_record = get_last_training_record(base_name)
        last_trained_count = (
            last_record.get("labeled_student_count", 0) if last_record else 0
        )
        new_students = labeled - last_trained_count

        logger.info(
            f"  Retrain check: labeled={labeled}, "
            f"last_trained={last_trained_count}, new={new_students}"
        )

        if new_students >= self.retrain_threshold:
            logger.info(f"  🔄 +{new_students} SV mới → RETRAIN")

            if dry_run:
                logger.info("  [DRY RUN] Sẽ retrain nhưng bỏ qua")
                return

            from ml.train_model import train_for_courses

            retrain_started = datetime.now().isoformat()
            result = train_for_courses(base_name, course_ids)

            if result:
                register_model_for_courses(
                    model_name=result["model_name"],
                    model_version=result["model_version"],
                    model_path=result["model_path"],
                    features_csv_path=result["features_csv_path"],
                    course_ids=course_ids,
                )

                save_training_record(
                    base_name=base_name,
                    course_ids=course_ids,
                    model_name=result["model_name"],
                    action="retrain",
                    labeled_student_count=result["student_count"],
                    accuracy=result["accuracy"],
                    f1_score=result["f1_score"],
                    auc_roc=result["auc_roc"],
                    status="success",
                    message=f"Retrained with {result['student_count']} students (+{new_students} new)",
                    started_at=retrain_started,
                    completed_at=datetime.now().isoformat(),
                )

                admin_email = os.getenv("ADMIN_EMAIL", "phanan.phu17@gmail.com")
                send_training_notification(
                    base_name=base_name,
                    model_name=result["model_name"],
                    action="retrain",
                    metrics=result,
                    student_count=result["student_count"],
                    recipients=[admin_email],
                )

                logger.info(f"  🎉 RETRAIN hoàn thành: {result['model_name']}")
            else:
                save_training_record(
                    base_name=base_name,
                    course_ids=course_ids,
                    model_name=model_name,
                    action="retrain",
                    labeled_student_count=labeled,
                    status="failed",
                    message="Retrain thất bại",
                    started_at=retrain_started,
                    completed_at=datetime.now().isoformat(),
                )
        else:
            logger.info(
                f"  ⏭ Chưa đủ threshold retrain "
                f"(cần +{self.retrain_threshold - new_students} SV nữa)"
            )


# ─────────────────────────────────────────────────────────────
# Scheduler Initialization
# ─────────────────────────────────────────────────────────────

_scheduler_instance = None


def init_scheduler(app):
    """
    Khởi tạo APScheduler trong Flask app.
    Chỉ start khi SCHEDULER_ENABLED=true trong .env.
    """
    global _scheduler_instance

    enabled = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"
    if not enabled:
        logger.info("📅 Scheduler DISABLED (set SCHEDULER_ENABLED=true để bật)")
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
    except ImportError:
        logger.error(
            "❌ APScheduler chưa cài! Chạy: pip install apscheduler"
        )
        return

    interval_days = int(os.getenv("SCHEDULER_INTERVAL_DAYS", "30"))

    manager = CourseLifecycleManager()

    def _scheduled_job():
        """Wrapper chạy trong Flask app context."""
        with app.app_context():
            logger.info("📅 Scheduler job triggered!")
            manager.check_and_process_all(dry_run=False)

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        _scheduled_job,
        trigger=IntervalTrigger(days=interval_days),
        id="mlops_lifecycle_check",
        name=f"MLOps Lifecycle Check (every {interval_days} days)",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler_instance = scheduler

    logger.info(f"📅 Scheduler STARTED — chạy mỗi {interval_days} ngày")
    logger.info(f"   Min students: {manager.min_students}")
    logger.info(f"   Retrain threshold: +{manager.retrain_threshold}")


def get_scheduler():
    """Trả về scheduler instance (dùng cho routes)."""
    return _scheduler_instance
