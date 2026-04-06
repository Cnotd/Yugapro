@echo off
chcp 65001 >nul
echo ========================================
echo   瑜伽姿态评估系统 - 测试脚本
echo ========================================
echo.

:: 检查Python环境
echo [1/6] 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ Python未安装
    exit /b 1
)
echo ✅ Python已安装
echo.

:: 检查Rust环境
echo [2/6] 检查Rust环境...
rustc --version
if errorlevel 1 (
    echo ⚠️ Rust未安装，正在安装...
    echo 请访问 https://rustup.rs 安装Rust
    echo 或者运行: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    set RUST_INSTALLED=0
) else (
    echo ✅ Rust已安装
    set RUST_INSTALLED=1
)
echo.

:: 检查Cargo依赖
echo [3/6] 检查Cargo依赖...
if "%RUST_INSTALLED%"=="1" (
    cargo --version
    if errorlevel 1 (
        echo ❌ Cargo未正确安装
        exit /b 1
    )
    echo ✅ Cargo已安装
) else (
    echo ⚠️ 跳过Cargo检查（Rust未安装）
)
echo.

:: 检查前端文件
echo [4/6] 检查前端文件...
if exist "js_frontend\index.html" (
    echo ✅ 前端文件存在
) else (
    echo ❌ 前端文件缺失
    exit /b 1
)
echo.

:: 检查后端文件
echo [5/6] 检查后端文件...
if exist "rust_backend\Cargo.toml" (
    echo ✅ 后端配置文件存在
    if exist "rust_backend\src\main.rs" (
        echo ✅ 主程序入口存在
    ) else (
        echo ❌ 主程序入口缺失
        exit /b 1
    )
) else (
    echo ❌ 后端配置文件缺失
    exit /b 1
)
echo.

:: 测试Rust编译
echo [6/6] 测试Rust编译...
if "%RUST_INSTALLED%"=="1" (
    echo 正在编译Rust后端（这可能需要几分钟）...
    cd rust_backend
    cargo check --message-format=short
    if errorlevel 1 (
        echo ❌ Rust编译失败
        cd ..
        exit /b 1
    )
    echo ✅ Rust编译检查通过
    cd ..
) else (
    echo ⚠️ 跳过Rust编译（Rust未安装）
)
echo.

:: 测试前端服务
echo ========================================
echo 测试前端服务...
echo.
cd js_frontend
start "" "http://localhost:3000" 
echo 启动前端服务: python -m http.server 3000
echo 按Ctrl+C停止服务
python -m http.server 3000
