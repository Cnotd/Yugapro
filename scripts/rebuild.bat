@echo off
cd /d D:\yuga_test\rust_backend
echo Stopping old server...
taskkill /F /IM yoga-assessment-server.exe 2>nul
echo Waiting...
timeout /t 2 /nobreak >nul
echo Building...
cargo build --release
echo Done!
pause
