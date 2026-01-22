"""
Storage Manager: Quản lý lưu trữ và truy xuất dữ liệu đã chuẩn bị
Lưu trữ vào MySQL database
"""
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd
import mysql.connector
from mysql.connector import Error

sys.path.append(str(Path(__file__).parent.parent))
from config import DB_CONFIG, LOGS_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f"storage_manager_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StorageManager:
    """Class để quản lý lưu trữ dữ liệu vào MySQL database"""
    
    def __init__(self):
        self.db_config = DB_CONFIG
        self.connection = None
    
    def connect(self):
        """Kết nối đến MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["database"],
                user=self.db_config["user"],
                password=self.db_config["password"]
            )
            
            if self.connection.is_connected():
                logger.info(f"Connected to MySQL database: {self.db_config['database']}")
                return True
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            return False
    
    def disconnect(self):
        """Đóng kết nối database"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
    
    def save_raw_data(self, df: pd.DataFrame, batch_id: str) -> bool:
        """Lưu raw data vào database"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False
        
        try:
            cursor = self.connection.cursor()
            
            # Chuẩn bị dữ liệu
            records = []
            for _, row in df.iterrows():
                record = (
                    str(row.get("user_id", "")),
                    str(row.get("course_id", "")),
                    pd.to_datetime(row.get("enrollment_date")) if pd.notna(row.get("enrollment_date")) else None,
                    str(row.get("enrollment_mode", "")),
                    bool(row.get("is_active", True)),
                    float(row.get("progress_percent", 0)),
                    int(row.get("completed_blocks", 0)),
                    int(row.get("total_blocks", 0)),
                    pd.to_datetime(row.get("last_activity")) if pd.notna(row.get("last_activity")) else None,
                    int(row.get("total_attempts", 0)),
                    float(row.get("avg_score", 0)),
                    float(row.get("max_score", 0)),
                    float(row.get("min_score", 0)),
                    int(row.get("total_video_views", 0)),
                    int(row.get("total_videos", 0)),
                    float(row.get("avg_completion", 0)),
                    int(row.get("total_contents", 0)),
                    int(row.get("completed_contents", 0)),
                    int(row.get("total_score", 0)),
                    int(row.get("total_max_score", 0)),
                    float(row.get("overall_percentage", 0)),
                    int(row.get("total_time_spent", 0)),
                    int(row.get("h5p_total_videos", row.get("completed_videos", 0))),
                    int(row.get("h5p_completed_videos", 0)),
                    int(row.get("total_duration", 0)),
                    int(row.get("total_watched_time", 0)),
                    int(row.get("threads_count", 0)),
                    int(row.get("comments_count", 0)),
                    int(row.get("total_upvotes", 0)),
                    batch_id
                )
                records.append(record)
            
            # Insert vào database
            insert_query = """
            INSERT INTO raw_data (
                user_id, course_id, enrollment_date, enrollment_mode, is_active,
                progress_percent, completed_blocks, total_blocks, last_activity,
                total_attempts, avg_score, max_score, min_score,
                total_video_views, total_videos, avg_completion,
                h5p_total_contents, h5p_completed_contents, h5p_total_score, h5p_total_max_score,
                h5p_overall_percentage, h5p_total_time_spent,
                h5p_total_videos, h5p_completed_videos, h5p_total_duration, h5p_total_watched_time,
                threads_count, comments_count, total_upvotes,
                extraction_batch_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_query, records)
            self.connection.commit()
            logger.info(f"Saved {len(records)} raw data records to database (batch: {batch_id})")
            return True
            
        except Error as e:
            logger.error(f"Error saving raw data: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def save_features(self, df: pd.DataFrame, batch_id: str) -> bool:
        """Lưu features vào database"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False
        
        try:
            cursor = self.connection.cursor()
            
            records = []
            for _, row in df.iterrows():
                record = (
                    str(row.get("user_id", "")),
                    str(row.get("course_id", "")),
                    float(row.get("access_frequency", 0)),
                    int(row.get("active_days", 0)),
                    int(row.get("last_activity_days_ago", 999)),
                    float(row.get("video_watch_rate", 0)),
                    float(row.get("video_completion_rate", 0)),
                    float(row.get("total_video_time", 0)),
                    int(row.get("quiz_attempts", 0)),
                    float(row.get("quiz_avg_score", 0)),
                    float(row.get("quiz_completion_rate", 0)),
                    int(row.get("missed_deadlines", 0)),
                    float(row.get("h5p_completion_rate", 0)),
                    float(row.get("h5p_avg_score", 0)),
                    int(row.get("forum_posts", 0)),
                    int(row.get("forum_comments", 0)),
                    int(row.get("forum_upvotes", 0)),
                    float(row.get("overall_progress", 0)),
                    float(row.get("progress_delta", 0)),
                    float(row.get("weeks_since_enrollment", 0)),
                    float(row.get("weeks_since_start", 0)),
                    batch_id
                )
                records.append(record)
            
            insert_query = """
            INSERT INTO features (
                user_id, course_id,
                access_frequency, active_days, last_activity_days_ago,
                video_watch_rate, video_completion_rate, total_video_time,
                quiz_attempts, quiz_avg_score, quiz_completion_rate, missed_deadlines,
                h5p_completion_rate, h5p_avg_score,
                forum_posts, forum_comments, forum_upvotes,
                overall_progress, progress_delta,
                weeks_since_enrollment, weeks_since_start,
                feature_batch_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_query, records)
            self.connection.commit()
            logger.info(f"Saved {len(records)} feature records to database (batch: {batch_id})")
            return True
            
        except Error as e:
            logger.error(f"Error saving features: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def save_labels(self, df: pd.DataFrame, batch_id: str) -> bool:
        """Lưu labels vào database"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False
        
        try:
            cursor = self.connection.cursor()
            
            records = []
            for _, row in df.iterrows():
                record = (
                    str(row.get("user_id", "")),
                    str(row.get("course_id", "")),
                    bool(row.get("passed", False)),
                    pd.to_datetime(row.get("passed_date")) if pd.notna(row.get("passed_date")) else None,
                    float(row.get("weeks_since_last_passed", 999)),
                    bool(row.get("dropout", False)),
                    str(row.get("risk_level", "Low")),
                    pd.to_datetime(row.get("enrollment_date")) if pd.notna(row.get("enrollment_date")) else None,
                    float(row.get("weeks_since_enrollment", 0)),
                    batch_id
                )
                records.append(record)
            
            insert_query = """
            INSERT INTO labels (
                user_id, course_id,
                passed, passed_date, weeks_since_last_passed,
                dropout, risk_level,
                enrollment_date, weeks_since_enrollment,
                label_batch_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_query, records)
            self.connection.commit()
            logger.info(f"Saved {len(records)} label records to database (batch: {batch_id})")
            return True
            
        except Error as e:
            logger.error(f"Error saving labels: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def save_training_sets(self, train_df: pd.DataFrame, val_df: pd.DataFrame, 
                          test_df: pd.DataFrame, batch_id: str) -> bool:
        """Lưu training sets vào database"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False
        
        try:
            cursor = self.connection.cursor()
            
            all_sets = [
                ("train", train_df),
                ("val", val_df),
                ("test", test_df)
            ]
            
            total_records = 0
            for set_type, df in all_sets:
                if df.empty:
                    continue
                    
                records = []
                feature_cols = [col for col in df.columns if col not in ["dropout", "user_id", "course_id"]]
                
                for _, row in df.iterrows():
                    features_dict = {col: float(row[col]) if pd.notna(row[col]) else 0 for col in feature_cols}
                    
                    record = (
                        set_type,
                        str(row.get("user_id", "")),
                        str(row.get("course_id", "")),
                        json.dumps(features_dict),
                        bool(row.get("dropout", False)),
                        batch_id
                    )
                    records.append(record)
                
                insert_query = """
                INSERT INTO training_sets (
                    set_type, user_id, course_id, features_json, dropout, training_batch_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                cursor.executemany(insert_query, records)
                total_records += len(records)
                logger.info(f"Saved {len(records)} {set_type} records")
            
            self.connection.commit()
            logger.info(f"Saved {total_records} total training set records (batch: {batch_id})")
            return True
            
        except Error as e:
            logger.error(f"Error saving training sets: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def load_training_data(self, batch_id: str) -> Optional[Dict[str, pd.DataFrame]]:
        """Load training data từ database"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            result = {}
            for set_type in ["train", "val", "test"]:
                query = """
                SELECT * FROM training_sets
                WHERE training_batch_id = %s AND set_type = %s
                ORDER BY id
                """
                cursor.execute(query, (batch_id, set_type))
                rows = cursor.fetchall()
                
                if rows:
                    # Parse features_json và tạo DataFrame
                    data = []
                    for row in rows:
                        features = json.loads(row["features_json"])
                        features["user_id"] = row["user_id"]
                        features["course_id"] = row["course_id"]
                        features["dropout"] = row["dropout"]
                        data.append(features)
                    
                    result[set_type] = pd.DataFrame(data)
                    logger.info(f"Loaded {len(result[set_type])} {set_type} records")
                else:
                    result[set_type] = pd.DataFrame()
            
            return result
            
        except Error as e:
            logger.error(f"Error loading training data: {e}")
            return None
        finally:
            cursor.close()
    
    def get_complete_data(self, course_id: str) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu đầy đủ (raw + features + labels) cho một course"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        
        try:
            query = "SELECT * FROM vw_complete_data WHERE course_id = %s"
            df = pd.read_sql(query, self.connection, params=(course_id,))
            logger.info(f"Loaded {len(df)} complete records for course {course_id}")
            return df
        except Error as e:
            logger.error(f"Error loading complete data: {e}")
            return None
    
    def create_batch_metadata(self, batch_id: str, batch_type: str, course_id: str = None,
                            total_records: int = 0, config: Dict = None) -> bool:
        """Tạo metadata cho một batch"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False
        
        try:
            cursor = self.connection.cursor()
            insert_query = """
            INSERT INTO batch_metadata (
                batch_id, batch_type, course_id, total_records, config_json, status
            ) VALUES (%s, %s, %s, %s, %s, 'running')
            """
            config_json = json.dumps(config) if config else None
            cursor.execute(insert_query, (batch_id, batch_type, course_id, total_records, config_json))
            self.connection.commit()
            logger.info(f"Created batch metadata: {batch_id}")
            return True
        except Error as e:
            logger.error(f"Error creating batch metadata: {e}")
            return False
        finally:
            cursor.close()
    
    def update_batch_status(self, batch_id: str, status: str, 
                           success_records: int = 0, failed_records: int = 0,
                           error_message: str = None) -> bool:
        """Cập nhật trạng thái batch"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False
        
        try:
            cursor = self.connection.cursor()
            update_query = """
            UPDATE batch_metadata
            SET status = %s, success_records = %s, failed_records = %s,
                completed_at = CURRENT_TIMESTAMP, error_message = %s
            WHERE batch_id = %s
            """
            cursor.execute(update_query, (status, success_records, failed_records, error_message, batch_id))
            self.connection.commit()
            logger.info(f"Updated batch {batch_id} status to {status}")
            return True
        except Error as e:
            logger.error(f"Error updating batch status: {e}")
            return False
        finally:
            cursor.close()


def main():
    """Test function"""
    manager = StorageManager()
    
    if manager.connect():
        logger.info("Storage manager connected successfully!")
        manager.disconnect()
    else:
        logger.error("Failed to connect to database!")


if __name__ == "__main__":
    main()

