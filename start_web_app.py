#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""启动Flask Web应用和前端服务"""

import subprocess
import time
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

print("=" * 60)
print("  启动瑜伽评估系统（Flask版本）")
print("=" * 60)
print()

# 启动Flask REST API
print("[1/2] 启动Flask REST API服务...")
api_process = subprocess.Popen(
    [sys.executable, "python_api.py"],
    cwd=str(PROJECT_ROOT),
    env={**os.environ, "YOGA_API_PORT": "5000"}
)

time.sleep(3)

# 启动前端服务
print("[2/2] 启动前端服务...")
frontend_dir = PROJECT_ROOT / "js_frontend"
frontend_process = subprocess.Popen(
    [sys.executable, "-m", "http.server", "3000"],
    cwd=str(frontend_dir)
)

print()
print("=" * 60)
print("✓ 系统启动成功！")
print()
print("  Flask REST API: http://localhost:5000")
print("  前端服务:       http://localhost:3000")
print()
print("  在浏览器中访问: http://localhost:3000")
print("=" * 60)
print()
print("按 Ctrl+C 停止所有服务")
print()

try:
    api_process.wait()
except KeyboardInterrupt:
    print("\n正在停止服务...")
    api_process.terminate()
    frontend_process.terminate()
    api_process.wait()
    frontend_process.wait()
    print("✓ 已停止")
