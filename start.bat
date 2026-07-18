@echo off
echo ============================================
echo   StudyPilot - Starting All Services
echo ============================================
echo.

echo [1/4] Checking Docker Desktop...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo   Docker not running. Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo   Waiting for Docker to start...
    :wait_docker
    timeout /t 5 /nobreak >nul
    docker version >nul 2>&1
    if %errorlevel% neq 0 goto wait_docker
    echo   Docker Desktop is ready!
) else (
    echo   Docker is already running.
)

echo.
echo [2/4] Starting backend services (Docker)...
docker-compose up -d --build
if %errorlevel% neq 0 (
    echo ERROR: Failed to start Docker services!
    pause
    exit /b 1
)

echo.
echo [3/4] Waiting for services to be healthy...
timeout /t 20 /nobreak >nul

echo.
echo [4/4] Starting frontend (Flask)...
cd frontend
start "StudyPilot Frontend" cmd /c "pip install -r requirements.txt -q 2>nul & python app.py"
cd ..

echo.
echo ============================================
echo   All services started successfully!
echo ============================================
echo.
echo   Backend API:    http://localhost:8000
echo   Frontend:       http://localhost:3000
echo   RabbitMQ UI:    http://localhost:15672
echo.
echo   Admin Login:    admin@studypilot.com / Admin@1234
echo   Test Login:     (register at /register)
echo.
echo   To stop all services, run: stop.bat
echo ============================================
pause
