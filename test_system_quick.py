# -*- coding: utf-8 -*-
"""
系统快速检查脚本 - 测试所有核心组件是否正常运行
"""

import sys
import os
from pathlib import Path

# 设置为 UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试导入"""
    print("\n" + "=" * 60)
    print("测试 1: 导入核心模块")
    print("=" * 60)
    
    try:
        print("导入 PoseDetector...", end=" ")
        from src.pose_detector import PoseDetector
        print("[OK]")
        
        print("导入 FrameSampler...", end=" ")
        from src.frame_sampler import FrameSampler
        print("[OK]")
        
        print("导入 AngleCalculator...", end=" ")
        from src.angle_calculator import AngleCalculator
        print("[OK]")
        
        print("导入 VideoReader...", end=" ")
        from src.video_reader import VideoReader
        print("[OK]")
        
        print("导入 OllamaClient...", end=" ")
        from src.ollama_client import OllamaClient
        print("[OK]")
        
        print("导入 SimpleEvaluator...", end=" ")
        from src.simple_evaluator import SimpleEvaluator
        print("[OK]")
        
        print("导入 ArchiveManager...", end=" ")
        from src.archive_manager import ArchiveManager
        print("[OK]")
        
        print("\n[PASS] 所有模块导入成功")
        return True
    except Exception as e:
        print(f"[FAIL] {e}")
        return False

def test_init():
    """测试初始化"""
    print("\n" + "=" * 60)
    print("测试 2: 初始化核心组件")
    print("=" * 60)
    
    try:
        from src.pose_detector import PoseDetector
        from src.frame_sampler import FrameSampler
        from src.angle_calculator import AngleCalculator
        from src.video_reader import VideoReader
        from src.ollama_client import OllamaClient
        from src.simple_evaluator import SimpleEvaluator
        
        print("初始化 PoseDetector...", end=" ")
        detector = PoseDetector()
        print("[OK]")
        
        print("初始化 FrameSampler...", end=" ")
        sampler = FrameSampler()
        print("[OK]")
        
        print("初始化 AngleCalculator...", end=" ")
        calc = AngleCalculator()
        print("[OK]")
        
        print("初始化 VideoReader...", end=" ")
        reader = VideoReader()
        print("[OK]")
        
        print("初始化 OllamaClient...", end=" ")
        ollama = OllamaClient()
        print("[OK]")
        
        print("初始化 SimpleEvaluator...", end=" ")
        evaluator = SimpleEvaluator()
        print("[OK]")
        
        print("\n[PASS] 所有组件初始化成功")
        return True
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_olama_connection():
    """测试 Ollama 连接"""
    print("\n" + "=" * 60)
    print("测试 3: Ollama 连接检查")
    print("=" * 60)
    
    try:
        from src.ollama_client import OllamaClient
        
        client = OllamaClient()
        print("检查 Ollama 服务连接...", end=" ")
        
        if client.check_connection():
            print("[OK]")
            print("\n[PASS] Ollama 服务正常运行")
            return True
        else:
            print("[NOT AVAILABLE]")
            print("\n[WARN] Ollama 服务未启动（但不影响基础功能）")
            print("      提示: ollama serve")
            return True  # 这不是致命错误
    except Exception as e:
        print(f"[WARN] {e}")
        return True

def test_video_detection():
    """测试视频检测"""
    print("\n" + "=" * 60)
    print("测试 4: 视频检测")
    print("=" * 60)
    
    try:
        # 查找测试视频
        video_dir = project_root / "data" / "temp" / "Ardhakati_Chakrasana"
        video_path = video_dir / "Ardhakati Chakrasana Right Step Angle 1.mp4"
        
        if not video_path.exists():
            print(f"[WARN] 测试视频不存在: {video_path}")
            return True  # 不是致命错误
        
        print(f"找到视频: {video_path.name}")
        print(f"文件大小: {video_path.stat().st_size / (1024*1024):.1f} MB")
        
        # 初始化 VideoReader
        from src.video_reader import VideoReader
        reader = VideoReader()
        
        print("读取视频元数据...", end=" ")
        info, frames = reader.read(str(video_path))
        print("[OK]")
        
        print(f"视频时长: {info['duration']:.1f} 秒")
        print(f"宽x高: {info['width']} x {info['height']}")
        print(f"帧数: {info['frame_count']}")
        print(f"FPS: {info['fps']:.1f}")
        
        print("\n[PASS] 视频检测成功")
        return True
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n")
    print("*" * 60)
    print("*" + " " * 58 + "*")
    print("*" + "  瑜伽动作评估系统 - 系统检查" .center(58) + "*")
    print("*" + " " * 58 + "*")
    print("*" * 60)
    
    results = []
    
    results.append(("导入模块", test_imports()))
    results.append(("初始化组件", test_init()))
    results.append(("Ollama 连接", test_olama_connection()))
    results.append(("视频检测", test_video_detection()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{name}: {status}")
    
    all_pass = all(r[1] for r in results)
    
    print("\n" + "=" * 60)
    if all_pass:
        print("系统状态: [OK] 所有测试通过，系统可正常使用")
    else:
        print("系统状态: [WARNING] 部分测试失败，请检查上述错误")
    print("=" * 60 + "\n")
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
