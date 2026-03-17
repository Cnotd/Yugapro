"""
整理项目文件夹，将临时测试文件移到temp_tests目录
"""

import shutil
from pathlib import Path

# 需要移动的文件
files_to_move = [
    "test_mediapipe.py",
    "test_model_output.py", 
    "test_ollama.py",
    "video_compressor.py",
    "view_video.html",
    "view_video.py",
    "run_no_proxy.py",
    "run_simple.py",
    "install.py",
    "model_output.txt"
]

# 需要保留的文件（不移动）
files_to_keep = [
    "test_system.py",  # 主要测试脚本
    "run.py",          # 启动脚本
    "requirements.txt" # 依赖文件
]

# 项目根目录
project_root = Path(__file__).parent

# 创建temp_tests目录
temp_tests_dir = project_root / "temp_tests"
temp_tests_dir.mkdir(exist_ok=True)

print("开始整理项目文件...")
print("=" * 60)

# 移动文件
moved_count = 0
for filename in files_to_move:
    source = project_root / filename
    destination = temp_tests_dir / filename
    
    if source.exists():
        try:
            shutil.copy2(source, destination)
            source.unlink()
            print(f"[OK] 已移动: {filename}")
            moved_count += 1
        except Exception as e:
            print(f"[FAIL] 移动失败: {filename} - {e}")
    else:
        print(f"- 文件不存在: {filename}")

print("\n" + "=" * 60)
print(f"完成! 共移动 {moved_count} 个文件")
print(f"\n临时测试文件位置: {temp_tests_dir}")

# 显示当前根目录的文件
print("\n当前根目录文件:")
print("-" * 60)
for file in sorted(project_root.glob("*.py *.txt *.md")):
    if file.is_file():
        print(f"  {file.name}")

print("\n整理完成!")
