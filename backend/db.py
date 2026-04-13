"""
Database helper functions cho MySQL connection
"""
import os
import logging
from typing import Optional, List, Dict, Any
import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool

logger = logging.getLogger(__name__)

# Global connection pool — initialized once on first use
_pool: Optional[MySQLConnectionPool] = None


def get_db_config() -> Dict[str, Any]:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "4000")),
        "database": os.getenv("DB_NAME", "dropout_prediction_db"),
        "user": os.getenv("DB_USER", "dropout_user"),
        "password": os.getenv("DB_PASSWORD", "dropout_pass_123"),
    }


def _get_pool() -> MySQLConnectionPool:
    global _pool
    if _pool is None:
        config = get_db_config()
        _pool = MySQLConnectionPool(
            pool_name="dropout_pool",
            pool_size=10,
            pool_reset_session=True,
            connection_timeout=30,
            **config,
        )
        logger.info("DB connection pool initialized (size=10)")
    return _pool


def get_db_connection():
    """
    Lấy một connection từ pool.
    Trả về pooled connection hoặc None nếu lỗi.
    """
    try:
        return _get_pool().get_connection()
    except Error as e:
        logger.error(f"Lỗi lấy connection từ pool: {e}")
        return None


def execute(query: str, params: tuple = None) -> Optional[int]:
    connection = get_db_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        connection.commit()
        rows_affected = cursor.rowcount
        cursor.close()
        return rows_affected
    except Error as e:
        logger.error(f"Lỗi thực thi query: {query[:100]}... - {e}")
        connection.rollback()
        return None
    finally:
        if connection.is_connected():
            connection.close()


def fetch_all(query: str, params: tuple = None) -> List[Dict]:
    connection = get_db_connection()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        cursor.close()
        return results
    except Error as e:
        logger.error(f"Lỗi fetch data: {query[:100]}... - {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()


def fetch_one(query: str, params: tuple = None) -> Optional[Dict]:
    connection = get_db_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchone()
        cursor.close()
        return result
    except Error as e:
        logger.error(f"Lỗi fetch one data: {query[:100]}... - {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()


# ============================================================================
# HELPER FUNCTIONS FOR NEW SCHEMA V2
# ============================================================================

def get_student_features(user_id: int, course_id: str) -> Optional[Dict]:
    return fetch_one(
        "SELECT * FROM student_features WHERE user_id = %s AND course_id = %s",
        (user_id, course_id)
    )


def get_latest_prediction(user_id: int, course_id: str, model_name: Optional[str] = None) -> Optional[Dict]:
    if model_name:
        return fetch_one(
            """
            SELECT * FROM predictions
            WHERE user_id = %s AND course_id = %s AND model_name = %s AND is_latest = TRUE
            ORDER BY predicted_at DESC LIMIT 1
            """,
            (user_id, course_id, model_name)
        )
    else:
        return fetch_one(
            """
            SELECT * FROM predictions
            WHERE user_id = %s AND course_id = %s AND is_latest = TRUE
            ORDER BY predicted_at DESC LIMIT 1
            """,
            (user_id, course_id)
        )


def save_prediction(user_id: int, course_id: str, model_name: str,
                   fail_risk_score: float, risk_level: str,
                   model_version: Optional[str] = None, model_path: Optional[str] = None,
                   snapshot_grade: Optional[float] = None,
                   snapshot_completion_rate: Optional[float] = None,
                   snapshot_days_inactive: Optional[int] = None) -> bool:
    connection = get_db_connection()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM predictions
            WHERE user_id = %s AND course_id = %s
            """,
            (user_id, course_id)
        )

        cursor.execute(
            """
            INSERT INTO predictions (
                user_id, course_id, model_name, model_version, model_path,
                fail_risk_score, risk_level,
                snapshot_grade, snapshot_completion_rate, snapshot_days_inactive,
                is_latest
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            """,
            (user_id, course_id, model_name, model_version, model_path,
             fail_risk_score, risk_level,
             snapshot_grade, snapshot_completion_rate, snapshot_days_inactive)
        )

        connection.commit()
        cursor.close()
        return True

    except Error as e:
        logger.error(f"Error saving prediction: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            connection.close()


def save_predictions_batch(
    predictions: List[Dict[str, Any]],
    model_name: str,
    model_version: str,
    model_path: str,
) -> int:
    if not predictions:
        return 0

    connection = get_db_connection()
    if connection is None:
        return 0

    try:
        cursor = connection.cursor()

        update_raw_data = [
            (float(p["fail_risk_score"]), int(p["user_id"]), p["course_id"])
            for p in predictions
        ]
        cursor.executemany(
            "UPDATE raw_data SET fail_risk_score = %s WHERE user_id = %s AND course_id = %s",
            update_raw_data,
        )

        course_ids = list({p["course_id"] for p in predictions})
        user_ids = [int(p["user_id"]) for p in predictions]
        placeholders_cid = ", ".join(["%s"] * len(course_ids))
        placeholders_uid = ", ".join(["%s"] * len(user_ids))
        cursor.execute(
            f"""
            UPDATE predictions SET is_latest = FALSE
            WHERE course_id IN ({placeholders_cid})
              AND user_id IN ({placeholders_uid})
            """,
            course_ids + user_ids,
        )

        insert_data = [
            (
                int(p["user_id"]),
                p["course_id"],
                model_name,
                model_version,
                model_path,
                float(p["fail_risk_score"]),
                p["risk_level"],
                float(p.get("snapshot_grade") or 0),
                float(p.get("snapshot_completion_rate") or 0),
                int(p.get("snapshot_days_inactive") or 0),
            )
            for p in predictions
        ]
        cursor.executemany(
            """
            INSERT INTO predictions (
                user_id, course_id, model_name, model_version, model_path,
                fail_risk_score, risk_level,
                snapshot_grade, snapshot_completion_rate, snapshot_days_inactive,
                is_latest
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            """,
            insert_data,
        )

        connection.commit()
        saved = len(insert_data)
        cursor.close()
        logger.info(f"Batch saved {saved} predictions (1 connection)")
        return saved

    except Error as e:
        logger.error(f"Error in save_predictions_batch: {e}")
        connection.rollback()
        return 0
    finally:
        if connection.is_connected():
            connection.close()


def get_course_model_mapping(course_id: str) -> Optional[Dict]:
    return fetch_one(
        """
        SELECT cmm.*, mr.model_path, mr.features_csv_path, mr.model_type
        FROM course_model_mapping cmm
        JOIN model_registry mr ON cmm.model_name = mr.model_name
        WHERE cmm.course_id = %s AND cmm.is_active = TRUE
        ORDER BY cmm.assigned_at DESC
        LIMIT 1
        """,
        (course_id,)
    )


def get_default_model() -> Optional[Dict]:
    return fetch_one(
        """
        SELECT * FROM model_registry
        WHERE is_default = TRUE AND is_active = TRUE
        LIMIT 1
        """
    )


# ============================================================================
# HELPER FUNCTIONS FOR SCHEDULER (MLOps Lifecycle)
# ============================================================================

def discover_course_groups() -> Dict[str, List[str]]:
    rows = fetch_all("""
        SELECT DISTINCT course_id, course_name
        FROM enrollments
        WHERE course_name IS NOT NULL AND course_name != ''
        GROUP BY course_id, course_name
    """)

    groups: Dict[str, List[str]] = {}
    for row in rows:
        course_name = row.get("course_name", "")
        course_id = row.get("course_id", "")
        if not course_name or not course_id:
            continue

        base_name = course_name.split(" - ")[0].strip()
        if base_name not in groups:
            groups[base_name] = []
        if course_id not in groups[base_name]:
            groups[base_name].append(course_id)

    return groups


def count_labeled_students(course_ids: List[str]) -> int:
    if not course_ids:
        return 0
    placeholders = ", ".join(["%s"] * len(course_ids))
    result = fetch_one(
        f"""
        SELECT COUNT(*) as labeled
        FROM mooc_grades
        WHERE course_id IN ({placeholders}) AND is_passed IS NOT NULL
        """,
        tuple(course_ids),
    )
    return int(result["labeled"]) if result else 0


def get_last_training_record(base_name: str) -> Optional[Dict]:
    return fetch_one(
        """
        SELECT * FROM training_history
        WHERE base_name = %s AND action IN ('initial_train', 'retrain')
              AND status = 'success'
        ORDER BY completed_at DESC
        LIMIT 1
        """,
        (base_name,),
    )


def save_training_record(
    base_name: str,
    course_ids: List[str],
    model_name: Optional[str],
    action: str,
    labeled_student_count: Optional[int] = None,
    predicted_student_count: Optional[int] = None,
    accuracy: Optional[float] = None,
    f1_score: Optional[float] = None,
    auc_roc: Optional[float] = None,
    status: str = "success",
    message: Optional[str] = None,
    started_at: Optional[str] = None,
    completed_at: Optional[str] = None,
) -> Optional[int]:
    import json
    return execute(
        """
        INSERT INTO training_history (
            base_name, course_ids, model_name, action,
            labeled_student_count, predicted_student_count,
            accuracy, f1_score, auc_roc,
            status, message, started_at, completed_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            base_name,
            json.dumps(course_ids),
            model_name,
            action,
            labeled_student_count,
            predicted_student_count,
            accuracy,
            f1_score,
            auc_roc,
            status,
            message,
            started_at,
            completed_at,
        ),
    )


def get_training_history(
    base_name: Optional[str] = None, limit: int = 50
) -> List[Dict]:
    if base_name:
        return fetch_all(
            """
            SELECT * FROM training_history
            WHERE base_name = %s
            ORDER BY started_at DESC
            LIMIT %s
            """,
            (base_name, limit),
        )
    return fetch_all(
        """
        SELECT * FROM training_history
        ORDER BY started_at DESC
        LIMIT %s
        """,
        (limit,),
    )


def get_model_for_courses(course_ids: List[str]) -> Optional[Dict]:
    if not course_ids:
        return None
    placeholders = ", ".join(["%s"] * len(course_ids))
    return fetch_one(
        f"""
        SELECT cmm.*, mr.model_path, mr.features_csv_path,
               mr.model_type, mr.model_version
        FROM course_model_mapping cmm
        JOIN model_registry mr ON cmm.model_name = mr.model_name
        WHERE cmm.course_id IN ({placeholders}) AND cmm.is_active = TRUE
        ORDER BY cmm.assigned_at DESC
        LIMIT 1
        """,
        tuple(course_ids),
    )


def register_model_for_courses(
    model_name: str,
    model_version: str,
    model_path: str,
    features_csv_path: str,
    course_ids: List[str],
    model_type: str = "CatBoost",
    domain: str = "dropout_prediction",
) -> bool:
    connection = get_db_connection()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO model_registry
                (model_name, model_version, model_path, features_csv_path,
                 model_type, domain, is_active, is_default)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE, FALSE)
            ON DUPLICATE KEY UPDATE
                model_version = VALUES(model_version),
                model_path    = VALUES(model_path),
                features_csv_path = VALUES(features_csv_path),
                is_active = TRUE
            """,
            (model_name, model_version, model_path, features_csv_path,
             model_type, domain),
        )

        for cid in course_ids:
            cursor.execute(
                "UPDATE course_model_mapping SET is_active = FALSE WHERE course_id = %s",
                (cid,),
            )
            cursor.execute(
                """
                INSERT INTO course_model_mapping
                    (course_id, model_name, auto_predict, is_active)
                VALUES (%s, %s, TRUE, TRUE)
                """,
                (cid, model_name),
            )

        connection.commit()
        cursor.close()
        return True

    except Error as e:
        logger.error(f"Error registering model: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            connection.close()
