"""
Database helper functions cho MySQL connection
"""
import os
import logging
from typing import Optional, List, Dict, Any
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)


def get_db_config() -> Dict[str, Any]:
    """
    Lấy cấu hình database từ biến môi trường hoặc dùng giá trị mặc định
    
    Returns:
        Dict chứa thông tin kết nối database
    """
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "4000")),
        "database": os.getenv("DB_NAME", "dropout_prediction_db"),
        "user": os.getenv("DB_USER", "dropout_user"),
        "password": os.getenv("DB_PASSWORD", "dropout_pass_123"),
    }


def get_db_connection():
    """
    Tạo và trả về một kết nối database mới
    
    Returns:
        Connection object hoặc None nếu lỗi
    """
    db_config = get_db_config()
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        logger.error(f"Lỗi kết nối database: {e}")
        return None


def execute(query: str, params: tuple = None) -> Optional[int]:
    """
    Thực thi một query (INSERT, UPDATE, DELETE, CREATE TABLE)
    
    Args:
        query: SQL query string
        params: Tuple các parameters cho query
        
    Returns:
        Số dòng bị ảnh hưởng hoặc None nếu lỗi
    """
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
    """
    Thực thi một query SELECT và trả về tất cả kết quả
    
    Args:
        query: SQL query string
        params: Tuple các parameters cho query
        
    Returns:
        List of dictionaries, mỗi dict là một row
    """
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
    """
    Thực thi một query SELECT và trả về một kết quả duy nhất
    
    Args:
        query: SQL query string
        params: Tuple các parameters cho query
        
    Returns:
        Dictionary của row hoặc None nếu không tìm thấy
    """
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
    """
    Lấy features của một sinh viên
    
    Args:
        user_id: ID sinh viên
        course_id: ID khóa học
        
    Returns:
        Dictionary chứa features hoặc None
    """
    return fetch_one(
        "SELECT * FROM student_features WHERE user_id = %s AND course_id = %s",
        (user_id, course_id)
    )


def get_latest_prediction(user_id: int, course_id: str, model_name: Optional[str] = None) -> Optional[Dict]:
    """
    Lấy prediction mới nhất của sinh viên
    
    Args:
        user_id: ID sinh viên
        course_id: ID khóa học
        model_name: Tên model (optional, nếu muốn filter theo model)
        
    Returns:
        Dictionary chứa prediction hoặc None
    """
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
    """
    Lưu prediction mới và mark predictions cũ là not latest
    
    Args:
        user_id: ID sinh viên
        course_id: ID khóa học
        model_name: Tên model
        fail_risk_score: Risk score (0-100)
        risk_level: 'LOW', 'MEDIUM', 'HIGH'
        model_version: Version của model
        model_path: Path to model file
        snapshot_grade: Grade tại thời điểm predict
        snapshot_completion_rate: Completion rate tại thời điểm predict
        snapshot_days_inactive: Days inactive tại thời điểm predict
        
    Returns:
        True nếu thành công, False nếu lỗi
    """
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
        
        # 2. Insert bản ghi mới (luôn is_latest = TRUE)
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


def get_course_model_mapping(course_id: str) -> Optional[Dict]:
    """
    Lấy model mapping cho course
    
    Args:
        course_id: ID khóa học
        
    Returns:
        Dictionary chứa mapping config hoặc None
    """
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
    """
    Lấy default model từ registry
    
    Returns:
        Dictionary chứa model info hoặc None
    """
    return fetch_one(
        """
        SELECT * FROM model_registry 
        WHERE is_default = TRUE AND is_active = TRUE
        LIMIT 1
        """
    )

