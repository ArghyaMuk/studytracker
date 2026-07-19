@echo off
setlocal enabledelayedexpansion
title StudyPilot - Stopping Application
color 0C

echo.
echo  ============================================================
echo   StudyPilot - Stopping and Cleaning Up
echo  ============================================================
echo.

:: ─────────────────────────────────────────────────────────────
:: STEP 1: Stop Flask frontend
:: ─────────────────────────────────────────────────────────────
echo  [1/5] Stopping Flask frontend...
taskkill /f /fi "WINDOWTITLE eq StudyPilot Frontend" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":3000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo         Frontend stopped.
echo.

:: ─────────────────────────────────────────────────────────────
:: STEP 2: Stop all containers
:: ─────────────────────────────────────────────────────────────
echo  [2/5] Stopping all containers...
docker-compose stop >nul 2>&1
echo         All containers stopped.
echo.

:: ─────────────────────────────────────────────────────────────
:: STEP 3: Remove all containers
:: ─────────────────────────────────────────────────────────────
echo  [3/5] Removing all StudyPilot containers...
docker-compose down >nul 2>&1
echo         All containers removed.
echo.

:: ─────────────────────────────────────────────────────────────
:: STEP 4: Remove StudyPilot custom images
:: ─────────────────────────────────────────────────────────────
echo  [4/5] Removing StudyPilot service images...
for /f "tokens=*" %%i in ('docker images --filter "reference=lpuproject-*" -q 2^>nul') do (
    docker rmi -f %%i >nul 2>&1
)
echo         Custom service images removed.
echo.

:: ─────────────────────────────────────────────────────────────
:: STEP 5: Ask about volumes and base images
:: ─────────────────────────────────────────────────────────────
echo  [5/5] Cleanup options:
echo.
set /p REMOVE_VOLUMES="  Remove database volumes (resets all data)? [y/N]: "
if /i "%REMOVE_VOLUMES%"=="y" (
    echo         Removing volumes...
    docker-compose down -v >nul 2>&1
    docker volume ls --filter "name=lpuproject" -q 2>nul | for /f "tokens=*" %%v in ('more') do docker volume rm %%v >nul 2>&1
    echo         Volumes removed. Database will be fresh on next start.
) else (
    echo         Volumes kept. Data preserved for next start.
)
echo.

set /p REMOVE_BASE="  Remove base images (mysql, redis, rabbitmq, python)? [y/N]: "
if /i "%REMOVE_BASE%"=="y" (
    echo         Removing base images...
    docker rmi -f mysql:8.0 >nul 2>&1
    docker rmi -f redis:7-alpine >nul 2>&1
    docker rmi -f rabbitmq:3-management-alpine >nul 2>&1
    docker rmi -f python:3.12-slim >nul 2>&1
    echo         Base images removed.
) else (
    echo         Base images kept (saves time on next start).
)
echo.

:: Remove project networks
docker network ls --filter "name=lpuproject" -q 2>nul | for /f "tokens=*" %%n in ('more') do docker network rm %%n >nul 2>&1

:: ─────────────────────────────────────────────────────────────
:: SUCCESS
:: ─────────────────────────────────────────────────────────────
echo.
echo  ============================================================
echo   StudyPilot - Cleanup Complete!
echo  ============================================================
echo.
echo   All StudyPilot containers: REMOVED
echo   Custom service images:     REMOVED
echo   Project networks:          REMOVED
if /i "%REMOVE_VOLUMES%"=="y" (
    echo   Database volumes:          REMOVED (fresh start next time)
) else (
    echo   Database volumes:          KEPT (data preserved)
)
if /i "%REMOVE_BASE%"=="y" (
    echo   Base images:               REMOVED
) else (
    echo   Base images:               KEPT
)
echo.
echo   To start again: run start.bat
echo  ============================================================
echo.
pause
