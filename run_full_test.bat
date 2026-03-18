@echo off
echo ========================================
echo Running Full Pipeline Test with Ollama
echo ========================================
echo.

REM 激活conda环境
call conda activate yuga

if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate conda environment
    pause
    exit /b 1
)

echo [OK] Conda environment activated
echo.

REM 运行完整流程测试
echo Starting full pipeline test...
python tests\test_full_pipeline.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Test failed with error code %errorlevel%
) else (
    echo.
    echo [SUCCESS] Test completed successfully
)

echo.
pause
