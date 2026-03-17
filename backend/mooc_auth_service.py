"""
MOOC Authentication Service.

Auto-login vào Open edX (MOOC) platform, quản lý session cookie,
tự động re-login khi session hết hạn.
"""
import os
import logging
import threading
import time
import requests
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

MOOC_BASE = "https://mooc.vnuhcm.edu.vn"
MOOC_API_BASE = f"{MOOC_BASE}/api/custom/v1"
CSRF_ENDPOINT = f"{MOOC_BASE}/csrf/api/v1/token"
LOGIN_ENDPOINT = f"{MOOC_BASE}/api/user/v1/account/login_session/"


class MOOCAuthService:
    """
    Quản lý xác thực với MOOC platform.

    - Auto-login bằng email/password từ .env
    - Cache session, tự refresh khi hết hạn hoặc gặp 401/403
    - Thread-safe
    """

    def __init__(self):
        self._email = os.getenv("MOOC_EMAIL", "")
        self._password = os.getenv("MOOC_PASSWORD", "")
        self._session: Optional[requests.Session] = None
        self._session_id: Optional[str] = None
        self._authenticated_at: Optional[datetime] = None
        self._lock = threading.Lock()
        self._max_age = timedelta(hours=12)

    @property
    def is_configured(self) -> bool:
        return bool(self._email and self._password)

    @property
    def is_authenticated(self) -> bool:
        if not self._session_id or not self._authenticated_at:
            return False
        return datetime.now() - self._authenticated_at < self._max_age

    @property
    def status(self) -> dict:
        return {
            "configured": self.is_configured,
            "authenticated": self.is_authenticated,
            "email": self._email[:3] + "***" if self._email else None,
            "authenticated_at": (
                self._authenticated_at.isoformat()
                if self._authenticated_at
                else None
            ),
        }

    def _create_session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update({
            "User-Agent": "DropoutPrediction/2.0",
            "Accept": "application/json",
            "Referer": f"{MOOC_BASE}/login",
            "Origin": MOOC_BASE,
        })
        return s

    def login(self) -> bool:
        """
        Login vào MOOC platform.

        1. GET csrf token
        2. POST login_session với email + password
        3. Verify bằng /users/me/
        """
        with self._lock:
            return self._do_login()

    def _do_login(self) -> bool:
        if not self.is_configured:
            logger.error(
                "MOOC credentials chưa cấu hình. "
                "Set MOOC_EMAIL và MOOC_PASSWORD trong .env"
            )
            return False

        self._session = self._create_session()
        logger.info(f"Đang login MOOC với {self._email[:3]}***...")

        try:
            # Bước 1: Lấy CSRF token
            csrf_resp = self._session.get(CSRF_ENDPOINT, timeout=15)
            csrf_resp.raise_for_status()
            csrf_token = self._session.cookies.get("csrftoken", "")
            if not csrf_token:
                csrf_data = csrf_resp.json()
                csrf_token = csrf_data.get("csrfToken", "")

            if not csrf_token:
                logger.error("Không lấy được CSRF token")
                return False

            logger.info("CSRF token OK")

            # Bước 2: POST login (Open edX cần form-encoded, không phải JSON)
            self._session.headers["X-CSRFToken"] = csrf_token
            self._session.headers["Content-Type"] = "application/x-www-form-urlencoded"
            login_resp = self._session.post(
                LOGIN_ENDPOINT,
                data={"email": self._email, "password": self._password},
                timeout=30,
            )
            self._session.headers.pop("Content-Type", None)

            if login_resp.status_code == 200:
                self._session_id = self._session.cookies.get("sessionid")
                if not self._session_id:
                    edx_session = self._session.cookies.get(
                        "edx-jwt-cookie-header-payload"
                    )
                    for c in self._session.cookies:
                        if "session" in c.name.lower():
                            self._session_id = c.value
                            break

                if self._session_id:
                    self._authenticated_at = datetime.now()
                    logger.info(
                        f"Login thành công! session_id={self._session_id[:8]}..."
                    )
                    return self._verify_session()

                logger.warning(
                    "Login response 200 nhưng không tìm thấy session cookie"
                )
                self._session_id = "login_ok"
                self._authenticated_at = datetime.now()
                return self._verify_session()

            elif login_resp.status_code == 403:
                logger.error("Login thất bại: 403 Forbidden (sai credentials hoặc CSRF)")
                return False
            else:
                logger.error(
                    f"Login thất bại: {login_resp.status_code} - "
                    f"{login_resp.text[:200]}"
                )
                return False

        except requests.RequestException as e:
            logger.error(f"Login request lỗi: {e}")
            return False

    def _verify_session(self) -> bool:
        """Verify session bằng /users/me/"""
        try:
            resp = self._session.get(
                f"{MOOC_API_BASE}/users/me/", timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                user_info = data.get("data", data)
                username = user_info.get("username", "unknown")
                logger.info(f"Session verified: logged in as '{username}'")
                return True
            else:
                logger.warning(
                    f"Session verify thất bại: {resp.status_code}"
                )
                return False
        except Exception as e:
            logger.warning(f"Session verify lỗi: {e}")
            return False

    def get_session(self) -> requests.Session:
        """
        Trả về authenticated session.
        Auto re-login nếu session hết hạn.
        """
        if not self.is_authenticated:
            self.login()

        if self._session is None:
            self._session = self._create_session()
        return self._session

    def request(
        self, method: str, url: str, retry_on_auth_fail: bool = True, **kwargs
    ) -> requests.Response:
        """
        Gửi request với auto-retry khi gặp 401/403.
        """
        kwargs.setdefault("timeout", 30)
        session = self.get_session()
        resp = session.request(method, url, **kwargs)

        if resp.status_code in (401, 403) and retry_on_auth_fail:
            logger.warning(
                f"Got {resp.status_code}, đang re-login..."
            )
            self._authenticated_at = None
            self.login()
            session = self.get_session()
            resp = session.request(method, url, **kwargs)

        return resp

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def fetch_all_courses(self) -> list:
        """
        Gọi /course-details/all/ (Public API, không cần auth).
        Trả về danh sách tất cả courses trên MOOC.
        """
        try:
            resp = requests.get(
                f"{MOOC_API_BASE}/course-details/all/", timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            courses = data.get("data", [])
            logger.info(f"Discovered {len(courses)} courses từ MOOC")
            return courses
        except Exception as e:
            logger.error(f"Lỗi fetch all courses: {e}")
            return []


_auth_instance: Optional[MOOCAuthService] = None


def get_mooc_auth() -> MOOCAuthService:
    """Singleton instance."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = MOOCAuthService()
    return _auth_instance
