@echo off
chcp 65001 >nul
echo ========================================
echo   启动前端开发服务器
echo ========================================
echo.
cd /d %~dp0js_frontend
echo 启动HTTP服务器在 http://localhost:3000
echo 按 Ctrl+C 停止服务器
echo.
python -m http.server 3000
