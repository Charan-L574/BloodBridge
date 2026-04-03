@echo off
echo ========================================
echo BloodBridge - Startup
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 16 or higher from https://nodejs.org/
    pause
    exit /b 1
)

echo.
echo [1/4] Setting up Backend...
cd backend

echo Checking if virtual environment exists...
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing backend dependencies...
pip install -r requirements.txt --quiet

echo Setting up MySQL database...
python setup_mysql.py >nul 2>&1

echo.
echo [2/4] Starting Backend Server...
echo Backend will run at: http://localhost:8000
echo API Docs will be at: http://localhost:8000/docs
echo.
start "BloodBridge Backend" cmd /k "cd /d %CD% && .venv\Scripts\activate.bat && uvicorn main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

cd ..

echo.
echo [3/4] Setting up Frontend...
cd frontend

if not exist "node_modules\" (
    echo Installing frontend dependencies...
    call npm install
) else (
    echo Frontend dependencies already installed.
)

echo.
echo [4/4] Starting Frontend Server...
echo Frontend will run at: http://localhost:3000
echo.
start "BloodBridge Frontend" cmd /k "cd /d %CD% && npm run dev"

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo Demo Credentials:
echo   Donor:     donor1@example.com / password123
echo   Requester: requester@example.com / password123
echo   Hospital:  hospital1@example.com / password123
echo.
echo Press any key to open the application in your browser...
pause >nul

start http://localhost:3000

echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
pause
