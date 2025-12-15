@echo off
REM ╔══════════════════════════════════════════════════════════════╗
REM ║      TrendsPro Clean Architecture Setup Script (Windows)      ║
REM ╚══════════════════════════════════════════════════════════════╝

echo.
echo ============================================================
echo     TrendsPro Clean Architecture Setup (Windows)
echo ============================================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [INFO] Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip upgraded
echo.

REM Install requirements
echo Installing requirements (this may take a few minutes)...
pip install -r requirements.txt --quiet
echo [OK] All requirements installed
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found
    
    if exist ".env.example" (
        echo Creating .env from template...
        copy .env.example .env >nul
        echo [OK] .env file created from template
        echo.
        echo Please edit .env and add your configuration:
        echo   - OPENAI_API_KEY
        echo   - DB_TRENDS_URL (MySQL connection)
        echo   - MONGO_LUDAFARMA_URL (MongoDB connection)
    ) else (
        echo [ERROR] No .env.example found
        echo Please create a .env file with your configuration
        pause
        exit /b 1
    )
) else (
    echo [OK] .env file exists
    
    REM Update ARCHITECTURE_MODE to clean
    powershell -Command "(gc .env) -replace 'ARCHITECTURE_MODE=.*', 'ARCHITECTURE_MODE=clean' | Out-File -encoding ASCII .env"
    echo [OK] ARCHITECTURE_MODE set to 'clean'
)

REM Create necessary directories
echo Creating required directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "cache" mkdir cache
if not exist "uploads" mkdir uploads
echo [OK] Directories created
echo.

REM Create start script for easy execution
echo @echo off > start.bat
echo call venv\Scripts\activate.bat >> start.bat
echo python start_clean.py >> start.bat
echo [OK] Created start.bat for easy execution
echo.

echo ============================================================
echo           Setup completed successfully!
echo ============================================================
echo.
echo Next steps:
echo.
echo 1. Edit .env file with your configuration (if needed)
echo    notepad .env
echo.
echo 2. Start the application:
echo    start.bat
echo.
echo    Or manually:
echo    venv\Scripts\activate
echo    python start_clean.py
echo.
echo Documentation will be available at:
echo    http://localhost:8000/docs (after starting)
echo.
echo Ready to run in Clean Architecture mode!
echo.
pause
