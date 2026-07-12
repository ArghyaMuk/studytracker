@echo off
echo ============================================
echo   StudyPilot - Stopping All Services
echo ============================================
echo.

echo [1/2] Stopping frontend (Flask)...
taskkill /f /fi "WINDOWTITLE eq StudyPilot Frontend" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo   Frontend stopped.

echo.
echo [2/2] Stopping backend services (Docker)...
docker-compose down
if %errorlevel% neq 0 (
    echo WARNING: Docker compose down may have failed.
)

echo.
echo ============================================
echo   All services stopped successfully!
echo ============================================
pause
