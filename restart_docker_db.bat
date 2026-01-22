@echo off
REM =============================================================================
REM Docker Restart Script - Rebuild Database từ đầu
REM =============================================================================
REM Purpose: Stop, remove containers và volumes, sau đó start lại với schema mới
REM WARNING: Script này sẽ XÓA TẤT CẢ DATA hiện tại!
REM =============================================================================

setlocal enabledelayedexpansion

echo ========================================
echo   Docker Database Restart Script
echo ========================================
echo.
echo [WARNING] Script nay se XOA TAT CA DATA hien tai!
echo.
set /p confirm="Ban co chac chan muon tiep tuc? (y/n): "
if /i not "%confirm%"=="y" (
    echo Huy bo.
    pause
    exit /b 0
)

echo.
echo [1/5] Stopping containers...
docker-compose down
if errorlevel 1 (
    echo [ERROR] Failed to stop containers
    pause
    exit /b 1
)
echo [OK] Containers stopped
echo.

echo [2/5] Removing volumes (deleting all data)...
docker volume rm dropout_prediction_mysql_data 2>nul
echo [OK] Volumes removed
echo.

echo [3/5] Starting containers with new schema...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start containers
    pause
    exit /b 1
)
echo [OK] Containers started
echo.

echo [4/5] Waiting for MySQL to be ready...
timeout /t 15 /nobreak >nul
echo [OK] MySQL should be ready
echo.

echo [5/5] Verifying database schema...
echo Checking tables...
docker exec -i dropout_prediction_mysql mysql -uroot -proot_password_123 dropout_prediction_db -e "SHOW TABLES;"
echo.

echo ========================================
echo Database restart completed!
echo ========================================
echo.
echo New tables created:
echo   - enrollments
echo   - h5p_scores, h5p_scores_summary
echo   - video_progress, video_progress_summary
echo   - dashboard_summary
echo   - mooc_progress (updated with new columns)
echo   - mooc_grades (NEW)
echo   - mooc_discussions (NEW)
echo   - raw_data (updated with new columns)
echo.
echo Access phpMyAdmin: http://localhost:8081
echo   Username: dropout_user
echo   Password: dropout_pass_123
echo.
echo Next steps:
echo   1. Verify schema in phpMyAdmin
echo   2. Run fetch_mooc_h5p_data.py to populate data
echo.
pause
