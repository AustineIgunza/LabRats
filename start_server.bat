@echo off
echo ===============================
echo   LabRats Management System
echo ===============================
echo.

cd /d "c:\Users\mmatt\LabRats"

REM Check if virtual environment exists
if exist "venv" (
    echo Activating virtual environment...
    call venv\Scripts\activate
) else (
    echo No virtual environment found. Creating one...
    python -m venv venv
    call venv\Scripts\activate
    
    echo Installing requirements...
    pip install -r backend\requirements.txt
)

echo.
echo Starting LabRats server...
echo Server will be available at: http://127.0.0.1:8000
echo API documentation: http://127.0.0.1:8000/api/docs
echo.

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

pause
