"""
Script để lấy dữ liệu từ MOOC và H5P APIs và lưu vào database
"""
import sys
import logging
import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import mysql.connector
from mysql.connector import Error
from urllib.parse import quote
import time

# Thêm parent directory vào path để import config
sys.path.append(str(Path(__file__).parent.parent))

# Cấu hình APIs
MOOC_API_BASE_URL = "https://mooc.vnuhcm.edu.vn/api/custom/v1"  # Open edX (MOOC)
H5P_API_BASE_URL = "https://h5p.itp.vn/wp-json/mooc/v1"  # H5P API

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 4000,
    "database": "dropout_prediction_db",
    "user": "dropout_user",
    "password": "dropout_pass_123"
}

# Setup logging
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f"fetch_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MOOCH5PDataFetcher:
    """Class để fetch data từ MOOC và H5P APIs"""
    
    def __init__(self):
        self.mooc_base_url = MOOC_API_BASE_URL
        self.h5p_base_url = H5P_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DropoutPrediction/1.0',
            'Accept': 'application/json'
        })
        self.db_connection = None
    
    def connect_db(self):
        """Kết nối đến database"""
        try:
            self.db_connection = mysql.connector.connect(**DB_CONFIG)
            logger.info("Connected to database successfully")
            return True
        except Error as e:
            logger.error(f"Error connecting to database: {e}")
            return False
    
    def close_db(self):
        """Đóng kết nối database"""
        if self.db_connection and self.db_connection.is_connected():
            self.db_connection.close()
            logger.info("Database connection closed")

    def set_mooc_session(self, sessionid: str):
        """Thiết lập cookie session cho MOOC API"""
        if not sessionid:
            return
        self.session.cookies.set("sessionid", sessionid)
        self.session.cookies.set("edx-session", sessionid)
    
    def url_encode_course_id(self, course_id: str) -> str:
        """URL encode course_id để tránh lỗi với ký tự đặc biệt"""
        return quote(course_id, safe='')
    
    def parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime từ nhiều format"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f%z')
            except:
                try:
                    return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                except:
                    return None
            return None
    
    # ==================== ENROLLMENTS ====================
    
    def save_enrollments(self, enrollments: List[Dict], course_id: str) -> bool:
        """Lưu danh sách enrollments vào bảng enrollments"""
        if not self.db_connection or not self.db_connection.is_connected():
            if not self.connect_db():
                return False
        
        try:
            cursor = self.db_connection.cursor()
            
            insert_query = """
            INSERT INTO enrollments (
                course_id, user_id, username, email, full_name, enrollment_id,
                mode, is_active, created,
                mssv, first_name, middle_name, last_name, full_name_vn,
                class_code, department, faculty, all_attributes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                email = VALUES(email),
                full_name = VALUES(full_name),
                mode = VALUES(mode),
                is_active = VALUES(is_active),
                created = VALUES(created),
                mssv = VALUES(mssv),
                first_name = VALUES(first_name),
                middle_name = VALUES(middle_name),
                last_name = VALUES(last_name),
                full_name_vn = VALUES(full_name_vn),
                class_code = VALUES(class_code),
                department = VALUES(department),
                faculty = VALUES(faculty),
                all_attributes = VALUES(all_attributes),
                updated_at = CURRENT_TIMESTAMP
            """
            
            saved_count = 0
            for enrollment in enrollments:
                student_info = enrollment.get('student_info', {}) or {}
                created_date = self.parse_datetime(enrollment.get('created'))
                all_attrs = enrollment.get('all_attributes', [])
                all_attrs_json = json.dumps(all_attrs) if all_attrs else None
                
                values = (
                    course_id,
                    enrollment.get('user_id'),
                    enrollment.get('username', ''),
                    enrollment.get('email'),
                    enrollment.get('full_name'),
                    enrollment.get('enrollment_id'),
                    enrollment.get('mode', 'audit'),
                    enrollment.get('is_active', True),
                    created_date,
                    student_info.get('mssv', ''),
                    student_info.get('first_name', ''),
                    student_info.get('middle_name', ''),
                    student_info.get('last_name', ''),
                    student_info.get('full_name_vn', ''),
                    student_info.get('class_code', ''),
                    student_info.get('department', ''),
                    student_info.get('faculty', ''),
                    all_attrs_json
                )
                
                cursor.execute(insert_query, values)
                saved_count += 1
            
            self.db_connection.commit()
            logger.info(f"Saved {saved_count} enrollments for course {course_id}")
            return True
            
        except Error as e:
            logger.error(f"Error saving enrollments: {e}")
            self.db_connection.rollback()
            return False
        finally:
            cursor.close()
    
    def fetch_mooc_course_students(self, course_id: str) -> Optional[List[int]]:
        """Lấy danh sách enrollments từ MOOC API và lưu vào bảng enrollments"""
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            limit = 200
            offset = 0
            user_ids: List[int] = []
            all_enrollments: List[Dict] = []

            while True:
                url = (
                    f"{self.mooc_base_url}/course-enrollments-attributes/"
                    f"{encoded_course_id}/?limit={limit}&offset={offset}"
                )
            
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()

                items = []
                if isinstance(data, dict):
                    if 'data' in data and isinstance(data['data'], dict):
                        data_obj = data['data']
                        if 'enrollments' in data_obj and isinstance(data_obj['enrollments'], list):
                            items = data_obj['enrollments']
                        elif isinstance(data_obj, list):
                            items = data_obj
                    elif 'enrollments' in data and isinstance(data['enrollments'], list):
                        items = data['enrollments']
                    elif 'results' in data and isinstance(data['results'], list):
                        items = data['results']
                    elif 'data' in data and isinstance(data['data'], list):
                        items = data['data']

                if not items:
                    break

                all_enrollments.extend(items)

                for item in items:
                    if not isinstance(item, dict):
                        continue
                    uid = item.get('user_id') or item.get('id')
                    if uid is not None:
                        user_ids.append(int(uid))

                if len(items) < limit:
                    break

                offset += limit

            if all_enrollments:
                self.save_enrollments(all_enrollments, course_id)
            
            logger.info(f"Fetched {len(user_ids)} students for course {course_id}")
            return user_ids
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching course students: {e}")
            return None
    
    # ==================== COURSE DETAILS (for course dates) ====================
    
    def fetch_course_details(self, course_id: str) -> Optional[Dict]:
        """Fetch course details từ MOOC API để lấy start/end date"""
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/course-details/display-name/?course_id={encoded_course_id}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and 'data' in data:
                course_data = data['data']
                return {
                    'course_name': course_data.get('display_name'),
                    'course_start': course_data.get('start'),
                    'course_end': course_data.get('end')
                }
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching course details for {course_id}: {e}")
            return None
    
    def update_enrollments_course_info(self, course_id: str, course_info: Dict) -> bool:
        """Cập nhật thông tin course_name, course_start, course_end vào enrollments"""
        if not self.db_connection or not self.db_connection.is_connected():
            if not self.connect_db():
                return False
        
        try:
            cursor = self.db_connection.cursor()
            
            # Parse datetime
            course_start = self.parse_datetime(course_info.get('course_start'))
            course_end = self.parse_datetime(course_info.get('course_end'))
            course_name = course_info.get('course_name')
            
            update_query = """
            UPDATE enrollments
            SET course_name = %s,
                course_start = %s,
                course_end = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE course_id = %s
            """
            
            cursor.execute(update_query, (course_name, course_start, course_end, course_id))
            affected_rows = cursor.rowcount
            
            self.db_connection.commit()
            logger.info(f"Updated course info for {affected_rows} enrollments in course {course_id}")
            logger.info(f"  - Course Name: {course_name}")
            logger.info(f"  - Course Start: {course_start}")
            logger.info(f"  - Course End: {course_end}")
            return True
            
        except Error as e:
            logger.error(f"Error updating enrollments course info: {e}")
            self.db_connection.rollback()
            return False
        finally:
            cursor.close()
    
    def fetch_and_update_course_info(self, course_id: str) -> bool:
        """Fetch course details và cập nhật vào enrollments"""
        course_info = self.fetch_course_details(course_id)
        if course_info:
            return self.update_enrollments_course_info(course_id, course_info)
        else:
            logger.warning(f"Could not fetch course details for {course_id}")
            return False
    
    # ==================== H5P SCORES ====================
    
    def save_h5p_scores(self, user_id: int, course_id: str, scores_data: Dict) -> bool:
        """Lưu H5P scores chi tiết và summary"""
        if not self.db_connection or not self.db_connection.is_connected():
            if not self.connect_db():
                return False
        
        try:
            cursor = self.db_connection.cursor()
            
            # Lưu chi tiết từng content
            scores = scores_data.get('scores', [])
            if scores:
                insert_detail_query = """
                INSERT INTO h5p_scores (
                    user_id, course_id, content_id, content_title, score, max_score,
                    percentage, opened, finished, time_spent, folder_id, folder_name
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    score = VALUES(score),
                    max_score = VALUES(max_score),
                    percentage = VALUES(percentage),
                    opened = VALUES(opened),
                    finished = VALUES(finished),
                    time_spent = VALUES(time_spent),
                    folder_id = VALUES(folder_id),
                    folder_name = VALUES(folder_name)
                """
                
                for score_item in scores:
                    values = (
                        user_id,
                        course_id,
                        score_item.get('content_id'),
                        score_item.get('content_title'),
                        score_item.get('score', 0),
                        score_item.get('max_score', 0),
                        score_item.get('percentage', 0),
                        score_item.get('opened', 0),
                        score_item.get('finished', 0),
                        score_item.get('time', 0),
                        score_item.get('folder_id'),
                        score_item.get('folder_name')
                    )
                    cursor.execute(insert_detail_query, values)
            
            # Lưu summary
            summary = scores_data.get('summary', {})
            if summary:
                insert_summary_query = """
                INSERT INTO h5p_scores_summary (
                    user_id, course_id, total_contents, completed_contents,
                    total_score, total_max_score, overall_percentage, total_time_spent
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    total_contents = VALUES(total_contents),
                    completed_contents = VALUES(completed_contents),
                    total_score = VALUES(total_score),
                    total_max_score = VALUES(total_max_score),
                    overall_percentage = VALUES(overall_percentage),
                    total_time_spent = VALUES(total_time_spent),
                    updated_at = CURRENT_TIMESTAMP
                """
                
                summary_values = (
                    user_id,
                    course_id,
                    summary.get('total_contents', 0),
                    summary.get('completed_contents', 0),
                    summary.get('total_score', 0),
                    summary.get('total_max_score', 0),
                    summary.get('overall_percentage', 0),
                    summary.get('total_time_spent', 0)
                )
                cursor.execute(insert_summary_query, summary_values)
            
            self.db_connection.commit()
            logger.debug(f"Saved H5P scores for user {user_id}, course {course_id}")
            return True
            
        except Error as e:
            logger.error(f"Error saving H5P scores: {e}")
            self.db_connection.rollback()
            return False
        finally:
            cursor.close()
    
    def fetch_h5p_scores(self, user_id: int, course_id: str) -> Optional[Dict]:
        """Fetch H5P scores từ API - KHÔNG encode course_id"""
        try:
            # H5P API không cần encode course_id, giữ nguyên
            url = f"{self.h5p_base_url}/scores/{user_id}/{course_id}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return data
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching H5P scores for user {user_id}: {e}")
            return None
    
    # ==================== VIDEO PROGRESS ====================
    
    def save_video_progress(self, user_id: int, course_id: str, video_data: Dict) -> bool:
        """Lưu video progress chi tiết và summary"""
        if not self.db_connection or not self.db_connection.is_connected():
            if not self.connect_db():
                return False
        
        try:
            cursor = self.db_connection.cursor()
            
            # Lưu chi tiết từng video
            videos = video_data.get('video_progress', [])
            if videos:
                insert_detail_query = """
                INSERT INTO video_progress (
                    user_id, course_id, content_id, content_title, progress_percent,
                    `current_time`, `duration`, status, folder_id, folder_name
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    progress_percent = VALUES(progress_percent),
                    `current_time` = VALUES(`current_time`),
                    `duration` = VALUES(`duration`),
                    status = VALUES(status),
                    folder_id = VALUES(folder_id),
                    folder_name = VALUES(folder_name)
                """
                
                for video_item in videos:
                    values = (
                        user_id,
                        course_id,
                        video_item.get('content_id'),
                        video_item.get('content_title'),
                        video_item.get('progress_percent', 0),
                        video_item.get('current_time', 0),
                        video_item.get('duration', 0),
                        video_item.get('status'),
                        video_item.get('folder_id'),
                        video_item.get('folder_name')
                    )
                    cursor.execute(insert_detail_query, values)
            
            # Lưu summary
            summary = video_data.get('summary', {})
            if summary:
                insert_summary_query = """
                INSERT INTO video_progress_summary (
                    user_id, course_id, total_videos, completed_videos,
                    in_progress_videos, not_started_videos, total_duration,
                    total_watched_time, overall_progress
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    total_videos = VALUES(total_videos),
                    completed_videos = VALUES(completed_videos),
                    in_progress_videos = VALUES(in_progress_videos),
                    not_started_videos = VALUES(not_started_videos),
                    total_duration = VALUES(total_duration),
                    total_watched_time = VALUES(total_watched_time),
                    overall_progress = VALUES(overall_progress),
                    updated_at = CURRENT_TIMESTAMP
                """
                
                summary_values = (
                    user_id,
                    course_id,
                    summary.get('total_videos', 0),
                    summary.get('completed_videos', 0),
                    summary.get('in_progress_videos', 0),
                    summary.get('not_started_videos', 0),
                    summary.get('total_duration', 0),
                    summary.get('total_watched_time', 0),
                    summary.get('overall_progress', 0)
                )
                cursor.execute(insert_summary_query, summary_values)
            
            self.db_connection.commit()
            logger.debug(f"Saved video progress for user {user_id}, course {course_id}")
            return True
            
        except Error as e:
            logger.error(f"Error saving video progress: {e}")
            self.db_connection.rollback()
            return False
        finally:
            cursor.close()
    
    def fetch_video_progress(self, user_id: int, course_id: str) -> Optional[Dict]:
        """Fetch video progress từ API - KHÔNG encode course_id"""
        try:
            # H5P API không cần encode course_id, giữ nguyên
            url = f"{self.h5p_base_url}/video-progress/{user_id}/{course_id}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return data
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching video progress for user {user_id}: {e}")
            return None

    # ==================== COMBINED PROGRESS ====================
    
    def fetch_combined_progress(self, user_id: int, course_id: str) -> Optional[Dict]:
        """Fetch combined progress từ API (thay thế dashboard) - KHÔNG encode course_id"""
        try:
            # H5P API không cần encode course_id, giữ nguyên
            url = f"{self.h5p_base_url}/combined-progress/{user_id}/{course_id}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return data
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching combined progress for user {user_id}: {e}")
            return None
    
    def save_combined_progress(self, user_id: int, course_id: str, combined_data: Dict) -> bool:
        """Lưu combined progress vào dashboard_summary (tương đương dashboard)"""
        if not self.db_connection or not self.db_connection.is_connected():
            if not self.connect_db():
                return False
        
        try:
            cursor = self.db_connection.cursor()
            
            overall = combined_data.get('overall', {})
            video_progress = combined_data.get('video_progress', {})
            scores = combined_data.get('scores', {})
            
            insert_query = """
            INSERT INTO dashboard_summary (
                user_id, course_id,
                overall_completion, total_items, completed_items, items_to_complete,
                h5p_total_contents, h5p_completed_contents, h5p_total_score,
                h5p_total_max_score, h5p_average_percentage, h5p_total_time_spent,
                video_total_videos, video_completed_videos, video_in_progress_videos,
                video_average_progress, folder_total_folders, folder_completed_folders,
                folder_average_percentage
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                overall_completion = VALUES(overall_completion),
                total_items = VALUES(total_items),
                completed_items = VALUES(completed_items),
                items_to_complete = VALUES(items_to_complete),
                h5p_total_contents = VALUES(h5p_total_contents),
                h5p_completed_contents = VALUES(h5p_completed_contents),
                h5p_total_score = VALUES(h5p_total_score),
                h5p_total_max_score = VALUES(h5p_total_max_score),
                h5p_average_percentage = VALUES(h5p_average_percentage),
                h5p_total_time_spent = VALUES(h5p_total_time_spent),
                video_total_videos = VALUES(video_total_videos),
                video_completed_videos = VALUES(video_completed_videos),
                video_in_progress_videos = VALUES(video_in_progress_videos),
                video_average_progress = VALUES(video_average_progress),
                folder_total_folders = VALUES(folder_total_folders),
                folder_completed_folders = VALUES(folder_completed_folders),
                folder_average_percentage = VALUES(folder_average_percentage),
                updated_at = CURRENT_TIMESTAMP
            """
            
            # Tính items_to_complete
            total_items = overall.get('total_items', 0)
            completed_items = overall.get('completed_items', 0)
            items_to_complete = max(0, total_items - completed_items)
            
            values = (
                user_id,
                course_id,
                overall.get('overall_completion', 0),
                total_items,
                completed_items,
                items_to_complete,
                scores.get('total_contents', 0),
                scores.get('completed_contents', 0),
                scores.get('total_score', 0),
                scores.get('total_max_score', 0),
                scores.get('average_percentage', 0),
                scores.get('total_time_spent', 0),
                video_progress.get('total_videos', 0),
                video_progress.get('completed_videos', 0),
                video_progress.get('in_progress_videos', 0),
                video_progress.get('average_progress', 0),
                0,  # folder_total_folders (không có trong combined-progress)
                0,  # folder_completed_folders
                0   # folder_average_percentage
            )
            
            cursor.execute(insert_query, values)
            self.db_connection.commit()
            logger.debug(f"Saved combined progress for user {user_id}, course {course_id}")
            return True
            
        except Error as e:
            logger.error(f"Error saving combined progress: {e}")
            self.db_connection.rollback()
            return False
        finally:
            cursor.close()

    # ==================== DASHBOARD (DEPRECATED - API không hoạt động) ====================
    
    def save_dashboard_summary(self, user_id: int, course_id: str, dashboard_data: Dict) -> bool:
        """Lưu dashboard summary"""
        if not self.db_connection or not self.db_connection.is_connected():
            if not self.connect_db():
                return False
        
        try:
            cursor = self.db_connection.cursor()
            
            overview = dashboard_data.get('overview', {})
            h5p_stats = dashboard_data.get('h5p_stats', {})
            video_stats = dashboard_data.get('video_stats', {})
            folder_stats = dashboard_data.get('folder_scores_stats', {})
            
            insert_query = """
            INSERT INTO dashboard_summary (
                user_id, course_id,
                overall_completion, total_items, completed_items, items_to_complete,
                h5p_total_contents, h5p_completed_contents, h5p_total_score,
                h5p_total_max_score, h5p_average_percentage, h5p_total_time_spent,
                video_total_videos, video_completed_videos, video_in_progress_videos,
                video_average_progress, folder_total_folders, folder_completed_folders,
                folder_average_percentage
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                overall_completion = VALUES(overall_completion),
                total_items = VALUES(total_items),
                completed_items = VALUES(completed_items),
                items_to_complete = VALUES(items_to_complete),
                h5p_total_contents = VALUES(h5p_total_contents),
                h5p_completed_contents = VALUES(h5p_completed_contents),
                h5p_total_score = VALUES(h5p_total_score),
                h5p_total_max_score = VALUES(h5p_total_max_score),
                h5p_average_percentage = VALUES(h5p_average_percentage),
                h5p_total_time_spent = VALUES(h5p_total_time_spent),
                video_total_videos = VALUES(video_total_videos),
                video_completed_videos = VALUES(video_completed_videos),
                video_in_progress_videos = VALUES(video_in_progress_videos),
                video_average_progress = VALUES(video_average_progress),
                folder_total_folders = VALUES(folder_total_folders),
                folder_completed_folders = VALUES(folder_completed_folders),
                folder_average_percentage = VALUES(folder_average_percentage),
                updated_at = CURRENT_TIMESTAMP
            """
            
            values = (
                user_id,
                course_id,
                overview.get('overall_completion', 0),
                overview.get('total_items', 0),
                overview.get('completed_items', 0),
                overview.get('items_to_complete', 0),
                h5p_stats.get('total_contents', 0),
                h5p_stats.get('completed_contents', 0),
                h5p_stats.get('total_score', 0),
                h5p_stats.get('total_max_score', 0),
                h5p_stats.get('average_percentage', 0),
                h5p_stats.get('total_time_spent', 0),
                video_stats.get('total_videos', 0),
                video_stats.get('completed_videos', 0),
                video_stats.get('in_progress_videos', 0),
                video_stats.get('average_video_progress', 0),
                folder_stats.get('total_folders', 0),
                folder_stats.get('completed_folders', 0),
                folder_stats.get('average_folder_percentage', 0)
            )
            
            cursor.execute(insert_query, values)
            self.db_connection.commit()
            logger.debug(f"Saved dashboard summary for user {user_id}, course {course_id}")
            return True
            
        except Error as e:
            logger.error(f"Error saving dashboard summary: {e}")
            self.db_connection.rollback()
            return False
        finally:
            cursor.close()
    
    def fetch_dashboard(self, user_id: int, course_id: str) -> Optional[Dict]:
        """Fetch dashboard từ API - KHÔNG encode course_id"""
        try:
            # H5P API không cần encode course_id, giữ nguyên
            url = f"{self.h5p_base_url}/dashboard/{user_id}/{course_id}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return data
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching dashboard for user {user_id}: {e}")
            return None
    
    
    # ==================== MOOC EXPORT APIs ====================
    
    def save_mooc_grades(self, course_id: str, grades_data: Dict) -> bool:
        """Lưu MOOC grades vào bảng mooc_grades"""
        if not self.db_connection or not self.db_connection.is_connected():
            if not self.connect_db():
                return False
        
        try:
            cursor = self.db_connection.cursor()
            
            students = grades_data.get('students', [])
            if not students:
                logger.warning(f"No students data in grades response for course {course_id}")
                return False
            
            insert_query = """
            INSERT INTO mooc_grades (
                user_id, course_id, username, email, full_name,
                percent_grade, grade_percentage, letter_grade, is_passed
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                email = VALUES(email),
                full_name = VALUES(full_name),
                percent_grade = VALUES(percent_grade),
                grade_percentage = VALUES(grade_percentage),
                letter_grade = VALUES(letter_grade),
                is_passed = VALUES(is_passed),
                updated_at = CURRENT_TIMESTAMP
            """
            
            saved_count = 0
            for student in students:
                # Map letter_grade: "Pass" if is_passed=true, "" if is_passed=false
                is_passed = student.get('is_passed', False)
                letter_grade = "Pass" if is_passed else ""
                
                values = (
                    student.get('user_id'),
                    course_id,
                    student.get('username'),
                    student.get('email'),
                    student.get('full_name'),
                    student.get('percent_grade', 0),
                    student.get('grade_percentage', 0),
                    letter_grade,
                    is_passed
                )
                
                cursor.execute(insert_query, values)
                saved_count += 1
            
            self.db_connection.commit()
            logger.info(f"Saved {saved_count} MOOC grades for course {course_id}")
            return True
            
        except Error as e:
            logger.error(f"Error saving MOOC grades: {e}")
            self.db_connection.rollback()
            return False
        finally:
            cursor.close()
    
    def fetch_mooc_grades(self, course_id: str) -> Optional[Dict]:
        """Fetch MOOC grades từ Export API"""
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/export/student-grades/{encoded_course_id}/"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return data
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching MOOC grades for course {course_id}: {e}")
            return None
    
    def save_mooc_progress(self, course_id: str, progress_data: Dict) -> bool:
        """Lưu MOOC progress vào bảng mooc_progress"""
        if not self.db_connection or not self.db_connection.is_connected():
            if not self.connect_db():
                return False
        
        try:
            cursor = self.db_connection.cursor()
            
            students = progress_data.get('students', [])
            if not students:
                logger.warning(f"No students data in progress response for course {course_id}")
                return False
            
            insert_query = """
            INSERT INTO mooc_progress (
                user_id, course_id, current_chapter, current_section, current_unit,
                completion_rate, last_activity
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                current_chapter = VALUES(current_chapter),
                current_section = VALUES(current_section),
                current_unit = VALUES(current_unit),
                completion_rate = VALUES(completion_rate),
                last_activity = VALUES(last_activity),
                updated_at = CURRENT_TIMESTAMP
            """
            
            saved_count = 0
            for student in students:
                last_activity = self.parse_datetime(student.get('last_activity'))
                
                values = (
                    student.get('user_id'),
                    course_id,
                    student.get('current_chapter'),
                    student.get('current_section'),
                    student.get('current_unit'),
                    student.get('completion_rate', 0),
                    last_activity
                )
                
                cursor.execute(insert_query, values)
                saved_count += 1
            
            self.db_connection.commit()
            logger.info(f"Saved {saved_count} MOOC progress records for course {course_id}")
            return True
            
        except Error as e:
            logger.error(f"Error saving MOOC progress: {e}")
            self.db_connection.rollback()
            return False
        finally:
            cursor.close()
    
    def fetch_mooc_progress(self, course_id: str) -> Optional[Dict]:
        """Fetch MOOC progress từ Export API"""
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/export/student-progress/{encoded_course_id}/"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return data
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching MOOC progress for course {course_id}: {e}")
            return None
    
    def save_mooc_discussions(self, course_id: str, discussions_data: Dict) -> bool:
        """Lưu MOOC discussions vào bảng mooc_discussions"""
        if not self.db_connection or not self.db_connection.is_connected():
            if not self.connect_db():
                return False
        
        try:
            cursor = self.db_connection.cursor()
            
            students = discussions_data.get('students', [])
            if not students:
                logger.warning(f"No students data in discussions response for course {course_id}")
                return False
            
            insert_query = """
            INSERT INTO mooc_discussions (
                user_id, course_id, username, email, full_name,
                threads_count, comments_count, total_interactions,
                questions_count, total_upvotes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                email = VALUES(email),
                full_name = VALUES(full_name),
                threads_count = VALUES(threads_count),
                comments_count = VALUES(comments_count),
                total_interactions = VALUES(total_interactions),
                questions_count = VALUES(questions_count),
                total_upvotes = VALUES(total_upvotes),
                updated_at = CURRENT_TIMESTAMP
            """
            
            saved_count = 0
            for student in students:
                values = (
                    student.get('user_id'),
                    course_id,
                    student.get('username'),
                    student.get('email'),
                    student.get('full_name'),
                    student.get('threads_count', 0),
                    student.get('comments_count', 0),
                    student.get('total_interactions', 0),
                    student.get('questions_count', 0),
                    student.get('total_upvotes', 0)
                )
                
                cursor.execute(insert_query, values)
                saved_count += 1
            
            self.db_connection.commit()
            logger.info(f"Saved {saved_count} MOOC discussion records for course {course_id}")
            return True
            
        except Error as e:
            logger.error(f"Error saving MOOC discussions: {e}")
            self.db_connection.rollback()
            return False
        finally:
            cursor.close()
    
    def fetch_mooc_discussions(self, course_id: str) -> Optional[Dict]:
        """Fetch MOOC discussions từ Export API"""
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/export/student-discussions/{encoded_course_id}/"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return data
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching MOOC discussions for course {course_id}: {e}")
            return None
    
    def fetch_mooc_complete_data(self, course_id: str) -> Optional[Dict]:
        """Fetch complete student data (grades + progress + discussions) từ Export API"""
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/export/complete-student-data/{encoded_course_id}/"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return data
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching MOOC complete data for course {course_id}: {e}")
            return None
    
    def fetch_all_mooc_export_data(self, course_id: str) -> Dict:
        """Fetch tất cả MOOC Export data (grades, progress, discussions) cho một course"""
        logger.info(f"Fetching all MOOC Export data for course {course_id}...")
        
        results = {
            "grades": False,
            "progress": False,
            "discussions": False
        }
        
        # Fetch và save grades
        logger.info("Fetching MOOC grades...")
        grades_data = self.fetch_mooc_grades(course_id)
        if grades_data:
            results["grades"] = self.save_mooc_grades(course_id, grades_data)
        
        time.sleep(0.5)  # Rate limiting
        
        # Fetch và save progress
        logger.info("Fetching MOOC progress...")
        progress_data = self.fetch_mooc_progress(course_id)
        if progress_data:
            results["progress"] = self.save_mooc_progress(course_id, progress_data)
        
        time.sleep(0.5)  # Rate limiting
        
        # Fetch và save discussions
        logger.info("Fetching MOOC discussions...")
        discussions_data = self.fetch_mooc_discussions(course_id)
        if discussions_data:
            results["discussions"] = self.save_mooc_discussions(course_id, discussions_data)
        
        time.sleep(0.5)  # Rate limiting
        
        # OPTION 2: Fetch và store course-level benchmarks
        logger.info("Fetching course-level benchmarks for comparative features...")
        self.fetch_and_store_course_benchmarks(course_id)
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"MOOC Export data fetch completed: {success_count}/3 successful")
        
        return results
    
    # ==================== OPTION 2: ADVANCED STATS APIs ====================
    
    def fetch_and_store_course_benchmarks(self, course_id: str) -> bool:
        """
        Fetch all Advanced Stats APIs and store course-level benchmarks
        This enables comparative features for Option 2
        """
        try:
            logger.info("Fetching course-level benchmarks from Advanced Stats APIs...")
            
            # Fetch Activity Stats
            activity_stats = self.fetch_activity_stats_summary(course_id)
            assessment_stats = self.fetch_assessment_stats_summary(course_id)
            progress_stats = self.fetch_progress_stats_summary(course_id)
            
            # Extract benchmarks
            benchmarks = {
                'course_id': course_id,
                'activity_avg_score': 0,
                'activity_total_activities': 0,
                'activity_avg_per_user': 0,
                'assessment_avg_score': 0,
                'assessment_avg_attempts': 0,
                'assessment_pass_rate': 0,
                'progress_avg_completion': 0,
                'progress_median_completion': 0,
                'progress_completion_rate': 0,
                'video_avg_completion': 0,
                'video_avg_watch_time': 0,
                'discussion_avg_interactions': 0,
                'discussion_participation_rate': 0,
                'total_students': 0,
                'active_students': 0
            }
            
            # Parse Activity Stats
            if activity_stats and activity_stats.get('success'):
                summary = activity_stats.get('summary', {})
                benchmarks['activity_avg_score'] = summary.get('avg_score', 0)
                benchmarks['activity_total_activities'] = summary.get('total_activities', 0)
                benchmarks['active_students'] = summary.get('total_active_users', 0)
                if benchmarks['active_students'] > 0:
                    benchmarks['activity_avg_per_user'] = round(
                        benchmarks['activity_total_activities'] / benchmarks['active_students'], 2
                    )
            
            # Parse Assessment Stats
            if assessment_stats and assessment_stats.get('success'):
                summary = assessment_stats.get('summary', {})
                benchmarks['assessment_avg_score'] = summary.get('avg_score', 0)
                benchmarks['total_students'] = summary.get('unique_students', 0)
                total_attempts = summary.get('total_attempts', 0)
                if benchmarks['total_students'] > 0:
                    benchmarks['assessment_avg_attempts'] = round(
                        total_attempts / benchmarks['total_students'], 2
                    )
            
            # Parse Progress Stats
            if progress_stats and progress_stats.get('success'):
                summary = progress_stats.get('summary', {})
                benchmarks['progress_avg_completion'] = summary.get('avg_progress', 0)
                benchmarks['progress_completion_rate'] = summary.get('completion_rate', 0)
                benchmarks['total_students'] = max(
                    benchmarks['total_students'], 
                    summary.get('total_students', 0)
                )
            
            # Store benchmarks to database
            cursor = self.db_connection.cursor()
            
            insert_query = """
            INSERT INTO course_stats_benchmarks (
                course_id, 
                activity_avg_score, activity_total_activities, activity_avg_per_user,
                assessment_avg_score, assessment_avg_attempts, assessment_pass_rate,
                progress_avg_completion, progress_median_completion, progress_completion_rate,
                video_avg_completion, video_avg_watch_time,
                discussion_avg_interactions, discussion_participation_rate,
                total_students, active_students
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                activity_avg_score = VALUES(activity_avg_score),
                activity_total_activities = VALUES(activity_total_activities),
                activity_avg_per_user = VALUES(activity_avg_per_user),
                assessment_avg_score = VALUES(assessment_avg_score),
                assessment_avg_attempts = VALUES(assessment_avg_attempts),
                progress_avg_completion = VALUES(progress_avg_completion),
                progress_completion_rate = VALUES(progress_completion_rate),
                total_students = VALUES(total_students),
                active_students = VALUES(active_students),
                updated_at = CURRENT_TIMESTAMP
            """
            
            values = (
                benchmarks['course_id'],
                benchmarks['activity_avg_score'],
                benchmarks['activity_total_activities'],
                benchmarks['activity_avg_per_user'],
                benchmarks['assessment_avg_score'],
                benchmarks['assessment_avg_attempts'],
                benchmarks['assessment_pass_rate'],
                benchmarks['progress_avg_completion'],
                benchmarks['progress_median_completion'],
                benchmarks['progress_completion_rate'],
                benchmarks['video_avg_completion'],
                benchmarks['video_avg_watch_time'],
                benchmarks['discussion_avg_interactions'],
                benchmarks['discussion_participation_rate'],
                benchmarks['total_students'],
                benchmarks['active_students']
            )
            
            cursor.execute(insert_query, values)
            self.db_connection.commit()
            cursor.close()
            
            logger.info(f"Course benchmarks stored: {benchmarks['total_students']} students, avg completion: {benchmarks['progress_avg_completion']:.2f}%")
            return True
            
        except Exception as e:
            logger.error(f"Error fetching/storing course benchmarks: {e}")
            if self.db_connection:
                self.db_connection.rollback()
            return False
    
    def fetch_activity_stats_summary(self, course_id: str) -> Optional[Dict]:
        """Fetch Activity Statistics from Advanced Stats API"""
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/stats/activity/{encoded_course_id}/"
            
            params = {'days': 90, 'group_by': 'day'}
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"Activity stats fetched")
                    return data
            else:
                logger.warning(f"Activity stats API returned {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching activity stats: {e}")
        return None
    
    def fetch_assessment_stats_summary(self, course_id: str) -> Optional[Dict]:
        """Fetch Assessment Statistics from Advanced Stats API"""
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/stats/assessment/{encoded_course_id}/"
            
            params = {'days': 90}
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"Assessment stats fetched")
                    return data
            else:
                logger.warning(f"Assessment stats API returned {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching assessment stats: {e}")
        return None
    
    def fetch_progress_stats_summary(self, course_id: str) -> Optional[Dict]:
        """Fetch Progress Statistics from Advanced Stats API"""
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/stats/progress/{encoded_course_id}/"
            
            params = {'days': 90}
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"Progress stats fetched")
                    return data
            else:
                logger.warning(f"Progress stats API returned {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching progress stats: {e}")
        return None
    
    def get_course_benchmarks(self, course_id: str) -> Optional[Dict]:
        """Retrieve course benchmarks from database"""
        try:
            cursor = self.db_connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM course_stats_benchmarks
                WHERE course_id = %s
            """, (course_id,))
            benchmarks = cursor.fetchone()
            cursor.close()
            return benchmarks
        except Exception as e:
            logger.error(f"Error retrieving course benchmarks: {e}")
            return None
    
    def calculate_comparative_features(
        self, 
        user_metrics: Dict, 
        course_benchmarks: Dict
    ) -> Dict:
        """
        Calculate comparative features (Option 2)
        Compare user metrics against course benchmarks
        """
        features = {
            'relative_to_course_problem_score': 0,
            'relative_to_course_completion': 0,
            'relative_to_course_video_completion': 0,
            'relative_to_course_discussion': 0,
            'performance_percentile': 50,  # Default to median
            'is_below_course_average': 0,
            'is_top_performer': 0,
            'is_bottom_performer': 0
        }
        
        try:
            # Relative to course scores
            user_problem_score = user_metrics.get('problem_avg_score', 0)
            course_avg_problem = course_benchmarks.get('assessment_avg_score', 0)
            if course_avg_problem > 0:
                features['relative_to_course_problem_score'] = round(
                    user_problem_score - course_avg_problem, 2
                )
            
            # Relative completion
            user_completion = user_metrics.get('mooc_completion_rate', 0)
            course_avg_completion = course_benchmarks.get('progress_avg_completion', 0)
            if course_avg_completion > 0:
                features['relative_to_course_completion'] = round(
                    user_completion - course_avg_completion, 2
                )
            
            # Relative video completion
            user_video_completion = user_metrics.get('video_completion_rate', 0)
            course_avg_video = course_benchmarks.get('video_avg_completion', 0) or user_video_completion
            features['relative_to_course_video_completion'] = round(
                user_video_completion - course_avg_video, 2
            )
            
            # Relative discussion
            user_discussion = user_metrics.get('discussion_total_interactions', 0)
            course_avg_discussion = course_benchmarks.get('discussion_avg_interactions', 0)
            features['relative_to_course_discussion'] = int(
                user_discussion - course_avg_discussion
            )
            
            # Calculate composite performance score for percentile
            # Weighted: 40% completion, 30% problem score, 30% engagement
            user_score = (
                user_completion * 0.4 +
                user_problem_score * 0.3 +
                (user_video_completion + min(user_discussion * 2, 100)) / 2 * 0.3
            )
            
            course_avg_score = (
                course_avg_completion * 0.4 +
                course_avg_problem * 0.3 +
                course_avg_video * 0.3
            )
            
            # Estimate percentile based on deviation from mean
            # Simple heuristic: assume normal distribution
            if course_avg_score > 0:
                deviation = (user_score - course_avg_score) / course_avg_score
                # Map deviation to percentile (rough approximation)
                if deviation > 0.5:
                    percentile = 90  # Top 10%
                elif deviation > 0.25:
                    percentile = 75  # Top quartile
                elif deviation > 0:
                    percentile = 60  # Above average
                elif deviation > -0.25:
                    percentile = 40  # Below average
                elif deviation > -0.5:
                    percentile = 25  # Bottom quartile
                else:
                    percentile = 10  # Bottom 10%
                
                features['performance_percentile'] = percentile
            
            # Set flags
            features['is_below_course_average'] = 1 if user_score < course_avg_score else 0
            features['is_top_performer'] = 1 if features['performance_percentile'] >= 75 else 0
            features['is_bottom_performer'] = 1 if features['performance_percentile'] <= 25 else 0
            
        except Exception as e:
            logger.error(f"Error calculating comparative features: {e}")
        
        return features
    
    # ==================== AGGREGATE RAW DATA ====================
    
    def aggregate_raw_data(self, user_id: int, course_id: str, batch_id: Optional[str] = None) -> bool:
        """Aggregate tất cả data từ các bảng vào raw_data"""
        if not self.db_connection or not self.db_connection.is_connected():
            if not self.connect_db():
                return False
        
        try:
            cursor = self.db_connection.cursor(dictionary=True)
            
            # Lấy enrollment data
            cursor.execute("""
                SELECT created, mode, is_active
                FROM enrollments
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
            """, (user_id, course_id))
            enrollment = cursor.fetchone()
            
            # Lấy H5P summary
            cursor.execute("""
                SELECT total_contents, completed_contents, total_score, total_max_score,
                       overall_percentage, total_time_spent
                FROM h5p_scores_summary
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
            """, (user_id, course_id))
            h5p_summary = cursor.fetchone()
            
            # Lấy video summary
            cursor.execute("""
                SELECT total_videos, completed_videos, in_progress_videos,
                       total_duration, total_watched_time, overall_progress
                FROM video_progress_summary
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
            """, (user_id, course_id))
            video_summary = cursor.fetchone()
            
            # Lấy dashboard summary
            cursor.execute("""
                SELECT overall_completion, total_items, completed_items
                FROM dashboard_summary
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
            """, (user_id, course_id))
            dashboard = cursor.fetchone()
            
            # Lấy MOOC grades
            cursor.execute("""
                SELECT grade_percentage, letter_grade, is_passed
                FROM mooc_grades
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
            """, (user_id, course_id))
            mooc_grades = cursor.fetchone()
            
            # Lấy MOOC progress
            cursor.execute("""
                SELECT current_chapter, current_section, current_unit,
                       completion_rate, last_activity
                FROM mooc_progress
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
            """, (user_id, course_id))
            mooc_progress = cursor.fetchone()
            
            # Lấy MOOC discussions
            cursor.execute("""
                SELECT threads_count, comments_count, total_interactions,
                       questions_count, total_upvotes
                FROM mooc_discussions
                WHERE user_id = %s AND course_id = %s
                LIMIT 1
            """, (user_id, course_id))
            mooc_discussions = cursor.fetchone()
            
            # Tính toán các features
            enrollment_mode = enrollment['mode'] if enrollment else None
            is_active = enrollment['is_active'] if enrollment else True
            
            # Tính weeks_since_enrollment từ created date
            weeks_since_enrollment = 0
            if enrollment and enrollment.get('created'):
                created_date = self.parse_datetime(enrollment['created'])
                if created_date:
                    delta = datetime.now() - (created_date.replace(tzinfo=None) if created_date.tzinfo else created_date)
                    weeks_since_enrollment = round(delta.days / 7.0, 2)
            
            # Progress features - tính từ dashboard hoặc từ summaries
            if dashboard and dashboard.get('overall_completion'):
                progress_percent = dashboard['overall_completion']
                overall_completion = dashboard['overall_completion']
                completed_blocks = dashboard.get('completed_items', 0)
                total_blocks = dashboard.get('total_items', 0)
            else:
                # Tính từ h5p và video summaries nếu không có dashboard
                h5p_completed = h5p_summary['completed_contents'] if h5p_summary and h5p_summary.get('completed_contents') else 0
                h5p_total = h5p_summary['total_contents'] if h5p_summary and h5p_summary.get('total_contents') else 0
                video_completed = video_summary['completed_videos'] if video_summary and video_summary.get('completed_videos') else 0
                video_total = video_summary['total_videos'] if video_summary and video_summary.get('total_videos') else 0
                
                completed_blocks = h5p_completed + video_completed
                total_blocks = h5p_total + video_total
                
                if total_blocks > 0:
                    overall_completion = round((completed_blocks / total_blocks) * 100, 2)
                    progress_percent = overall_completion
                else:
                    progress_percent = 0
                    overall_completion = 0
            
            # H5P features
            h5p_total_contents = h5p_summary['total_contents'] if h5p_summary and h5p_summary.get('total_contents') else 0
            h5p_completed_contents = h5p_summary['completed_contents'] if h5p_summary and h5p_summary.get('completed_contents') else 0
            h5p_total_score = h5p_summary['total_score'] if h5p_summary and h5p_summary.get('total_score') else 0
            h5p_total_max_score = h5p_summary['total_max_score'] if h5p_summary and h5p_summary.get('total_max_score') else 0
            h5p_overall_percentage = h5p_summary['overall_percentage'] if h5p_summary and h5p_summary.get('overall_percentage') else 0
            h5p_total_time_spent = h5p_summary['total_time_spent'] if h5p_summary and h5p_summary.get('total_time_spent') else 0
            h5p_completion_rate = round((h5p_completed_contents / h5p_total_contents * 100), 2) if h5p_total_contents > 0 else 0
            
            # Video features
            video_total_videos = video_summary['total_videos'] if video_summary and video_summary.get('total_videos') else 0
            video_completed_videos = video_summary['completed_videos'] if video_summary and video_summary.get('completed_videos') else 0
            video_in_progress_videos = video_summary['in_progress_videos'] if video_summary and video_summary.get('in_progress_videos') else 0
            video_total_duration = video_summary['total_duration'] if video_summary and video_summary.get('total_duration') else 0
            video_total_watched_time = video_summary['total_watched_time'] if video_summary and video_summary.get('total_watched_time') else 0
            video_completion_rate = round((video_completed_videos / video_total_videos * 100), 2) if video_total_videos > 0 else 0
            video_watch_rate = round((video_total_watched_time / video_total_duration * 100), 2) if video_total_duration > 0 else 0
            
            # MOOC Grades features
            mooc_grade_percentage = mooc_grades['grade_percentage'] if mooc_grades and mooc_grades.get('grade_percentage') else 0
            mooc_letter_grade = mooc_grades['letter_grade'] if mooc_grades and mooc_grades.get('letter_grade') else ""
            mooc_is_passed = mooc_grades['is_passed'] if mooc_grades and mooc_grades.get('is_passed') is not None else None
            
            # MOOC Progress features
            current_chapter = mooc_progress['current_chapter'] if mooc_progress and mooc_progress.get('current_chapter') else None
            current_section = mooc_progress['current_section'] if mooc_progress and mooc_progress.get('current_section') else None
            current_unit = mooc_progress['current_unit'] if mooc_progress and mooc_progress.get('current_unit') else None
            mooc_completion_rate = mooc_progress['completion_rate'] if mooc_progress and mooc_progress.get('completion_rate') else 0
            last_activity = mooc_progress['last_activity'] if mooc_progress and mooc_progress.get('last_activity') else None
            
            # Calculate days_since_last_activity
            days_since_last_activity = 999
            if last_activity:
                last_activity_dt = last_activity if isinstance(last_activity, datetime) else self.parse_datetime(str(last_activity))
                if last_activity_dt:
                    delta = datetime.now() - (last_activity_dt.replace(tzinfo=None) if last_activity_dt.tzinfo else last_activity_dt)
                    days_since_last_activity = delta.days
            
            # MOOC Discussion features
            discussion_threads_count = mooc_discussions['threads_count'] if mooc_discussions and mooc_discussions.get('threads_count') else 0
            discussion_comments_count = mooc_discussions['comments_count'] if mooc_discussions and mooc_discussions.get('comments_count') else 0
            discussion_total_interactions = mooc_discussions['total_interactions'] if mooc_discussions and mooc_discussions.get('total_interactions') else 0
            discussion_questions_count = mooc_discussions['questions_count'] if mooc_discussions and mooc_discussions.get('questions_count') else 0
            discussion_total_upvotes = mooc_discussions['total_upvotes'] if mooc_discussions and mooc_discussions.get('total_upvotes') else 0
            
            # Quiz features (từ H5P)
            quiz_attempts = h5p_completed_contents
            quiz_avg_score = h5p_overall_percentage
            quiz_completion_rate = h5p_completion_rate
            
            # Target labels và predictions
            
            # is_passed: Lấy từ MOOC grades API
            # - NULL: Chưa hoàn thành khóa học (không dùng để train)
            # - TRUE: Pass (dùng để train)
            # - FALSE: Fail (dùng để train)
            is_passed = mooc_is_passed
            
            # is_dropout: Tự động label dựa trên activity
            # - TRUE: Coi là dropout nếu không active VÀ không hoạt động > 30 ngày
            # - FALSE: Còn active hoặc hoạt động gần đây (< 7 ngày)
            # - NULL: Không chắc chắn (7-30 ngày không hoạt động)
            is_dropout = None
            if not is_active and days_since_last_activity > 30:
                is_dropout = True
            elif is_active or days_since_last_activity < 7:
                is_dropout = False
            # Else: NULL (không chắc chắn, 7-30 ngày)
            
            # Risk scores: Để NULL, sẽ được AI model predict sau
            fail_risk_score = None
            
            # OPTION 2: Calculate comparative features
            course_benchmarks = self.get_course_benchmarks(course_id)
            
            # Prepare user metrics for comparison
            user_metrics = {
                'problem_avg_score': quiz_avg_score,  # Using quiz as proxy for problem
                'mooc_completion_rate': mooc_completion_rate,
                'video_completion_rate': video_completion_rate,
                'discussion_total_interactions': discussion_total_interactions
            }
            
            # Calculate comparative features
            if course_benchmarks:
                comparative_features = self.calculate_comparative_features(
                    user_metrics, 
                    course_benchmarks
                )
            else:
                # Default values if no benchmarks available
                comparative_features = {
                    'relative_to_course_problem_score': 0,
                    'relative_to_course_completion': 0,
                    'relative_to_course_video_completion': 0,
                    'relative_to_course_discussion': 0,
                    'performance_percentile': 50,
                    'is_below_course_average': 0,
                    'is_top_performer': 0,
                    'is_bottom_performer': 0
                }
            
            # Insert vào raw_data
            insert_query = """
            INSERT INTO raw_data (
                user_id, course_id,
                enrollment_mode, is_active, weeks_since_enrollment,
                mooc_grade_percentage, mooc_letter_grade, mooc_is_passed,
                progress_percent, current_chapter, current_section, current_unit,
                mooc_completion_rate, overall_completion, completed_blocks, total_blocks,
                last_activity, days_since_last_activity,
                h5p_total_contents, h5p_completed_contents, h5p_total_score, h5p_total_max_score,
                h5p_overall_percentage, h5p_total_time_spent, h5p_completion_rate,
                video_total_videos, video_completed_videos, video_in_progress_videos,
                video_total_duration, video_total_watched_time, video_completion_rate, video_watch_rate,
                quiz_attempts, quiz_avg_score, quiz_completion_rate,
                discussion_threads_count, discussion_comments_count, discussion_total_interactions,
                discussion_questions_count, discussion_total_upvotes,
                relative_to_course_problem_score, relative_to_course_completion,
                relative_to_course_video_completion, relative_to_course_discussion,
                performance_percentile, is_below_course_average,
                is_top_performer, is_bottom_performer,
                is_dropout, is_passed, fail_risk_score, extraction_batch_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                enrollment_mode = VALUES(enrollment_mode),
                is_active = VALUES(is_active),
                weeks_since_enrollment = VALUES(weeks_since_enrollment),
                mooc_grade_percentage = VALUES(mooc_grade_percentage),
                mooc_letter_grade = VALUES(mooc_letter_grade),
                mooc_is_passed = VALUES(mooc_is_passed),
                progress_percent = VALUES(progress_percent),
                current_chapter = VALUES(current_chapter),
                current_section = VALUES(current_section),
                current_unit = VALUES(current_unit),
                mooc_completion_rate = VALUES(mooc_completion_rate),
                overall_completion = VALUES(overall_completion),
                completed_blocks = VALUES(completed_blocks),
                total_blocks = VALUES(total_blocks),
                last_activity = VALUES(last_activity),
                days_since_last_activity = VALUES(days_since_last_activity),
                h5p_total_contents = VALUES(h5p_total_contents),
                h5p_completed_contents = VALUES(h5p_completed_contents),
                h5p_total_score = VALUES(h5p_total_score),
                h5p_total_max_score = VALUES(h5p_total_max_score),
                h5p_overall_percentage = VALUES(h5p_overall_percentage),
                h5p_total_time_spent = VALUES(h5p_total_time_spent),
                h5p_completion_rate = VALUES(h5p_completion_rate),
                video_total_videos = VALUES(video_total_videos),
                video_completed_videos = VALUES(video_completed_videos),
                video_in_progress_videos = VALUES(video_in_progress_videos),
                video_total_duration = VALUES(video_total_duration),
                video_total_watched_time = VALUES(video_total_watched_time),
                video_completion_rate = VALUES(video_completion_rate),
                video_watch_rate = VALUES(video_watch_rate),
                quiz_attempts = VALUES(quiz_attempts),
                quiz_avg_score = VALUES(quiz_avg_score),
                quiz_completion_rate = VALUES(quiz_completion_rate),
                discussion_threads_count = VALUES(discussion_threads_count),
                discussion_comments_count = VALUES(discussion_comments_count),
                discussion_total_interactions = VALUES(discussion_total_interactions),
                discussion_questions_count = VALUES(discussion_questions_count),
                discussion_total_upvotes = VALUES(discussion_total_upvotes),
                relative_to_course_problem_score = VALUES(relative_to_course_problem_score),
                relative_to_course_completion = VALUES(relative_to_course_completion),
                relative_to_course_video_completion = VALUES(relative_to_course_video_completion),
                relative_to_course_discussion = VALUES(relative_to_course_discussion),
                performance_percentile = VALUES(performance_percentile),
                is_below_course_average = VALUES(is_below_course_average),
                is_top_performer = VALUES(is_top_performer),
                is_bottom_performer = VALUES(is_bottom_performer),
                is_dropout = VALUES(is_dropout),
                is_passed = VALUES(is_passed),
                fail_risk_score = VALUES(fail_risk_score),
                extraction_batch_id = VALUES(extraction_batch_id),
                extracted_at = CURRENT_TIMESTAMP
            """
            
            values = (
                user_id, course_id,
                enrollment_mode, is_active, weeks_since_enrollment,
                mooc_grade_percentage, mooc_letter_grade, mooc_is_passed,
                progress_percent, current_chapter, current_section, current_unit,
                mooc_completion_rate, overall_completion, completed_blocks, total_blocks,
                last_activity, days_since_last_activity,
                h5p_total_contents, h5p_completed_contents, h5p_total_score, h5p_total_max_score,
                h5p_overall_percentage, h5p_total_time_spent, h5p_completion_rate,
                video_total_videos, video_completed_videos, video_in_progress_videos,
                video_total_duration, video_total_watched_time, video_completion_rate, video_watch_rate,
                quiz_attempts, quiz_avg_score, quiz_completion_rate,
                discussion_threads_count, discussion_comments_count, discussion_total_interactions,
                discussion_questions_count, discussion_total_upvotes,
                comparative_features['relative_to_course_problem_score'],
                comparative_features['relative_to_course_completion'],
                comparative_features['relative_to_course_video_completion'],
                comparative_features['relative_to_course_discussion'],
                comparative_features['performance_percentile'],
                comparative_features['is_below_course_average'],
                comparative_features['is_top_performer'],
                comparative_features['is_bottom_performer'],
                is_dropout, is_passed, fail_risk_score, batch_id
            )
            
            cursor.execute(insert_query, values)
            self.db_connection.commit()
            logger.debug(f"Aggregated raw_data for user {user_id}, course {course_id}")
            return True
            
        except Error as e:
            logger.error(f"Error aggregating raw_data: {e}")
            self.db_connection.rollback()
            return False
        finally:
            cursor.close()
    
    def aggregate_all_raw_data(self, course_id: str, batch_id: Optional[str] = None) -> Dict:
        """Aggregate raw_data cho tất cả users trong course"""
        if not self.db_connection or not self.db_connection.is_connected():
            if not self.connect_db():
                return {"success": False, "message": "Database connection failed"}
        
        try:
            cursor = self.db_connection.cursor()
            
            # Lấy danh sách user_ids từ enrollments
            cursor.execute("""
                SELECT DISTINCT user_id FROM enrollments WHERE course_id = %s
            """, (course_id,))
            user_ids = [row[0] for row in cursor.fetchall()]
            
            if not user_ids:
                return {"success": False, "message": "No users found"}
            
            logger.info(f"Aggregating raw_data for {len(user_ids)} users...")
            
            success_count = 0
            failed_count = 0
            
            for user_id in user_ids:
                if self.aggregate_raw_data(user_id, course_id, batch_id):
                    success_count += 1
                else:
                    failed_count += 1
            
            logger.info(f"Aggregation completed! Success: {success_count}, Failed: {failed_count}")
            return {
                "success": True,
                "total_users": len(user_ids),
                "success_count": success_count,
                "failed_count": failed_count
            }
            
        except Error as e:
            logger.error(f"Error in aggregate_all_raw_data: {e}")
            return {"success": False, "message": str(e)}
        finally:
            cursor.close()

    # ==================== FETCH ALL DATA FOR USER ====================
    
    def fetch_user_data(self, user_id: int, course_id: str, delay: float = 0.5) -> bool:
        """Fetch tất cả data cho một user"""
        success = True
        
        # Fetch H5P scores
        logger.info(f"Fetching H5P scores for user {user_id}...")
        h5p_scores = self.fetch_h5p_scores(user_id, course_id)
        if h5p_scores:
            self.save_h5p_scores(user_id, course_id, h5p_scores)
        else:
            success = False
        time.sleep(delay)
        
        # Fetch video progress
        logger.info(f"Fetching video progress for user {user_id}...")
        video_progress = self.fetch_video_progress(user_id, course_id)
        if video_progress:
            self.save_video_progress(user_id, course_id, video_progress)
        else:
            success = False
        time.sleep(delay)
        
        # Fetch combined-progress (thay thế dashboard - API dashboard không hoạt động)
        logger.info(f"Fetching combined progress for user {user_id}...")
        combined_progress = self.fetch_combined_progress(user_id, course_id)
        if combined_progress:
            self.save_combined_progress(user_id, course_id, combined_progress)
        else:
            # Fallback: thử fetch dashboard (nếu có)
            logger.debug(f"Combined progress failed, trying dashboard API...")
            dashboard = self.fetch_dashboard(user_id, course_id)
            if dashboard:
                self.save_dashboard_summary(user_id, course_id, dashboard)
            else:
                logger.warning(f"Both combined-progress and dashboard APIs failed for user {user_id}. Will calculate from summaries.")
                success = False  # Không fail hoàn toàn, vì có thể tính từ summaries
        time.sleep(delay)
        
        return success
    
    def fetch_all_course_data(self, course_id: str, delay: float = 0.5, max_users: Optional[int] = None, aggregate: bool = True) -> Dict:
        """Fetch tất cả data cho một course"""
        logger.info(f"Starting to fetch all data for course {course_id}")
        
        # Bước 1: Fetch enrollments
        logger.info("Step 1: Fetching enrollments...")
        user_ids = self.fetch_mooc_course_students(course_id)
        
        if not user_ids:
            logger.error("No users found in course")
            return {"success": False, "message": "No users found"}
        
        # Bước 1.5: Fetch course details (start/end date) và cập nhật vào enrollments
        logger.info("Step 1.5: Fetching course details (start/end dates)...")
        course_info_success = self.fetch_and_update_course_info(course_id)
        if course_info_success:
            logger.info("Course info updated successfully!")
        else:
            logger.warning("Could not update course info - continuing without it")
        
        if max_users:
            user_ids = user_ids[:max_users]
            logger.info(f"Limiting to {max_users} users for testing")
        
        total_users = len(user_ids)
        logger.info(f"Found {total_users} users.")
        
        # Bước 2: Fetch MOOC Export data (course-level APIs)
        logger.info("Step 2: Fetching MOOC Export data (grades, progress, discussions)...")
        mooc_export_results = self.fetch_all_mooc_export_data(course_id)
        logger.info(f"MOOC Export results: {mooc_export_results}")
        
        # Bước 3: Fetch H5P data cho từng user
        logger.info("Step 3: Fetching H5P data for each user...")
        success_count = 0
        failed_count = 0
        
        for idx, user_id in enumerate(user_ids, 1):
            logger.info(f"[{idx}/{total_users}] Processing user {user_id}...")
            if self.fetch_user_data(user_id, course_id, delay):
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Fetch completed! Success: {success_count}, Failed: {failed_count}")
        
        # Bước 4: Aggregate vào raw_data (nếu được yêu cầu)
        if aggregate:
            logger.info("Step 4: Aggregating data into raw_data table...")
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            aggregate_result = self.aggregate_all_raw_data(course_id, batch_id)
            logger.info(f"Aggregation completed! {aggregate_result.get('success_count', 0)}/{aggregate_result.get('total_users', 0)} users processed")
        
        return {
            "success": True,
            "total_users": total_users,
            "success_count": success_count,
            "failed_count": failed_count,
            "mooc_export_results": mooc_export_results,
            "aggregated": aggregate
        }


def main():
    """Main function để chạy script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch data from MOOC and H5P APIs')
    parser.add_argument('--course-id', type=str, required=True, help='Course ID')
    parser.add_argument(
        '--sessionid',
        type=str,
        help='MOOC sessionid cookie (từ trình duyệt) để gọi được các API yêu cầu đăng nhập'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay giữa các API calls (seconds, default: 0.5)'
    )
    parser.add_argument(
        '--max-users',
        type=int,
        help='Giới hạn số lượng users để test (optional)'
    )
    parser.add_argument(
        '--no-aggregate',
        action='store_true',
        help='Không aggregate vào raw_data (chỉ fetch data)'
    )
    parser.add_argument(
        '--aggregate-only',
        action='store_true',
        help='Chỉ aggregate raw_data từ data đã có (không fetch mới)'
    )
    
    args = parser.parse_args()
    
    fetcher = MOOCH5PDataFetcher()
    
    # Thiết lập sessionid (nếu có)
    sessionid = args.sessionid
    if not sessionid:
        try:
            sessionid = input(
                "Nhập MOOC sessionid (cookie khi bạn đang đăng nhập, Enter để bỏ qua): "
            ).strip()
        except EOFError:
            sessionid = ""

    if sessionid:
        fetcher.set_mooc_session(sessionid)
    
    if not fetcher.connect_db():
        logger.error("Failed to connect to database")
        return
    
    try:
        # Nếu chỉ aggregate
        if args.aggregate_only:
            logger.info("Aggregating existing data into raw_data...")
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            result = fetcher.aggregate_all_raw_data(args.course_id, batch_id)
            
            if result.get("success"):
                logger.info(f"Successfully aggregated {result['success_count']}/{result['total_users']} users")
            else:
                logger.error(f"Failed: {result.get('message', 'Unknown error')}")
        else:
            # Fetch data (có thể kèm aggregate)
            result = fetcher.fetch_all_course_data(
                args.course_id,
                delay=args.delay,
                max_users=args.max_users,
                aggregate=not args.no_aggregate
            )
            
            if result.get("success"):
                logger.info(f"Successfully processed {result['success_count']}/{result['total_users']} users")
                if result.get("aggregated"):
                    logger.info("Data has been aggregated into raw_data table")
            else:
                logger.error(f"Failed: {result.get('message', 'Unknown error')}")
    
    finally:
        fetcher.close_db()


if __name__ == "__main__":
    main()
