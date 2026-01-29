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

