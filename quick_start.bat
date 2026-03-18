@echo off
chcp 65001 >nul
echo ========================================
echo     瑜伽动作评估系统 - 快速启动
echo ========================================
echo.
echo 1. 激活环境
call D:\conda\Scripts\activate.bat yuga
echo.
echo ========================================
echo 请选择操作:
echo ========================================
echo.
echo [1] 处理单个视频并归档
echo [2] 批量处理视频并归档
echo [3] 查看归档内容
echo [4] 手动归档 temp/ 下的结果
echo [5] 启动 Web 界面
echo [6] 退出
echo.
set /p choice="请输入选项 (1-6): "

if "%choice%"=="1" goto single
if "%choice%"=="2" goto batch
if "%choice%"=="3" goto view
if "%choice%"=="4" goto manual
if "%choice%"=="5" goto web
if "%choice%"=="6" goto end

echo 无效选项，请重新运行
goto end

:single
echo.
echo [1] 处理单个视频
echo.
python temp_tests/test_ardhakati.py
pause
goto end

:batch
echo.
echo [2] 批量处理视频
echo.
python temp_tests/test_mediapipe_batch.py
pause
goto end

:view
echo.
echo [3] 查看归档内容
echo.
python view_archive.py
pause
goto end

:manual
echo.
echo [6] 手动归档
echo.
python archive_results.py
pause
goto end

:angle_single
echo.
echo [3] 角度检测和标注（单视频）
echo.
python temp_tests/test_angle_single.py
pause
goto end

:angle_batch
echo.
echo [4] 角度检测和标注（批量）
echo.
python temp_tests/test_angle_analysis.py
pause
goto end

:web
echo.
echo [7] 启动 Web 界面
echo.
python run.py
goto end

:end
echo.
echo 按任意键退出...
pause >nul
