"""
视频帧采样模块 - 均匀采样 + 无效帧过滤
"""

import cv2
import mediapipe as mp
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import time

@dataclass
class FrameInfo:
    """帧信息数据类"""
    frame_idx: int
    timestamp: float
    frame: np.ndarray
    landmarks: Optional[any] = None
    is_valid: bool = False
    confidence: float = 0.0
    valid_points_ratio: float = 0.0
    blur_score: float = 0.0
    brightness: float = 0.0
    invalid_reason: str = ""


class FrameSampler:
    """
    帧采样器 - 均匀采样 + 无效帧过滤
    """
    def __init__(self, 
                 confidence_threshold: float = 0.5,
                 min_valid_ratio: float = 0.7,
                 blur_threshold: float = 50.0,
                 brightness_range: Tuple[float, float] = (30, 225)):
        """
        初始化采样器
        
        Args:
            confidence_threshold: 置信度阈值
            min_valid_ratio: 最少有效关键点比例
            blur_threshold: 模糊度阈值（拉普拉斯方差）
            brightness_range: 亮度范围
        """
        self.confidence_threshold = confidence_threshold
        self.min_valid_ratio = min_valid_ratio
        self.blur_threshold = blur_threshold
        self.brightness_range = brightness_range
        
        # 初始化MediaPipe
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=1,
            min_detection_confidence=0.5
        )
    
    def calculate_blur(self, frame: np.ndarray) -> float:
        """计算图像模糊度"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()
    
    def calculate_brightness(self, frame: np.ndarray) -> float:
        """计算图像平均亮度"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return np.mean(gray)
    
    def check_frame_quality(self, frame: np.ndarray) -> Tuple[bool, str]:
        """检查帧的基本质量"""
        # 检查亮度
        brightness = self.calculate_brightness(frame)
        if brightness < self.brightness_range[0]:
            return False, f"亮度过低 ({brightness:.1f})"
        if brightness > self.brightness_range[1]:
            return False, f"亮度过高 ({brightness:.1f})"
        
        # 检查模糊度
        blur = self.calculate_blur(frame)
        if blur < self.blur_threshold:
            return False, f"画面模糊 ({blur:.1f})"
        
        return True, "质量合格"
    
    def detect_pose(self, frame: np.ndarray) -> Tuple[Optional[any], float, float]:
        """
        检测人体姿态
        返回: (landmarks, 平均置信度, 有效点比例)
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)
        
        if not results.pose_landmarks:
            return None, 0.0, 0.0
        
        # 计算置信度
        confidences = [lm.visibility for lm in results.pose_landmarks.landmark]
        avg_confidence = np.mean(confidences)
        
        # 计算有效点比例（置信度高于阈值的点）
        valid_points = sum(1 for c in confidences if c > self.confidence_threshold)
        valid_ratio = valid_points / len(confidences)
        
        return results.pose_landmarks, avg_confidence, valid_ratio
    
    def process_frame(self, frame_idx: int, frame: np.ndarray, fps: float) -> FrameInfo:
        """处理单帧"""
        info = FrameInfo(
            frame_idx=frame_idx,
            timestamp=frame_idx / fps,
            frame=frame
        )
        
        # 1. 基本质量检查
        quality_ok, quality_reason = self.check_frame_quality(frame)
        if not quality_ok:
            info.is_valid = False
            info.invalid_reason = quality_reason
            return info
        
        # 2. 人体姿态检测
        landmarks, avg_conf, valid_ratio = self.detect_pose(frame)
        
        info.landmarks = landmarks
        info.confidence = avg_conf
        info.valid_points_ratio = valid_ratio
        info.blur_score = self.calculate_blur(frame)
        info.brightness = self.calculate_brightness(frame)
        
        # 3. 判断是否有效
        if landmarks is None:
            info.is_valid = False
            info.invalid_reason = "未检测到人体"
        elif valid_ratio < self.min_valid_ratio:
            info.is_valid = False
            info.invalid_reason = f"有效关键点比例过低 ({valid_ratio:.2f} < {self.min_valid_ratio})"
        elif avg_conf < self.confidence_threshold:
            info.is_valid = False
            info.invalid_reason = f"置信度过低 ({avg_conf:.2f})"
        else:
            info.is_valid = True
            info.invalid_reason = "有效"
        
        return info
    
    def sample_from_video(self, 
                      video_path: str, 
                      target_frames: int = 100,
                      frame_interval: int = None) -> Tuple[List[FrameInfo], Dict]:
        """
        从视频中均匀采样并过滤无效帧
        
        Args:
            video_path: 视频路径
            target_frames: 目标采样帧数
            frame_interval: 帧间隔（秒），如果指定则优先使用此间隔
            
        Returns:
            (有效帧列表, 统计信息)
        """
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"视频信息:")
        print(f"  路径: {video_path}")
        print(f"  时长: {duration:.2f}秒")
        print(f"  FPS: {fps:.2f}")
        print(f"  总帧数: {total_frames}")
        
        # 确定采样间隔
        if frame_interval is not None:
            # 使用指定的秒数间隔
            interval_frames = int(fps * frame_interval)
            sample_indices = list(range(0, total_frames, interval_frames))
            print(f"  采样间隔: {frame_interval}秒 ({interval_frames}帧)")
        else:
            # 使用目标帧数均匀采样
            if total_frames <= target_frames:
                sample_indices = list(range(total_frames))
            else:
                step = total_frames / target_frames
                sample_indices = [int(i * step) for i in range(target_frames)]
            print(f"  目标采样帧数: {len(sample_indices)}")
        
        print(f"\n开始采样和过滤...")
        start_time = time.time()
        
        # 逐帧处理
        all_frames = []
        valid_frames = []
        invalid_frames = []
        
        for i, idx in enumerate(sample_indices):
            # 显示进度
            if (i + 1) % 20 == 0:
                print(f"  已处理 {i+1}/{len(sample_indices)} 帧...")
            
            # 定位到指定帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # 处理帧
            frame_info = self.process_frame(idx, frame, fps)
            all_frames.append(frame_info)
            
            if frame_info.is_valid:
                valid_frames.append(frame_info)
            else:
                invalid_frames.append(frame_info)
        
        cap.release()
        
        # 统计信息
        elapsed = time.time() - start_time
        stats = {
            'total_sampled': len(all_frames),
            'valid_frames': len(valid_frames),
            'invalid_frames': len(invalid_frames),
            'valid_ratio': len(valid_frames) / len(all_frames) if all_frames else 0,
            'processing_time': elapsed,
            'avg_confidence': np.mean([f.confidence for f in valid_frames]) if valid_frames else 0,
            'avg_blur': np.mean([f.blur_score for f in valid_frames]) if valid_frames else 0,
            'avg_brightness': np.mean([f.brightness for f in valid_frames]) if valid_frames else 0,
            'invalid_reasons': {}
        }
        
        # 统计无效原因
        for frame in invalid_frames:
            reason = frame.invalid_reason
            stats['invalid_reasons'][reason] = stats['invalid_reasons'].get(reason, 0) + 1
        
        print(f"\n处理完成！耗时: {elapsed:.2f}秒")
        print(f"有效帧: {len(valid_frames)}/{len(all_frames)} ({stats['valid_ratio']*100:.1f}%)")
        
        return valid_frames, stats
    
    def get_best_frames(self, valid_frames: List[FrameInfo], top_k: int = 10) -> List[FrameInfo]:
        """
        从有效帧中选出最好的几帧
        按置信度、清晰度等综合评分
        """
        if not valid_frames:
            return []
        
        # 计算综合得分
        for frame in valid_frames:
            # 综合得分 = 置信度*0.5 + 清晰度归一化*0.3 + 亮度适中度*0.2
            blur_norm = min(1.0, frame.blur_score / 200)  # 归一化模糊度
            brightness_score = 1.0 - abs(frame.brightness - 128) / 128  # 亮度接近128最好
            
            frame.composite_score = (
                frame.confidence * 0.5 +
                blur_norm * 0.3 +
                brightness_score * 0.2
            )
        
        # 按综合得分排序
        sorted_frames = sorted(valid_frames, 
                              key=lambda x: x.composite_score, 
                              reverse=True)
        
        return sorted_frames[:top_k]
