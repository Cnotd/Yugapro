@echo off
chcp 65001 >nul
echo ==========================================
echo   Yoga Assessment System - Flask API
echo ==========================================
echo.

cd /d D:\yuga_test
set YOGA_API_PORT=5000
echo Starting Python Flask API on http://localhost:%YOGA_API_PORT% ...
echo.
python python_api.py
