"""
Pipeline Service — Full automated ML pipeline with SSE event streaming.

Quy trình:
  Step 1: Discover tất cả khóa học từ MOOC API
  Step 2: Fetch data (enrollments, grades, progress) cho mỗi course
  Step 3: Populate student_features (Feature Engineering)
  Step 4: Training model (cho nhóm course >= 500 SV đã hoàn thành)
  Step 5: Prediction (dùng model vừa train)

Mỗi bước phát ra SSE events để frontend hiển thị real-time.
"""
import os
import sys
import json
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class PipelineEvent:
    """Một SSE event được gửi tới frontend."""

    def __init__(
        self,
        event_type: str,
        data: dict,
    ):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now().isoformat()

    def to_sse(self) -> str:
        payload = {**self.data, "timestamp": self.timestamp}
        return f"event: {self.event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


class PipelineService:
    """
    Orchestrator chạy full ML pipeline trong background thread,
    phát events qua Queue cho SSE stream.
    """

    TOTAL_STEPS = 5
    STEP_NAMES = [
        "Discover khóa học",
        "Fetch dữ liệu từ MOOC",
        "Feature Engineering",
        "Training Model",
        "Prediction",
    ]

    def __init__(self, app=None):
        self._queue: Queue = Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._app = app
        self._should_stop = False
        self._summary: Optional[dict] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def summary(self) -> Optional[dict]:
        return self._summary

    def emit(self, event_type: str, **data):
        self._queue.put(PipelineEvent(event_type, data))

    def emit_log(self, message: str, level: str = "info"):
        self.emit("log", message=message, level=level)

    def emit_step(self, step: int, status: str, detail: str = ""):
        self.emit(
            "step_update",
            step=step,
            step_name=self.STEP_NAMES[step - 1] if 1 <= step <= 5 else "",
            status=status,
            detail=detail,
            total_steps=self.TOTAL_STEPS,
        )

    def emit_progress(self, step: int, current: int, total: int, label: str = ""):
        pct = round((current / total) * 100, 1) if total > 0 else 0
        self.emit(
            "progress",
            step=step,
            current=current,
            total=total,
            percent=pct,
            label=label,
        )

    def get_events(self):
        """Generator yields SSE events (blocking)."""
        while True:
            try:
                event = self._queue.get(timeout=30)
                yield event.to_sse()
                if event.event_type == "done":
                    break
            except Exception:
                yield f"event: heartbeat\ndata: {{}}\n\n"

    def start(self, session_id: str = ""):
        """Bắt đầu pipeline trong background thread."""
        if self._running:
            self.emit_log("Pipeline đang chạy, vui lòng đợi...", "warning")
            return False

        self._should_stop = False
        self._summary = None
        self._thread = threading.Thread(
            target=self._run_pipeline,
            args=(session_id,),
            daemon=True,
        )
        self._thread.start()
        return True

    def start_fetch_only(self, course_ids: list, session_id: str = ""):
        """Chỉ fetch data + feature engineering cho danh sách course_ids cụ thể."""
        if self._running:
            self.emit_log("Pipeline đang chạy, vui lòng đợi...", "warning")
            return False

        self._should_stop = False
        self._summary = None
        self._thread = threading.Thread(
            target=self._run_fetch_only,
            args=(course_ids, session_id),
            daemon=True,
        )
        self._thread.start()
        return True

    def stop(self):
        self._should_stop = True
        self.emit_log("Đang dừng pipeline...", "warning")

    def _check_stop(self):
        if self._should_stop:
            raise InterruptedError("Pipeline bị dừng bởi user")

    # ──────────────────────────────────────────────────────────
    #  MAIN PIPELINE
    # ──────────────────────────────────────────────────────────

    def _run_pipeline(self, session_id: str = ""):
        self._running = True
        started = datetime.now()

        self.emit("pipeline_start", message="Pipeline bắt đầu chạy")
        self.emit_log("=" * 50)
        self.emit_log("Pipeline ML tự động — bắt đầu")
        self.emit_log("=" * 50)

        summary = {
            "started_at": started.isoformat(),
            "courses_discovered": 0,
            "courses_fetched": 0,
            "students_featured": 0,
            "courses_trained": [],
            "courses_predicted": [],
            "errors": [],
        }

        try:
            # ── Step 1: Discover ──
            courses = self._step1_discover()
            summary["courses_discovered"] = len(courses)
            self._check_stop()

            if not courses:
                self.emit_log("Không tìm thấy khóa học nào. Dừng pipeline.", "error")
                self._finish(summary, started)
                return

            # ── Step 2: Fetch data ──
            fetched = self._step2_fetch(courses, session_id)
            summary["courses_fetched"] = fetched
            self._check_stop()

            # ── Step 3: Feature Engineering ──
            featured = self._step3_features(courses)
            summary["students_featured"] = featured
            self._check_stop()

            # ── Step 4: Training ──
            trained = self._step4_training()
            summary["courses_trained"] = trained
            self._check_stop()

            # ── Step 5: Prediction ──
            predicted = self._step5_prediction()
            summary["courses_predicted"] = predicted

        except InterruptedError:
            self.emit_log("Pipeline đã bị dừng.", "warning")
            summary["errors"].append("Stopped by user")
        except Exception as e:
            logger.exception("Pipeline error")
            self.emit_log(f"Lỗi nghiêm trọng: {e}", "error")
            summary["errors"].append(str(e))

        self._finish(summary, started)

    def _finish(self, summary: dict, started: datetime):
        elapsed = (datetime.now() - started).total_seconds()
        summary["elapsed_seconds"] = round(elapsed, 1)
        summary["completed_at"] = datetime.now().isoformat()
        self._summary = summary

        self.emit_log("=" * 50)
        self.emit_log(f"Pipeline hoàn thành trong {elapsed:.1f}s")
        self.emit_log(
            f"Kết quả: {summary['courses_discovered']} courses discovered, "
            f"{summary['courses_fetched']} fetched, "
            f"{len(summary['courses_trained'])} trained, "
            f"{len(summary['courses_predicted'])} predicted"
        )
        self.emit("done", summary=summary)
        self._running = False

    # ──────────────────────────────────────────────────────────
    #  STEP 1: DISCOVER
    # ──────────────────────────────────────────────────────────

    def _step1_discover(self) -> list:
        self.emit_step(1, "running", "Đang lấy danh sách khóa học từ MOOC...")
        self.emit_log("Bước 1: Discover khóa học từ MOOC API")

        try:
            from backend.mooc_auth_service import get_mooc_auth

            auth = get_mooc_auth()
            courses = auth.fetch_all_courses()

            if courses:
                self.emit_log(f"Tìm thấy {len(courses)} khóa học trên MOOC")
                for i, c in enumerate(courses[:10]):
                    name = c.get("display_name", c.get("id", "?"))
                    cid = c.get("id", "?")
                    self.emit_log(f"  {i+1}. {name} ({cid})")
                if len(courses) > 10:
                    self.emit_log(f"  ... và {len(courses) - 10} khóa học khác")
            else:
                self.emit_log("Không tìm thấy khóa học nào!", "warning")

            self.emit_step(1, "completed", f"{len(courses)} khóa học")
            return courses

        except Exception as e:
            self.emit_log(f"Lỗi discover: {e}", "error")
            self.emit_step(1, "error", str(e))
            return []

    # ──────────────────────────────────────────────────────────
    #  STEP 2: FETCH DATA
    # ──────────────────────────────────────────────────────────

    def _step2_fetch(self, courses: list, session_id: str = "") -> int:
        self.emit_step(2, "running", "Đang fetch dữ liệu từ MOOC...")
        self.emit_log("Bước 2: Fetch enrollments, grades, progress từ MOOC API")

        try:
            from backend.mooc_auth_service import get_mooc_auth
            from database.fetch_mooc_h5p_data import MOOCH5PDataFetcher

            auth = get_mooc_auth()

            if not auth.is_authenticated:
                self.emit_log("Đang login vào MOOC...", "info")
                success = auth.login()
                if success:
                    self.emit_log("Login MOOC thành công!", "info")
                else:
                    self.emit_log(
                        "Không thể login MOOC. Sẽ thử fetch với session hiện có.",
                        "warning",
                    )

            fetcher = MOOCH5PDataFetcher()
            if not fetcher.connect_db():
                self.emit_log("Không thể kết nối database!", "error")
                self.emit_step(2, "error", "DB connection failed")
                return 0

            # Nâng cấp: Truyền toàn bộ requests.Session đã được xác thực (chứa jwt, csrf, cookie) cho fetcher
            mooc_session_obj = auth.get_session() if auth.is_authenticated else None
            sid = auth._session_id if (auth._session_id and auth._session_id != "login_ok") else None

            # Ưu tiên session lấy được từ Auth, nếu không có mới dùng session_id truyền vô từ Manual Input
            if mooc_session_obj:
                fetcher.set_mooc_session(mooc_session_obj)
                self.emit_log(f"Đã mượn Session Object thành công: {sid[:8] if sid else 'N/A'}...")
            elif session_id:
                fetcher.set_mooc_session(session_id)
                self.emit_log(f"Đã sử dụng session cookie truyền thủ công: {session_id[:8]}...")
            else:
                self.emit_log("Không tìm thấy session cookie nào!", "warning")

            total = len(courses)
            fetched_count = 0

            for i, course in enumerate(courses):
                self._check_stop()
                course_id = course.get("id", "")
                course_name = course.get("display_name", course_id)

                self.emit_progress(2, i + 1, total, course_name)
                self.emit_log(f"[{i+1}/{total}] Fetching: {course_name}")

                try:
                    user_ids = fetcher.fetch_mooc_course_students(course_id)
                    enrollment_count = len(user_ids) if user_ids else 0
                    self.emit_log(f"  Enrollments: {enrollment_count}")

                    fetcher.fetch_and_update_course_info(course_id)

                    grades_data = fetcher.fetch_mooc_grades(course_id)
                    if grades_data:
                        fetcher.save_mooc_grades(course_id, grades_data)
                        self.emit_log(f"  Grades: {len(grades_data)} records")

                    progress_data = fetcher.fetch_mooc_progress(course_id)
                    if progress_data:
                        fetcher.save_mooc_progress(course_id, progress_data)
                        self.emit_log(
                            f"  Progress: {len(progress_data)} records"
                        )


                    # ── Fetch H5P & Video per student (CONCURRENT) ──
                    if user_ids:
                        self.emit_log(f"  Fetching H5P & Video for {len(user_ids)} students (concurrent)...")

                        def _progress_cb(done, total_sv, _course_name=course_name, _i=i, _total=total):
                            if done % 20 == 0 or done == total_sv:
                                self.emit_progress(2, _i + 1, _total, f"{_course_name} ({done}/{total_sv} SV)")

                        concurrent_result = fetcher.fetch_users_concurrent(
                            user_ids, course_id, progress_callback=_progress_cb
                        )
                        h5p_success = concurrent_result["success_count"]
                        self.emit_log(
                            f"  H5P/Video: {h5p_success}/{len(user_ids)} students synced"
                        )

                        # Aggregate raw data (CRITICAL step to populate raw_data table for predictions)
                        self.emit_log(f"  Aggregating raw_data for {len(user_ids)} students...")
                        agg_res = fetcher.aggregate_all_raw_data(course_id)
                        if agg_res.get("success"):
                            self.emit_log(f"  Aggregated: {agg_res.get('success_count')}/{agg_res.get('total_users')} success")
                        else:
                            self.emit_log(f"  Aggregate raw_data failed: {agg_res.get('message')}", "warning")

                    fetched_count += 1
                    time.sleep(0.3)

                except Exception as e:
                    self.emit_log(
                        f"  Lỗi fetch {course_name}: {e}", "warning"
                    )

            fetcher.close_db()

            self.emit_step(
                2, "completed", f"Fetch xong {fetched_count}/{total} courses"
            )
            self.emit_log(
                f"Bước 2 hoàn thành: {fetched_count}/{total} courses"
            )
            return fetched_count

        except Exception as e:
            self.emit_log(f"Lỗi bước fetch: {e}", "error")
            self.emit_step(2, "error", str(e))
            return 0

    # ──────────────────────────────────────────────────────────
    #  STEP 3: FEATURE ENGINEERING
    # ──────────────────────────────────────────────────────────

    def _step3_features(self, courses: list) -> int:
        self.emit_step(3, "running", "Đang tạo features cho sinh viên...")
        self.emit_log("Bước 3: Populate student_features từ raw data")

        try:
            from backend.populate_student_features import populate_student_features

            total = len(courses)
            total_affected = 0

            for i, course in enumerate(courses):
                self._check_stop()
                course_id = course.get("id", "")
                course_name = course.get("display_name", course_id)

                self.emit_progress(3, i + 1, total, course_name)

                try:
                    affected = populate_student_features(course_id)
                    total_affected += affected or 0
                    if affected:
                        self.emit_log(
                            f"  [{i+1}/{total}] {course_name}: {affected} features"
                        )
                except Exception as e:
                    self.emit_log(
                        f"  [{i+1}/{total}] {course_name}: lỗi - {e}",
                        "warning",
                    )

            self.emit_step(
                3, "completed", f"{total_affected} student features"
            )
            self.emit_log(
                f"Bước 3 hoàn thành: {total_affected} student features"
            )
            return total_affected

        except Exception as e:
            self.emit_log(f"Lỗi bước features: {e}", "error")
            self.emit_step(3, "error", str(e))
            return 0

    # ──────────────────────────────────────────────────────────
    #  STEP 4: TRAINING
    # ──────────────────────────────────────────────────────────

    def _step4_training(self) -> list:
        self.emit_step(4, "running", "Đang kiểm tra và training model...")

        trained_list = []

        try:
            from backend.db import (
                discover_course_groups,
                count_labeled_students,
                get_model_for_courses,
                get_last_training_record,
                save_training_record,
                register_model_for_courses,
            )

            min_students = int(os.getenv("MIN_STUDENTS_FOR_TRAINING", "300"))
            retrain_threshold = int(os.getenv("RETRAIN_THRESHOLD", "50"))
            self.emit_log(
                f"Bước 4: Kiểm tra course groups "
                f"(ngưỡng train: {min_students} SV, retrain: +{retrain_threshold} SV)"
            )

            groups = discover_course_groups()

            if not groups:
                self.emit_log("Không tìm thấy nhóm khóa học nào trong DB.", "warning")
                self.emit_step(4, "completed", "Không có nhóm nào")
                return []

            self.emit_log(f"Phát hiện {len(groups)} nhóm môn học")
            total_groups = len(groups)

            for idx, (base_name, course_ids) in enumerate(groups.items()):
                self._check_stop()
                self.emit_progress(4, idx + 1, total_groups, base_name)

                labeled = count_labeled_students(course_ids)
                model_info = get_model_for_courses(course_ids)

                # ── Đã có model → kiểm tra có cần retrain không ──
                if model_info:
                    last_record = get_last_training_record(base_name)
                    last_trained_count = (
                        last_record.get("labeled_student_count", 0)
                        if last_record else 0
                    )
                    new_students = labeled - last_trained_count

                    if new_students >= retrain_threshold:
                        self.emit_log(
                            f"  {base_name}: model '{model_info['model_name']}' "
                            f"đã có, +{new_students} SV mới >= {retrain_threshold} → RETRAIN!"
                        )
                        started_at = datetime.now().isoformat()
                        try:
                            from ml.train_model import train_for_courses

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
                                    message=(
                                        f"Pipeline retrain: +{new_students} SV mới, "
                                        f"tổng {result['student_count']} SV"
                                    ),
                                    started_at=started_at,
                                    completed_at=datetime.now().isoformat(),
                                )
                                self.emit_log(
                                    f"  RETRAIN THÀNH CÔNG: {result['model_name']} "
                                    f"(Acc={result['accuracy']:.3f}, "
                                    f"F1={result['f1_score']:.3f}, "
                                    f"AUC={result['auc_roc']:.3f})"
                                )
                                trained_list.append(
                                    {
                                        "base_name": base_name,
                                        "model_name": result["model_name"],
                                        "action": "retrain",
                                        "accuracy": result["accuracy"],
                                        "f1_score": result["f1_score"],
                                        "auc_roc": result["auc_roc"],
                                        "student_count": result["student_count"],
                                        "new_students": new_students,
                                    }
                                )
                            else:
                                self.emit_log(
                                    f"  Retrain thất bại cho {base_name}", "error"
                                )
                        except Exception as e:
                            self.emit_log(f"  Lỗi retrain {base_name}: {e}", "error")
                    else:
                        self.emit_log(
                            f"  {base_name}: model '{model_info['model_name']}' đã có "
                            f"({labeled} SV, +{new_students} mới) — "
                            f"chưa đủ ngưỡng retrain (cần +{retrain_threshold - new_students} SV nữa)"
                        )
                    continue

                # ── Chưa có model → kiểm tra đủ data train lần đầu chưa ──
                if labeled < min_students:
                    self.emit_log(
                        f"  {base_name}: {labeled}/{min_students} SV — "
                        f"chưa đủ data, cần thêm {min_students - labeled} SV"
                    )
                    continue

                self.emit_log(
                    f"  {base_name}: {labeled} SV >= {min_students} — "
                    f"BẮT ĐẦU INITIAL TRAINING!"
                )

                started_at = datetime.now().isoformat()
                try:
                    from ml.train_model import train_for_courses

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
                            action="initial_train",
                            labeled_student_count=result["student_count"],
                            accuracy=result["accuracy"],
                            f1_score=result["f1_score"],
                            auc_roc=result["auc_roc"],
                            status="success",
                            message=f"Pipeline initial_train: {result['model_name']}",
                            started_at=started_at,
                            completed_at=datetime.now().isoformat(),
                        )
                        self.emit_log(
                            f"  TRAINING THÀNH CÔNG: {result['model_name']} "
                            f"(Acc={result['accuracy']:.3f}, "
                            f"F1={result['f1_score']:.3f}, "
                            f"AUC={result['auc_roc']:.3f})"
                        )
                        trained_list.append(
                            {
                                "base_name": base_name,
                                "model_name": result["model_name"],
                                "action": "initial_train",
                                "accuracy": result["accuracy"],
                                "f1_score": result["f1_score"],
                                "auc_roc": result["auc_roc"],
                                "student_count": result["student_count"],
                            }
                        )
                    else:
                        self.emit_log(
                            f"  Training thất bại cho {base_name}", "error"
                        )
                        save_training_record(
                            base_name=base_name,
                            course_ids=course_ids,
                            model_name=None,
                            action="initial_train",
                            labeled_student_count=labeled,
                            status="failed",
                            message="Pipeline initial_train failed",
                            started_at=started_at,
                            completed_at=datetime.now().isoformat(),
                        )
                except Exception as e:
                    self.emit_log(
                        f"  Lỗi training {base_name}: {e}", "error"
                    )

            status_msg = (
                f"Đã xử lý {len(trained_list)} nhóm (initial/retrain)"
                if trained_list
                else "Không có nhóm nào cần training/retrain"
            )
            self.emit_step(4, "completed", status_msg)
            self.emit_log(f"Bước 4 hoàn thành: {status_msg}")
            return trained_list

        except Exception as e:
            self.emit_log(f"Lỗi bước training: {e}", "error")
            self.emit_step(4, "error", str(e))
            return []

    # ──────────────────────────────────────────────────────────
    #  STEP 5: PREDICTION
    # ──────────────────────────────────────────────────────────

    def _step5_prediction(self) -> list:
        self.emit_step(5, "running", "Đang predict cho sinh viên...")
        self.emit_log("Bước 5: Chạy prediction cho tất cả courses có model")

        predicted_list = []

        try:
            from backend.db import (
                discover_course_groups,
                get_model_for_courses,
                save_training_record,
            )
            from backend.inference_service import InferenceService

            groups = discover_course_groups()
            total_groups = len(groups)

            for idx, (base_name, course_ids) in enumerate(groups.items()):
                self._check_stop()
                self.emit_progress(5, idx + 1, total_groups, base_name)

                model_info = get_model_for_courses(course_ids)
                if not model_info:
                    continue

                self.emit_log(
                    f"  {base_name}: predict với model '{model_info['model_name']}'"
                )

                try:
                    service = InferenceService(
                        model_path=model_info.get("model_path"),
                        feature_fallback_csv=model_info.get("features_csv_path"),
                    )

                    predicted_count = 0
                    high_risk = 0
                    for cid in course_ids:
                        result_df = service.predict_course(cid, save_db=True)
                        if result_df is not None and not result_df.empty:
                            predicted_count += len(result_df)
                            high_risk += int(
                                (result_df["fail_risk_score"] >= 55).sum()
                            )

                    if predicted_count > 0:
                        self.emit_log(
                            f"  Predicted {predicted_count} SV, "
                            f"{high_risk} nguy cơ cao"
                        )
                        predicted_list.append(
                            {
                                "base_name": base_name,
                                "predicted_count": predicted_count,
                                "high_risk_count": high_risk,
                            }
                        )

                        save_training_record(
                            base_name=base_name,
                            course_ids=course_ids,
                            model_name=model_info["model_name"],
                            action="predict",
                            predicted_student_count=predicted_count,
                            status="success",
                            message=(
                                f"Pipeline predict: {predicted_count} SV, "
                                f"{high_risk} high risk"
                            ),
                            started_at=datetime.now().isoformat(),
                            completed_at=datetime.now().isoformat(),
                        )

                except Exception as e:
                    self.emit_log(
                        f"  Lỗi predict {base_name}: {e}", "warning"
                    )

            total_predicted = sum(p["predicted_count"] for p in predicted_list)
            self.emit_step(
                5,
                "completed",
                f"Predicted {total_predicted} sinh viên",
            )
            self.emit_log(f"Bước 5 hoàn thành: {total_predicted} SV predicted")
            return predicted_list

        except Exception as e:
            self.emit_log(f"Lỗi bước prediction: {e}", "error")
            self.emit_step(5, "error", str(e))
            return []

    # ──────────────────────────────────────────────────────────
    #  SELECTIVE FETCH: Chỉ Step 2 + Step 3 cho courses cụ thể
    # ──────────────────────────────────────────────────────────

    def _run_fetch_only(self, course_ids: list, session_id: str = ""):
        """
        Pipeline rút gọn: chỉ Fetch + Feature Engineering cho course_ids được chọn.

        Args:
            course_ids: Danh sách course_id string
            session_id: MOOC session (optional)
        """
        self._running = True
        started = datetime.now()

        self.emit("pipeline_start", message="Fetch có chọn lọc — bắt đầu")
        self.emit_log("=" * 50)
        self.emit_log(f"⚡ Fetch có chọn lọc — {len(course_ids)} khóa học")
        self.emit_log("=" * 50)

        summary = {
            "started_at": started.isoformat(),
            "courses_discovered": len(course_ids),
            "courses_fetched": 0,
            "students_featured": 0,
            "courses_trained": [],
            "courses_predicted": [],
            "errors": [],
        }

        # Lấy course info từ DB để có course_name
        try:
            from backend.db import fetch_all
            rows = fetch_all(
                f"""
                SELECT DISTINCT course_id, MAX(course_name) as course_name
                FROM enrollments
                WHERE course_id IN ({','.join(['%s'] * len(course_ids))})
                GROUP BY course_id
                """,
                tuple(course_ids),
            )
            course_map = {r["course_id"]: r.get("course_name", r["course_id"]) for r in rows}
            courses = [
                {"id": cid, "display_name": course_map.get(cid, cid)}
                for cid in course_ids
            ]
        except Exception as e:
            courses = [{"id": cid, "display_name": cid} for cid in course_ids]
            self.emit_log(f"Không lấy được tên khóa học từ DB: {e}", "warning")

        try:
            # ── Step 2: Fetch data ──
            self.emit_log(f"Sẽ fetch {len(courses)} khóa học đã chọn")
            fetched = self._step2_fetch(courses, session_id)
            summary["courses_fetched"] = fetched
            self._check_stop()

            # ── Step 3: Feature Engineering ──
            featured = self._step3_features(courses)
            summary["students_featured"] = featured
            self._check_stop()

            # ── Step 4: Training ──
            # Step 4 tự phát hiện groups và train nếu đủ threshold
            trained_list = self._step4_training()
            summary["courses_trained"] = trained_list
            self._check_stop()

            # ── Step 5: Prediction ──
            predicted_list = self._step5_prediction()
            summary["courses_predicted"] = predicted_list

        except InterruptedError:
            self.emit_log("Tiến trình bị dừng bởi user.", "warning")
            summary["errors"].append("Stopped by user")
        except Exception as e:
            logger.exception("Selective pipeline error")
            self.emit_log(f"Lỗi: {e}", "error")
            summary["errors"].append(str(e))

        elapsed = (datetime.now() - started).total_seconds()
        summary["elapsed_seconds"] = round(elapsed, 1)
        summary["completed_at"] = datetime.now().isoformat()
        self._summary = summary

        self.emit_log("=" * 50)
        self.emit_log(
            f"⚡ Hoàn thành Pipeline có chọn lọc trong {elapsed:.1f}s — "
            f"{fetched} courses fetched, {len(summary['courses_trained'])} models updated"
        )
        self.emit("done", summary=summary)
        self._running = False


# ── Singleton ──

_pipeline_instance: Optional[PipelineService] = None


def get_pipeline_service(app=None) -> PipelineService:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = PipelineService(app=app)
    return _pipeline_instance
