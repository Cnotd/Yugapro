@echo off
chcp 65001 >nul
echo ==========================================
echo   Yoga Assessment System - Quick Start
echo ==========================================
echo.

:: Stop old server
echo [1/4] Stopping old server...
taskkill /F /IM yoga-assessment-server.exe 2>nul
timeout /t 1 /nobreak >nul

:: Build backend
echo [2/4] Building backend...
cd /d D:\yuga_test\rust_backend
cargo build --release
if %ERRORLEVEL% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

:: Start backend server
echo [3/4] Starting backend server on port 8080...
start "Yoga Backend" cmd /k ".\target\release\yoga-assessment-server.exe"

timeout /t 2 /nobreak >nul

:: Start frontend server
echo [4/4] Starting frontend server on port 3000...
cd /d D:\yuga_test\js_frontend
start "Yoga Frontend" cmd /k "python -m http.server 3000"

echo.
echo ==========================================
echo   All services started!
echo ==========================================
echo   Backend API:  http://localhost:8080
echo   Frontend:    http://localhost:3000
echo.
echo   Press any key to exit this window...
pause >nul
