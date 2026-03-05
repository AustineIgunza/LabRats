@echo off
echo =====================================
echo     LabRats Application Setup
echo =====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python detected!

REM Check if we're in the backend directory
if not exist "requirements.txt" (
    echo Error: requirements.txt not found
    echo Please run this script from the backend directory
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo =====================================
echo   Dependencies installed successfully!
echo =====================================
echo.

REM Check if PostgreSQL is needed
echo Checking PostgreSQL setup...
python -c "import psycopg2" >nul 2>&1
if errorlevel 1 (
    echo Warning: PostgreSQL client not properly installed
) else (
    echo PostgreSQL client is ready!
)

REM Check if Redis is needed
echo Checking Redis setup...
python -c "import redis" >nul 2>&1
if errorlevel 1 (
    echo Warning: Redis client not properly installed
) else (
    echo Redis client is ready!
)

echo.
echo =====================================
echo        Setup Instructions
echo =====================================
echo.
echo 1. Install and start PostgreSQL server
echo 2. Install and start Redis server
echo 3. Run: python setup_db.py (to setup database)
echo 4. Run: python main.py (to start the application)
echo.
echo Application will be available at: http://localhost:8000
echo API docs will be available at: http://localhost:8000/api/docs
echo.

REM Ask if user wants to run setup_db.py
set /p setup_db="Do you want to run database setup now? (y/n): "
if /i "%setup_db%"=="y" (
    echo.
    echo Running database setup...
    python setup_db.py
    if errorlevel 1 (
        echo Database setup failed. Please check PostgreSQL configuration.
    ) else (
        echo Database setup completed!
    )
)

echo.
set /p start_app="Do you want to start the application now? (y/n): "
if /i "%start_app%"=="y" (
    echo.
    echo Starting LabRats application...
    echo Press Ctrl+C to stop the server
    echo.
    python main.py
) else (
    echo.
    echo To start the application later, run:
    echo   venv\Scripts\activate.bat
    echo   python main.py
)

echo.
pause
