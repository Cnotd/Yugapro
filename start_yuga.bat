@echo off
chcp 65001 >nul
echo ========================================
echo     Yoga Action Assessment System
echo ========================================
echo.
echo Activating yuga environment...
call D:\conda\Scripts\activate.bat yuga
echo.
echo Environment: yuga
echo Python Path: %CONDA_PREFIX%\python.exe
echo.
echo Usage:
echo   python temp_tests/test_ardhakati.py
echo   python temp_tests/test_mediapipe_batch.py
echo   python run.py
echo.
echo ========================================
cmd /k
