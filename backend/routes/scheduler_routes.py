"""
Scheduler API Routes — xem lịch sử, trigger thủ công, xem trạng thái.
"""
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

scheduler_bp = Blueprint("scheduler", __name__, url_prefix="/api/scheduler")


@scheduler_bp.get("/status")
def get_scheduler_status():
    """
    Trạng thái mỗi nhóm môn học: waiting / active / no_data.
    """
    try:
        from ..db import discover_course_groups, fetch_all
        import os

        min_students = int(os.getenv("MIN_STUDENTS_FOR_TRAINING", "500"))
        retrain_threshold = int(os.getenv("RETRAIN_THRESHOLD", "100"))

        groups = discover_course_groups()
        statuses = []

        # -- Bulk Queries for Performance --
        # 1. Labeled students per course
        labeled_rows = fetch_all("SELECT course_id, COUNT(*) as labeled FROM mooc_grades WHERE is_passed IS NOT NULL GROUP BY course_id")
        labeled_map = {r['course_id']: r['labeled'] for r in labeled_rows}

        # 2. Model mapping per course
        model_rows = fetch_all("SELECT course_id, model_name FROM course_model_mapping WHERE is_active = TRUE")
        model_map = {r['course_id']: r['model_name'] for r in model_rows}

        # 3. Last training records per base_name
        history_rows = fetch_all("""
            SELECT base_name, completed_at, labeled_student_count 
            FROM training_history 
            WHERE action IN ('initial_train', 'retrain') AND status = 'success'
            ORDER BY completed_at DESC
        """)
        last_record_map = {}
        for r in history_rows:
            bn = r['base_name']
            if bn not in last_record_map:
                last_record_map[bn] = r

        for base_name, course_ids in groups.items():
            labeled = sum(labeled_map.get(cid, 0) for cid in course_ids)
            model_name = next((model_map[cid] for cid in course_ids if cid in model_map), None)
            last_record = last_record_map.get(base_name)

            if model_name:
                last_trained = (
                    last_record.get("labeled_student_count", 0)
                    if last_record
                    else 0
                )
                new_since_train = labeled - last_trained
                status = "active"
            else:
                new_since_train = 0
                status = "waiting" if labeled > 0 else "no_data"

            statuses.append({
                "base_name": base_name,
                "status": status,
                "course_count": len(course_ids),
                "course_ids": course_ids,
                "labeled_students": labeled,
                "min_required": min_students,
                "model_name": model_name,
                "new_since_last_train": max(0, new_since_train),
                "retrain_threshold": retrain_threshold,
                "last_train_at": (
                    last_record.get("completed_at").isoformat()
                    if last_record and last_record.get("completed_at")
                    else None
                ),
            })

        return jsonify({
            "scheduler_enabled": os.getenv("SCHEDULER_ENABLED", "false").lower() == "true",
            "interval_days": int(os.getenv("SCHEDULER_INTERVAL_DAYS", "30")),
            "groups": statuses,
            "total_groups": len(statuses),
        })

    except Exception:
        logger.exception("Error getting scheduler status")
        return jsonify({"error": "Failed to get scheduler status"}), 500


@scheduler_bp.get("/history")
def get_scheduler_history():
    """
    Lịch sử tất cả runs — filter bằng ?base_name=... nếu cần.
    """
    try:
        from ..db import get_training_history

        base_name = request.args.get("base_name")
        limit = int(request.args.get("limit", "50"))

        records = get_training_history(base_name=base_name, limit=limit)

        # Serialize datetime objects
        for r in records:
            for key in ("started_at", "completed_at"):
                val = r.get(key)
                if val and hasattr(val, "isoformat"):
                    r[key] = val.isoformat()

        return jsonify({
            "history": records,
            "total": len(records),
            "filter": {"base_name": base_name} if base_name else None,
        })

    except Exception:
        logger.exception("Error getting scheduler history")
        return jsonify({"error": "Failed to get scheduler history"}), 500


@scheduler_bp.post("/trigger")
def trigger_scheduler():
    """
    Trigger thủ công — chạy kiểm tra ngay lập tức.

    Body (optional):
        {"dry_run": true}   → chỉ log, không train/predict thật
    """
    try:
        from ..scheduler import CourseLifecycleManager

        data = request.get_json(silent=True) or {}
        dry_run = data.get("dry_run", False)

        logger.info(f"🔧 Manual trigger! dry_run={dry_run}")

        manager = CourseLifecycleManager()
        manager.check_and_process_all(dry_run=dry_run)

        return jsonify({
            "success": True,
            "message": "Scheduler triggered successfully",
            "dry_run": dry_run,
            "triggered_at": datetime.now().isoformat(),
        })

    except Exception:
        logger.exception("Error triggering scheduler")
        return jsonify({"error": "Trigger failed"}), 500


@scheduler_bp.post("/assign-model")
def assign_model():
    """
    Gán model từ một course cho course khác.

    Body:
        {
            "source_course": "course-v1:...",
            "target_course": "course-v1:..."
        }
    """
    try:
        from ..db import get_course_model_mapping, register_model_for_courses

        data = request.get_json(silent=True) or {}
        source = data.get("source_course")
        target = data.get("target_course")

        if not source or not target:
            return jsonify({
                "error": "Cần source_course và target_course"
            }), 400

        # Lấy model của source
        model_info = get_course_model_mapping(source)
        if not model_info:
            return jsonify({
                "error": f"Không tìm thấy model cho course {source}"
            }), 404

        # Gán cho target
        success = register_model_for_courses(
            model_name=model_info["model_name"],
            model_version=model_info.get("model_version", "v1.0.0"),
            model_path=model_info["model_path"],
            features_csv_path=model_info.get("features_csv_path", ""),
            course_ids=[target],
        )

        if success:
            return jsonify({
                "success": True,
                "message": f"Model {model_info['model_name']} đã gán cho {target}",
                "model_name": model_info["model_name"],
                "source_course": source,
                "target_course": target,
            })
        else:
            return jsonify({"error": "Lỗi khi gán model"}), 500

    except Exception:
        logger.exception("Error assigning model")
        return jsonify({"error": "Assign model failed"}), 500
