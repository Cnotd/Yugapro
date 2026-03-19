@echo off
echo ====================================
echo 激活yuga环境并运行测试
echo ====================================
echo.

REM 使用yuga环境的Python路径
set PYTHON_PATH=D:\conda\envs\yuga\python.exe

echo [信息] 使用Python: %PYTHON_PATH%
echo.

if not exist "%PYTHON_PATH%" (
    echo [错误] 找不到yuga环境的Python
    pause
    exit /b 1
)

echo [信息] 运行测试...
echo.

"%PYTHON_PATH%" test_half_moon_assessment.py

echo.
echo ====================================
echo 测试完成
echo ====================================
pause
