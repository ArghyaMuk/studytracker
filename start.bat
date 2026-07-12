@echo off
echo ============================================
echo   StudyPilot - Starting All Services
echo ============================================
echo.

echo [1/3] Starting backend services (Docker)...
docker-compose up -d --build
if %errorlevel% neq 0 (
    echo ERROR: Failed to start Docker services!
    echo Make sure Docker Desktop is running.
    pause
    exit /b 1
)

echo.
echo [2/3] Waiting for services to be healthy...
timeout /t 15 /nobreak >nul

echo.
echo [3/3] Starting frontend (Next.js)...
cd frontend
start "StudyPilot Frontend" cmd /c "npm run dev"
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
echo   Test Login:     test@student.com / Test@1234
echo.
echo   To stop all services, run: stop.bat
echo ============================================
pause
