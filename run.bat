@echo off
echo ==============================================================================
echo   ONLINE EXAMINATION MANAGEMENT AND STUDENT PERFORMANCE ANALYSIS SYSTEM
echo ==============================================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in your system PATH.
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [2/3] Checking and installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python packages.
    pause
    exit /b 1
)

if not exist exam_system.db (
    echo [3/3] Initializing and seeding database with realistic sample exams ^& students...
    python seed_data.py
) else (
    echo [3/3] Database found. Starting application server...
)

echo.
echo ==============================================================================
echo   Starting ExamSphere Pro Application Server...
echo   Open your web browser and navigate to: http://127.0.0.1:5000
echo ==============================================================================
echo.

python app.py
pause
