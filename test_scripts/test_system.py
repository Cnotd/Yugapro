"""
系统完整性测试
测试所有核心模块是否正常工作
"""

import sys
import os

print("=" * 60)
print("瑜伽动作评估系统 - 模块完整性测试")
print("=" * 60)

# 检查Python版本
print(f"\nPython版本: {sys.version}")
if sys.version_info < (3, 9):
    print("⚠ 警告: Python版本过低,建议使用3.9+")
else:
    print("✓ Python版本符合要求")

# 检查关键依赖
print("\n检查依赖包...")
dependencies = [
    "cv2",  # opencv-python
    "mediapipe",
    "numpy",
    "requests",
    "matplotlib",
    "gradio",
    "PIL",  # pillow
    "pandas",
]

missing_deps = []
for dep in dependencies:
    try:
        __import__(dep)
        print(f"✓ {dep}")
    except ImportError:
        print(f"✗ {dep} - 未安装")
        missing_deps.append(dep)

if missing_deps:
    print(f"\n⚠ 缺失依赖包,请运行: pip install -r requirements.txt")
else:
    print("\n✓ 所有依赖包已安装")

# 测试模块导入
print("\n测试模块导入...")
modules_to_test = [
    "config.settings",
    "src.video_reader",
    "src.pose_detector",
    "src.angle_calculator",
    "src.stats_calculator",
    "src.prompt_builder",
    "src.ollama_client",
    "src.result_parser",
    "utils.video_utils",
    "utils.visualization",
]

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"✓ {module_name}")
    except Exception as e:
        print(f"✗ {module_name} - {str(e)}")

# 检查Ollama连接
print("\n检查Ollama服务...")
try:
    from src.ollama_client import OllamaClient
    client = OllamaClient()
    if client.check_connection():
        print("✓ Ollama服务可用")
        models = client.list_models()
        if models:
            print(f"  可用模型: {len(models)}个")
            for model in models[:3]:
                print(f"    - {model.get('name', 'Unknown')}")
        else:
            print("  ⚠ 未找到可用模型,建议运行: ollama pull qwen:7b")
    else:
        print("⚠ Ollama服务不可用 (可选功能)")
except Exception as e:
    print(f"✗ 无法检查Ollama服务: {e}")

# 检查目录结构
print("\n检查目录结构...")
required_dirs = [
    "src",
    "config",
    "utils",
    "tests",
    "data/raw",
    "data/processed",
]

for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print(f"✓ {dir_path}")
    else:
        print(f"⚠ {dir_path} - 不存在")

# 检查配置文件
print("\n检查配置文件...")
if os.path.exists("config/settings.py"):
    print("✓ config/settings.py")
    try:
        from config.settings import POSE_STANDARDS
        print(f"  支持动作数: {len(POSE_STANDARDS)}")
        for pose_name in POSE_STANDARDS.keys():
            print(f"    - {pose_name}")
    except Exception as e:
        print(f"  ✗ 加载配置失败: {e}")
else:
    print("✗ config/settings.py 不存在")

# 总结
print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)

if not missing_deps:
    print("\n✓ 系统基本功能正常,可以启动")
    print("运行命令: python run.py")
else:
    print("\n✗ 请先安装缺失的依赖包")
    print("运行命令: pip install -r requirements.txt")
