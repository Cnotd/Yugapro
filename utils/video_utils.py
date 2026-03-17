"""
视频工具函数模块
提供视频处理相关的工具函数
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path


def resize_frame(frame: np.ndarray, max_width: int = 640) -> np.ndarray:
    """
    调整帧大小,保持宽高比
    
    Args:
        frame: 原始帧
        max_width: 最大宽度
        
    Returns:
        调整大小后的帧
    """
    height, width = frame.shape[:2]
    
    if width <= max_width:
        return frame
    
    ratio = max_width / width
    new_height = int(height * ratio)
    
    return cv2.resize(frame, (max_width, new_height))


def save_video(frames: List[np.ndarray], output_path: str, fps: float = 30.0):
    """
    保存视频文件
    
    Args:
        frames: 帧列表
        output_path: 输出路径
        fps: 帧率
    """
    if not frames:
        raise ValueError("帧列表为空")
    
    # 获取帧尺寸
    height, width = frames[0].shape[:2]
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # 写入每一帧
    for frame in frames:
        # 转换为BGR格式(OpenCV默认)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)
    
    out.release()


def extract_frames_at_indices(frames: List[np.ndarray], 
                             indices: List[int]) -> List[np.ndarray]:
    """
    提取指定索引的帧
    
    Args:
        frames: 原始帧列表
        indices: 要提取的索引列表
        
    Returns:
        提取的帧列表
    """
    result = []
    for idx in indices:
        if 0 <= idx < len(frames):
            result.append(frames[idx])
    return result


def get_key_frames(frames: List[np.ndarray], 
                  num_frames: int = 3) -> List[np.ndarray]:
    """
    获取关键帧(均匀采样)
    
    Args:
        frames: 原始帧列表
        num_frames: 要提取的关键帧数量
        
    Returns:
        关键帧列表
    """
    if len(frames) <= num_frames:
        return frames
    
    step = len(frames) // num_frames
    indices = [i * step for i in range(num_frames)]
    return extract_frames_at_indices(frames, indices)


def create_video_preview(frames: List[np.ndarray], 
                         output_path: str,
                         fps: int = 10,
                         max_frames: int = 30):
    """
    创建视频预览(降低帧率)
    
    Args:
        frames: 原始帧列表
        output_path: 输出路径
        fps: 输出帧率
        max_frames: 最大帧数
    """
    # 限制帧数
    if len(frames) > max_frames:
        step = len(frames) // max_frames
        frames = frames[::step]
    
    save_video(frames, output_path, fps)


def add_text_overlay(frame: np.ndarray, text: str, 
                    position: Tuple[int, int] = (10, 30),
                    font_scale: float = 1.0,
                    color: Tuple[int, int, int] = (255, 255, 255),
                    thickness: int = 2) -> np.ndarray:
    """
    在帧上添加文字叠加
    
    Args:
        frame: 原始帧
        text: 要添加的文字
        position: 文字位置 (x, y)
        font_scale: 字体大小
        color: 文字颜色 (BGR格式)
        thickness: 文字粗细
        
    Returns:
        添加文字后的帧
    """
    result = frame.copy()
    cv2.putText(result, text, position, 
               cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
    return result


def crop_to_person(frame: np.ndarray, landmarks: List[dict], 
                  padding: float = 0.1) -> np.ndarray:
    """
    根据人体关键点裁剪图像
    
    Args:
        frame: 原始帧
        landmarks: 关键点列表
        padding: 边距比例
        
    Returns:
        裁剪后的帧
    """
    if not landmarks:
        return frame
    
    height, width = frame.shape[:2]
    
    # 获取所有关键点的坐标
    x_coords = [lm["x"] * width for lm in landmarks]
    y_coords = [lm["y"] * height for lm in landmarks]
    
    # 计算边界框
    min_x = int(min(x_coords))
    max_x = int(max(x_coords))
    min_y = int(min(y_coords))
    max_y = int(max(y_coords))
    
    # 添加边距
    pad_x = int((max_x - min_x) * padding)
    pad_y = int((max_y - min_y) * padding)
    
    min_x = max(0, min_x - pad_x)
    max_x = min(width, max_x + pad_x)
    min_y = max(0, min_y - pad_y)
    max_y = min(height, max_y + pad_y)
    
    # 裁剪
    return frame[min_y:max_y, min_x:max_x]


def blend_images(img1: np.ndarray, img2: np.ndarray, 
                alpha: float = 0.5) -> np.ndarray:
    """
    混合两张图像
    
    Args:
        img1: 第一张图像
        img2: 第二张图像
        alpha: 第一张图像的权重(0-1)
        
    Returns:
        混合后的图像
    """
    # 确保图像大小相同
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    
    return cv2.addWeighted(img1, alpha, img2, 1 - alpha, 0)


def create_comparison_video(original_frames: List[np.ndarray],
                           annotated_frames: List[np.ndarray],
                           output_path: str,
                           fps: float = 30.0):
    """
    创建并排对比视频
    
    Args:
        original_frames: 原始帧列表
        annotated_frames: 标注帧列表
        output_path: 输出路径
        fps: 帧率
    """
    if len(original_frames) != len(annotated_frames):
        raise ValueError("原始帧和标注帧数量不匹配")
    
    if not original_frames:
        return
    
    height, width = original_frames[0].shape[:2]
    output_width = width * 2
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, 
                         (output_width, height))
    
    for orig, annot in zip(original_frames, annotated_frames):
        # 转换为BGR
        orig_bgr = cv2.cvtColor(orig, cv2.COLOR_RGB2BGR)
        annot_bgr = cv2.cvtColor(annot, cv2.COLOR_RGB2BGR)
        
        # 水平拼接
        combined = np.hstack([orig_bgr, annot_bgr])
        out.write(combined)
    
    out.release()
