@echo off
REM UIDAI Intelligence System - Run Script
REM Windows Batch File for Easy Execution

echo ============================================================
echo    UIDAI INTELLIGENCE SYSTEM
echo    Production Deployment Runner
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.9 or higher.
    pause
    exit /b 1
)

REM Navigate to script directory
cd /d "%~dp0"

echo [INFO] Current directory: %CD%
echo [INFO] Starting UIDAI Intelligence System...
echo.

REM Run the main system
python main.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo [ERROR] System encountered an error. Check outputs/system.log for details.
    pause
    exit /b 1
) else (
    echo.
    echo [SUCCESS] Analysis completed successfully!
    echo.
    echo Reports saved to: outputs\reports\
    echo.
)

pause
