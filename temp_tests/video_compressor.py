"""
视频处理工具 - 用于处理大视频文件
"""

import cv2
import numpy as np
from pathlib import Path

class VideoProcessor:
    """视频处理器 - 用于调整视频大小和压缩"""
    
    def __init__(self):
        pass
    
    def resize_video(self, input_path: str, output_path: str, 
                    target_width: int = 640, target_fps: int = 15):
        """
        调整视频大小和帧率
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            target_width: 目标宽度（高度会自动计算保持比例）
            target_fps: 目标帧率
        """
        print(f"读取视频: {input_path}")
        cap = cv2.VideoCapture(input_path)
        
        # 获取视频信息
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        original_fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 计算目标高度（保持比例）
        aspect_ratio = original_height / original_width
        target_height = int(target_width * aspect_ratio)
        
        print(f"原始视频信息:")
        print(f"  分辨率: {original_width}x{original_height}")
        print(f"  帧率: {original_fps} FPS")
        print(f"  总帧数: {total_frames}")
        print(f"  时长: {total_frames/original_fps:.2f}秒")
        
        print(f"\n压缩后视频信息:")
        print(f"  分辨率: {target_width}x{target_height}")
        print(f"  帧率: {target_fps} FPS")
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, target_fps, 
                             (target_width, target_height))
        
        # 帧采样间隔
        frame_interval = original_fps // target_fps
        
        print(f"\n开始处理视频...")
        frame_count = 0
        processed_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 按间隔采样
            if frame_count % frame_interval == 0:
                # 调整大小
                resized = cv2.resize(frame, (target_width, target_height))
                out.write(resized)
                processed_count += 1
            
            frame_count += 1
            
            # 进度显示
            if frame_count % 100 == 0:
                progress = frame_count / total_frames * 100
                print(f"进度: {progress:.1f}% ({frame_count}/{total_frames})")
        
        cap.release()
        out.release()
        
        # 获取输出文件大小
        output_size = Path(output_path).stat().st_size / (1024 * 1024)
        
        print(f"\n✓ 视频处理完成!")
        print(f"  处理后帧数: {processed_count}")
        print(f"  输出文件: {output_path}")
        print(f"  文件大小: {output_size:.2f} MB")


def process_large_videos(data_dir: str = "data"):
    """
    处理 data 目录下的大视频文件
    
    Args:
        data_dir: 数据目录路径
    """
    data_path = Path(data_dir)
    
    # 查找所有视频文件
    video_extensions = ['.mp4', '.avi', '.mov']
    video_files = []
    for ext in video_extensions:
        video_files.extend(data_path.rglob(f"*{ext}"))
    
    if not video_files:
        print(f"在 {data_dir} 目录下未找到视频文件")
        return
    
    # 按文件大小排序
    video_files.sort(key=lambda x: x.stat().st_size, reverse=True)
    
    print("=" * 60)
    print("视频文件列表 (按大小排序):")
    print("=" * 60)
    
    for i, video_file in enumerate(video_files):
        size_mb = video_file.stat().st_size / (1024 * 1024)
        print(f"{i+1}. {video_file.name}")
        print(f"   大小: {size_mb:.2f} MB")
        print(f"   路径: {video_file}")
        print()
    
    # 处理大于 50MB 的视频
    processor = VideoProcessor()
    
    for video_file in video_files:
        size_mb = video_file.stat().st_size / (1024 * 1024)
        
        if size_mb > 50:
            print("=" * 60)
            print(f"处理大视频: {video_file.name} ({size_mb:.2f} MB)")
            print("=" * 60)
            
            # 生成输出文件名
            output_name = f"{video_file.stem}_compressed{video_file.suffix}"
            output_path = video_file.parent / output_name
            
            # 跳过已存在的文件
            if output_path.exists():
                print(f"跳过: {output_name} 已存在")
                print()
                continue
            
            # 处理视频
            processor.resize_video(
                str(video_file),
                str(output_path),
                target_width=640,
                target_fps=15
            )
            
            # 比较文件大小
            output_size = output_path.stat().st_size / (1024 * 1024)
            compression_ratio = (1 - output_size / size_mb) * 100
            
            print(f"压缩率: {compression_ratio:.1f}%")
            print(f"节省空间: {size_mb - output_size:.2f} MB")
            print()
    
    print("=" * 60)
    print("处理完成!")
    print("=" * 60)


if __name__ == "__main__":
    print("视频压缩工具")
    print("=" * 60)
    print()
    
    # 处理 data 目录下的所有视频
    process_large_videos("data")
    
    print("\n使用方法:")
    print("1. 压缩后的视频文件名格式: 原文件名_compressed.mp4")
    print("2. 压缩参数: 宽度640px, 帧率15fps (保持原始宽高比)")
    print("3. 压缩后的视频适合用于关键点检测")
