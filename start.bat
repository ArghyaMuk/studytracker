@echo off
setlocal enabledelayedexpansion
title StudyPilot - Starting Application
color 0A

echo.
echo  ============================================================
echo   StudyPilot - AI-Powered Study ^& Exam Readiness Platform
echo  ============================================================
echo.

:: ─────────────────────────────────────────────────────────────
:: STEP 1: Check Docker Desktop is running
:: ─────────────────────────────────────────────────────────────
echo  [1/6] Checking Docker Desktop...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo         Docker not running. Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo         Waiting for Docker daemon...
    :wait_docker
    timeout /t 5 /nobreak >nul
    docker version >nul 2>&1
    if %errorlevel% neq 0 goto wait_docker
    echo         Docker Desktop is ready!
) else (
    echo         Docker is already running.
)
echo.

:: ─────────────────────────────────────────────────────────────
:: STEP 2: Pull required base images
:: ─────────────────────────────────────────────────────────────
echo  [2/6] Checking and pulling required images...
echo         Pulling mysql:8.0...
docker pull mysql:8.0 >nul 2>&1
echo         Pulling redis:7-alpine...
docker pull redis:7-alpine >nul 2>&1
echo         Pulling rabbitmq:3-management-alpine...
docker pull rabbitmq:3-management-alpine >nul 2>&1
echo         Pulling python:3.12-slim...
docker pull python:3.12-slim >nul 2>&1
echo         All base images ready.
echo.

:: ─────────────────────────────────────────────────────────────
:: STEP 3: Build custom service images
:: ─────────────────────────────────────────────────────────────
echo  [3/6] Building StudyPilot service images...
docker-compose build --parallel
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Build failed! Check Dockerfile errors above.
    pause
    exit /b 1
)
echo         All service images built successfully.
echo.

:: ─────────────────────────────────────────────────────────────
:: STEP 4: Start all containers
:: ─────────────────────────────────────────────────────────────
echo  [4/6] Starting all containers...
docker-compose up -d
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Failed to start containers!
    pause
    exit /b 1
)
echo         All containers started.
echo.

:: ─────────────────────────────────────────────────────────────
:: STEP 5: Wait for services to become healthy
:: ─────────────────────────────────────────────────────────────
echo  [5/6] Waiting for all services to become healthy...
set attempts=0
:health_check
set /a attempts+=1
if %attempts% gtr 30 (
    echo.
    echo  [WARNING] Services took too long. Some may not be healthy.
    goto start_frontend
)
timeout /t 3 /nobreak >nul
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo         Waiting... (attempt %attempts%/30)
    goto health_check
)
echo         All backend services are healthy!
echo.

:: ─────────────────────────────────────────────────────────────
:: STEP 6: Start Flask frontend
:: ─────────────────────────────────────────────────────────────
:start_frontend
echo  [6/6] Starting Flask frontend...
cd frontend
start "StudyPilot Frontend" cmd /c "pip install -r requirements.txt -q 2>nul & python app.py"
cd ..
timeout /t 3 /nobreak >nul
echo         Frontend started on port 3000.
echo.

:: ─────────────────────────────────────────────────────────────
:: SUCCESS
:: ─────────────────────────────────────────────────────────────
echo.
echo  ============================================================
echo   StudyPilot is READY!
echo  ============================================================
echo.
echo   Frontend:       http://localhost:3000
echo   Backend API:    http://localhost:8000
echo   RabbitMQ UI:    http://localhost:15672 (guest/guest)
echo.
echo   Admin Login:    (see .env file for credentials)
echo   Student:        Register at http://localhost:3000/register
echo.
echo   To stop: run stop.bat
echo  ============================================================
echo.
pause
