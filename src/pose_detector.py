"""
人体关键点检测模块
使用MediaPipe进行33个关键点检测和骨骼可视化
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
import mediapipe as mp

from config.settings import POSE_CONNECTIONS


class PoseDetector:
    """MediaPipe姿态检测器"""
    
    def __init__(self, static_image_mode=False, model_complexity=1, 
                 min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """
        初始化姿态检测器
        
        Args:
            static_image_mode: 是否为静态图像模式
            model_complexity: 模型复杂度 (0, 1, 2)
            min_detection_confidence: 最小检测置信度
            min_tracking_confidence: 最小跟踪置信度
        """
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        # 统计信息
        self.detection_count = 0
        self.success_count = 0
    
    def detect(self, frame: np.ndarray) -> Optional[List[Dict]]:
        """
        检测单帧中的人体关键点
        
        Args:
            frame: RGB图像帧
            
        Returns:
            landmarks: 关键点列表,每个点包含{x, y, z, visibility}
            失败时返回None
        """
        self.detection_count += 1
        
        # MediaPipe期望RGB输入
        results = self.pose.process(frame)
        
        if results.pose_landmarks:
            self.success_count += 1
            
            # 提取33个关键点
            landmarks = []
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                landmarks.append({
                    "id": idx,
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z,
                    "visibility": landmark.visibility
                })
            
            return landmarks
        
        return None
    
    def detect_sequence(self, frames: List[np.ndarray]) -> List[Optional[List[Dict]]]:
        """
        检测视频序列中的人体关键点
        
        Args:
            frames: 视频帧列表
            
        Returns:
            landmarks_seq: 每帧的关键点列表
        """
        landmarks_seq = []
        
        for frame in frames:
            landmarks = self.detect(frame)
            landmarks_seq.append(landmarks)
        
        # 输出检测成功率
        success_rate = self.success_count / self.detection_count * 100
        print(f"关键点检测成功率: {success_rate:.1f}% ({self.success_count}/{self.detection_count})")
        
        return landmarks_seq
    
    def draw_landmarks(self, frame: np.ndarray, landmarks: List[Dict], 
                      thickness: int = 2, circle_radius: int = 3) -> np.ndarray:
        """
        在图像上绘制骨骼连线
        
        Args:
            frame: 原始图像
            landmarks: 关键点列表
            thickness: 连线粗细
            circle_radius: 关键点圆圈半径
            
        Returns:
            annotated_frame: 标注后的图像
        """
        # 创建副本避免修改原图
        annotated = frame.copy()
        height, width = frame.shape[:2]
        
        # 转换为像素坐标
        points = []
        for lm in landmarks:
            points.append({
                "x": int(lm["x"] * width),
                "y": int(lm["y"] * height),
                "z": lm["z"],
                "visibility": lm["visibility"]
            })
        
        # 绘制骨骼连线
        for start_idx, end_idx in POSE_CONNECTIONS:
            if start_idx < len(points) and end_idx < len(points):
                pt1 = points[start_idx]
                pt2 = points[end_idx]
                
                # 只绘制可见度较高的点
                if pt1["visibility"] > 0.5 and pt2["visibility"] > 0.5:
                    cv2.line(annotated, 
                           (pt1["x"], pt1["y"]), 
                           (pt2["x"], pt2["y"]), 
                           (0, 255, 0), thickness)
        
        # 绘制关键点
        for i, pt in enumerate(points):
            if pt["visibility"] > 0.5:
                # 根据深度用不同颜色显示
                color = (255, 0, 0) if pt["z"] < 0 else (0, 0, 255)
                cv2.circle(annotated, (pt["x"], pt["y"]), circle_radius, color, -1)
        
        return annotated
    
    def get_landmark_by_id(self, landmarks: List[Dict], landmark_id: int) -> Optional[Dict]:
        """
        根据ID获取关键点
        
        Args:
            landmarks: 关键点列表
            landmark_id: 关键点ID
            
        Returns:
            关键点信息,不存在则返回None
        """
        for lm in landmarks:
            if lm["id"] == landmark_id:
                return lm
        return None
    
    def get_success_rate(self) -> float:
        """获取检测成功率"""
        if self.detection_count == 0:
            return 0.0
        return self.success_count / self.detection_count
    
    def reset_stats(self):
        """重置统计信息"""
        self.detection_count = 0
        self.success_count = 0
    
    def __del__(self):
        """释放资源"""
        if hasattr(self, 'pose'):
            self.pose.close()
