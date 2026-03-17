"""
角度计算模块
计算各个关节角度和身体姿态参数
"""

import numpy as np
import math
from typing import List, Dict, Optional, Tuple


class AngleCalculator:
    """角度计算器"""
    
    def __init__(self):
        pass
    
    def compute_all(self, landmarks_seq: List[List[Dict]]) -> List[Dict]:
        """
        计算所有帧的所有关节角度
        
        Args:
            landmarks_seq: 关键点序列
            
        Returns:
            angles_seq: 角度序列列表
        """
        angles_seq = []
        
        for landmarks in landmarks_seq:
            if landmarks is None or len(landmarks) == 0:
                angles_seq.append({})
                continue
            
            angles = self._compute_frame_angles(landmarks)
            angles_seq.append(angles)
        
        return angles_seq
    
    def _compute_frame_angles(self, landmarks: List[Dict]) -> Dict:
        """计算单帧的所有角度"""
        angles = {}
        
        # 肘关节角度
        angles["left_elbow"] = self.compute_angle(
            landmarks, 11, 13, 15  # shoulder, elbow, wrist
        )
        angles["right_elbow"] = self.compute_angle(
            landmarks, 12, 14, 16
        )
        
        # 膝关节角度
        angles["left_knee"] = self.compute_angle(
            landmarks, 23, 25, 27  # hip, knee, ankle
        )
        angles["right_knee"] = self.compute_angle(
            landmarks, 24, 26, 28
        )
        
        # 髋关节角度 (简化: 使用肩膀-髋-膝)
        angles["left_hip"] = self.compute_angle(
            landmarks, 11, 23, 25  # shoulder, hip, knee
        )
        angles["right_hip"] = self.compute_angle(
            landmarks, 12, 24, 26
        )
        
        # 肩关节角度
        angles["left_shoulder"] = self.compute_angle(
            landmarks, 13, 11, 23  # elbow, shoulder, hip
        )
        angles["right_shoulder"] = self.compute_angle(
            landmarks, 14, 12, 24
        )
        
        # 脊柱角度 (使用肩膀-髋-髋连线)
        angles["spine_angle"] = self.compute_spine_angle(landmarks)
        
        # 身体倾斜角度
        angles["body_tilt"] = self.compute_body_tilt(landmarks)
        
        return angles
    
    def compute_angle(self, landmarks: List[Dict], 
                     point1_idx: int, point2_idx: int, point3_idx: int) -> Optional[float]:
        """
        计算三点角度 (point1-point2-point3)
        
        Args:
            landmarks: 关键点列表
            point1_idx: 第一个点索引
            point2_idx: 第二个点索引 (顶点)
            point3_idx: 第三个点索引
            
        Returns:
            角度值(度数), 计算失败返回None
        """
        # 获取三个点
        p1 = self._get_point(landmarks, point1_idx)
        p2 = self._get_point(landmarks, point2_idx)
        p3 = self._get_point(landmarks, point3_idx)
        
        if p1 is None or p2 is None or p3 is None:
            return None
        
        # 计算向量
        v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
        
        # 计算夹角
        angle = self._vector_angle(v1, v2)
        
        return angle
    
    def _vector_angle(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """计算两个向量的夹角"""
        # 计算点积
        dot_product = np.dot(v1, v2)
        
        # 计算模
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # 计算余弦值,限制在[-1, 1]范围内
        cos_angle = np.clip(dot_product / (norm1 * norm2), -1.0, 1.0)
        
        # 转换为角度
        angle = np.degrees(np.arccos(cos_angle))
        
        return angle
    
    def _get_point(self, landmarks: List[Dict], idx: int) -> Optional[Tuple[float, float]]:
        """获取关键点的x,y坐标"""
        for lm in landmarks:
            if lm["id"] == idx:
                return (lm["x"], lm["y"])
        return None
    
    def compute_spine_angle(self, landmarks: List[Dict]) -> Optional[float]:
        """
        计算脊柱角度 (简化版)
        
        使用肩膀中点到髋部中点的角度
        """
        # 左右肩膀和髋部的中点
        left_shoulder = self._get_point(landmarks, 11)
        right_shoulder = self._get_point(landmarks, 12)
        left_hip = self._get_point(landmarks, 23)
        right_hip = self._get_point(landmarks, 24)
        
        if left_shoulder and right_shoulder and left_hip and right_hip:
            # 计算中点
            shoulder_center = ((left_shoulder[0] + right_shoulder[0])/2,
                             (left_shoulder[1] + right_shoulder[1])/2)
            hip_center = ((left_hip[0] + right_hip[0])/2,
                         (left_hip[1] + right_hip[1])/2)
            
            # 计算脊柱相对于垂直线的角度
            dx = shoulder_center[0] - hip_center[0]
            dy = shoulder_center[1] - hip_center[1]
            
            angle = np.degrees(np.arctan2(dx, -dy))
            return abs(angle)
        
        return None
    
    def compute_body_tilt(self, landmarks: List[Dict]) -> Optional[float]:
        """
        计算身体整体倾斜角度
        """
        left_shoulder = self._get_point(landmarks, 11)
        right_shoulder = self._get_point(landmarks, 12)
        
        if left_shoulder and right_shoulder:
            dx = left_shoulder[0] - right_shoulder[0]
            dy = left_shoulder[1] - right_shoulder[1]
            
            angle = np.degrees(np.arctan2(dy, dx))
            return abs(angle)
        
        return None
    
    def get_average_angles(self, angles_seq: List[Dict]) -> Dict[str, float]:
        """
        计算角度平均值
        
        Args:
            angles_seq: 角度序列
            
        Returns:
            平均角度字典
        """
        avg_angles = {}
        
        # 收集所有有效的角度值
        angle_values = {}
        for angles in angles_seq:
            for key, value in angles.items():
                if value is not None:
                    if key not in angle_values:
                        angle_values[key] = []
                    angle_values[key].append(value)
        
        # 计算平均值
        for key, values in angle_values.items():
            avg_angles[key] = np.mean(values)
        
        return avg_angles
    
    def get_angle_std(self, angles_seq: List[Dict]) -> Dict[str, float]:
        """
        计算角度标准差
        
        Args:
            angles_seq: 角度序列
            
        Returns:
            标准差字典
        """
        std_angles = {}
        
        # 收集所有有效的角度值
        angle_values = {}
        for angles in angles_seq:
            for key, value in angles.items():
                if value is not None:
                    if key not in angle_values:
                        angle_values[key] = []
                    angle_values[key].append(value)
        
        # 计算标准差
        for key, values in angle_values.items():
            std_angles[key] = np.std(values)
        
        return std_angles
    
    def check_angle_in_range(self, angle: float, angle_range: Tuple[float, float], 
                            tolerance: float = 5) -> bool:
        """
        检查角度是否在标准范围内
        
        Args:
            angle: 角度值
            angle_range: 标准范围 (min, max)
            tolerance: 容差(度)
            
        Returns:
            是否在范围内
        """
        min_val, max_val = angle_range
        return (min_val - tolerance) <= angle <= (max_val + tolerance)
