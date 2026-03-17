"""
视频读取模块测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.video_reader import VideoReader


def test_video_reader():
    """测试视频读取功能"""
    print("测试视频读取模块...")
    
    reader = VideoReader()
    
    # 这里需要一个测试视频文件
    test_video = "data/test/sample.mp4"
    
    if os.path.exists(test_video):
        try:
            video_info, frames = reader.read(test_video)
            print(f"✓ 视频读取成功")
            print(f"  分辨率: {video_info['resolution']}")
            print(f"  时长: {video_info['duration']:.2f}秒")
            print(f"  帧数: {video_info['frame_count']}")
            print(f"  FPS: {video_info['fps']:.2f}")
        except Exception as e:
            print(f"✗ 测试失败: {e}")
    else:
        print(f"✓ 模块导入成功 (未找到测试视频: {test_video})")


if __name__ == "__main__":
    test_video_reader()
