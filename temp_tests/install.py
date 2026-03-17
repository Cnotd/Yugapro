"""
自动安装脚本
自动检查依赖并尝试安装
"""

import subprocess
import sys

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ {package} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ {package} 安装失败")
        return False

def check_module(module_name):
    """检查模块是否已安装"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def main():
    print("=" * 60)
    print("瑜伽动作评估系统 - 自动安装")
    print("=" * 60)

    # 依赖列表
    dependencies = [
        ("opencv-python", "cv2"),
        ("mediapipe", "mediapipe"),
        ("numpy", "numpy"),
        ("requests", "requests"),
        ("matplotlib", "matplotlib"),
        ("gradio", "gradio"),
        ("pillow", "PIL"),
        ("pandas", "pandas"),
        ("tqdm", "tqdm"),
    ]

    print("\n检查依赖...")
    missing = []
    for pkg_name, module_name in dependencies:
        if check_module(module_name):
            print(f"✓ {pkg_name}")
        else:
            print(f"✗ {pkg_name} - 需要安装")
            missing.append(pkg_name)

    if not missing:
        print("\n✓ 所有依赖已安装!")
        print("\n运行系统测试:")
        print("  python test_system.py")
        print("\n启动应用:")
        print("  python run.py")
        return

    print(f"\n发现 {len(missing)} 个缺失的包,开始安装...")

    # 尝试安装
    success_count = 0
    for pkg in missing:
        if install_package(pkg):
            success_count += 1

    print("\n" + "=" * 60)
    if success_count == len(missing):
        print("✓ 所有依赖安装成功!")
        print("\n下一步:")
        print("  1. 运行系统测试: python test_system.py")
        print("  2. 启动应用: python run.py")
    else:
        print(f"⚠ 部分包安装失败 ({success_count}/{len(missing)})")
        print("\n手动安装失败的包:")
        for pkg in missing:
            if not check_module(pkg.replace("-", "_")):
                print(f"  pip install {pkg}")
    print("=" * 60)

if __name__ == "__main__":
    main()
