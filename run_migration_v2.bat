@echo off
REM ============================================================================
REM Migration V2 - Quick Run Script
REM ============================================================================

echo ================================================================================
echo MIGRATION V2: raw_data -^> 3 Tables
echo ================================================================================
echo.

REM Check if in correct directory
if not exist "backend\app.py" (
    echo ERROR: Please run this script from dropout_prediction folder!
    pause
    exit /b 1
)

echo Step 1: Backup database (recommended)
echo ----------------------------------------
echo.
echo Do you want to backup database first? (Y/N)
set /p BACKUP_CHOICE="> "

if /i "%BACKUP_CHOICE%"=="Y" (
    echo.
    echo Creating backup...
    set BACKUP_FILE=backup_v1_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sql
    mysqldump -u root -p mooc_database > "%BACKUP_FILE%"
    echo Backup saved to: %BACKUP_FILE%
    echo.
)

echo.
echo Step 2: Run migration script
echo ----------------------------------------
echo.
python database\migrate_to_v2.py
if errorlevel 1 (
    echo.
    echo ❌ Migration FAILED!
    pause
    exit /b 1
)

echo.
echo Step 3: Verify migration
echo ----------------------------------------
echo.
python verify_v2_migration.py

echo.
echo ================================================================================
echo Migration completed! Check output above for any errors.
echo ================================================================================
echo.
echo Next steps:
echo   1. Review verification results above
echo   2. If OK, switch backend to V2:
echo      - Stop current backend (Ctrl+C)
echo      - Run: python backend\app_v2.py
echo   3. Test dashboard
echo   4. (Optional) Rename raw_data to legacy backup
echo.
pause
