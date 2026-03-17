"""
视频读取模块
负责视频文件的读取、信息提取和质量检查
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional
import os

from config.settings import VIDEO_CONFIG


class VideoReader:
    """视频读取器类"""
    
    def __init__(self):
        self.cap = None
        self.video_info = {}
    
    def read(self, video_path: str) -> Tuple[dict, List[np.ndarray]]:
        """
        读取视频文件
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            video_info: 视频信息字典
            frames: 视频帧列表
            
        Raises:
            ValueError: 视频文件格式不支持或质量不合格
        """
        # 检查文件是否存在
        if not Path(video_path).exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 检查文件格式
        ext = Path(video_path).suffix.lower()
        if ext not in VIDEO_CONFIG["supported_formats"]:
            raise ValueError(f"不支持的视频格式: {ext}")
        
        # 检查文件大小
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if file_size_mb > VIDEO_CONFIG["max_size_mb"]:
            raise ValueError(f"视频文件过大: {file_size_mb:.2f}MB (最大支持{VIDEO_CONFIG['max_size_mb']}MB)")
        
        # 打开视频
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        # 提取视频信息
        self.video_info = self._extract_info()
        
        # 检查视频时长
        if self.video_info["duration"] > VIDEO_CONFIG["max_duration_sec"]:
            self.cap.release()
            raise ValueError(f"视频时长过长: {self.video_info['duration']:.1f}秒 (最大支持{VIDEO_CONFIG['max_duration_sec']}秒)")
        
        # 读取视频帧
        frames = self._read_frames()
        
        # 质量检查
        self._quality_check(frames)
        
        self.cap.release()
        
        return self.video_info, frames
    
    def _extract_info(self) -> dict:
        """提取视频基本信息"""
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": duration,
            "resolution": f"{width}x{height}"
        }
    
    def _read_frames(self) -> List[np.ndarray]:
        """读取所有视频帧"""
        frames = []
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            # 转换为RGB格式
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
        return frames
    
    def _quality_check(self, frames: List[np.ndarray]):
        """
        视频质量检查
        
        检查内容:
        1. 亮度是否合适
        2. 是否过于模糊
        3. 是否有人体
        """
        if len(frames) == 0:
            raise ValueError("视频中没有帧")
        
        # 采样几帧进行检测
        sample_indices = [0, len(frames)//2, -1]
        sample_frames = [frames[i] for i in sample_indices if i < len(frames)]
        
        for frame in sample_frames:
            # 亮度检查
            brightness = np.mean(frame)
            if brightness < 30:
                print(f"警告: 视频过暗 (亮度: {brightness:.1f})")
            elif brightness > 230:
                print(f"警告: 视频过亮 (亮度: {brightness:.1f})")
            
            # 模糊度检查 (使用Laplacian方差)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            if blur_score < 50:
                print(f"警告: 视频可能模糊 (清晰度: {blur_score:.1f})")
        
        # 人体检测需要关键点检测模块,这里先做基本检查
        if len(frames) < 10:
            print(f"警告: 视频帧数较少 ({len(frames)}帧), 可能影响评估效果")
    
    def get_frame_at(self, frame_index: int) -> Optional[np.ndarray]:
        """获取指定索引的帧"""
        if self.cap is None or not self.cap.isOpened():
            return None
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self.cap.read()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None
