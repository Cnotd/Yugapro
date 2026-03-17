"""
统计分析模块
计算统计特征和稳定性评分
"""

import numpy as np
from typing import List, Dict, Optional


class StatsCalculator:
    """统计分析器"""
    
    def __init__(self):
        pass
    
    def compute(self, angles_seq: List[Dict]) -> Dict:
        """
        计算统计特征
        
        Args:
            angles_seq: 角度序列
            
        Returns:
            stats: 统计特征字典
        """
        stats = {
            "mean": {},
            "std": {},
            "min": {},
            "max": {},
            "range": {}
        }
        
        # 收集所有有效的角度值
        angle_values = {}
        for angles in angles_seq:
            for key, value in angles.items():
                if value is not None:
                    if key not in angle_values:
                        angle_values[key] = []
                    angle_values[key].append(value)
        
        # 计算各项统计指标
        for key, values in angle_values.items():
            stats["mean"][key] = float(np.mean(values))
            stats["std"][key] = float(np.std(values))
            stats["min"][key] = float(np.min(values))
            stats["max"][key] = float(np.max(values))
            stats["range"][key] = float(np.max(values) - np.min(values))
        
        return stats
    
    def compute_stability(self, landmarks_seq: List[List[Dict]], 
                         important_points: Optional[List[int]] = None) -> float:
        """
        计算稳定性评分 (0-10分)
        
        Args:
            landmarks_seq: 关键点序列
            important_points: 重要关键点索引列表
            
        Returns:
            stability_score: 稳定性评分
        """
        if important_points is None:
            # 默认使用肩膀和髋部作为稳定性参考点
            important_points = [11, 12, 23, 24]  # 左肩、右肩、左髋、右髋
        
        # 计算每个重要点的移动幅度
        point_movements = []
        
        for point_idx in important_points:
            positions = []
            
            for landmarks in landmarks_seq:
                if landmarks is not None:
                    for lm in landmarks:
                        if lm["id"] == point_idx:
                            positions.append((lm["x"], lm["y"]))
                            break
            
            # 计算移动距离
            if len(positions) > 1:
                distances = []
                for i in range(1, len(positions)):
                    dx = positions[i][0] - positions[i-1][0]
                    dy = positions[i][1] - positions[i-1][1]
                    distance = np.sqrt(dx*dx + dy*dy)
                    distances.append(distance)
                
                if distances:
                    avg_movement = np.mean(distances)
                    std_movement = np.std(distances)
                    point_movements.append(avg_movement + std_movement)
        
        # 综合计算稳定性
        if point_movements:
            total_movement = np.mean(point_movements)
            # 移动越小越稳定,转换为0-10分
            stability_score = max(0, min(10, 10 - total_movement * 50))
        else:
            stability_score = 5.0  # 默认中等稳定性
        
        return round(stability_score, 2)
    
    def compute_angle_stability(self, angles_seq: List[Dict], 
                               angle_names: List[str]) -> Dict[str, float]:
        """
        计算各个角度的稳定性
        
        Args:
            angles_seq: 角度序列
            angle_names: 需要评估的角度名称列表
            
        Returns:
            stability_scores: 各角度的稳定性评分字典
        """
        stability_scores = {}
        
        for angle_name in angle_names:
            values = []
            for angles in angles_seq:
                if angle_name in angles and angles[angle_name] is not None:
                    values.append(angles[angle_name])
            
            if values:
                # 计算标准差作为不稳定性指标
                std = np.std(values)
                # 标准差越小越稳定,转换为0-10分
                stability = max(0, min(10, 10 - std / 2))
                stability_scores[angle_name] = round(stability, 2)
            else:
                stability_scores[angle_name] = 0.0
        
        return stability_scores
    
    def check_angle_compliance(self, stats: Dict, pose_standards: Dict,
                              tolerance: float = 5) -> Dict[str, bool]:
        """
        检查角度是否符合标准
        
        Args:
            stats: 统计特征
            pose_standards: 动作标准库
            tolerance: 容差(度)
            
        Returns:
            compliance: 各角度是否符合标准
        """
        compliance = {}
        
        for angle_name, angle_range in pose_standards["angles"].items():
            # 查找对应的角度统计值
            mean_angle = None
            for stat_angle in stats["mean"]:
                if angle_name in stat_angle or stat_angle in angle_name:
                    mean_angle = stats["mean"][stat_angle]
                    break
            
            if mean_angle is not None:
                min_val, max_val = angle_range
                compliance[angle_name] = (min_val - tolerance) <= mean_angle <= (max_val + tolerance)
            else:
                compliance[angle_name] = False
        
        return compliance
    
    def get_angle_changes_over_time(self, angles_seq: List[Dict], 
                                    angle_name: str) -> List[float]:
        """
        获取某角度随时间的变化曲线
        
        Args:
            angles_seq: 角度序列
            angle_name: 角度名称
            
        Returns:
            angle_values: 角度值列表
        """
        angle_values = []
        
        for angles in angles_seq:
            if angle_name in angles and angles[angle_name] is not None:
                angle_values.append(angles[angle_name])
        
        return angle_values
    
    def compute_overall_score(self, stats: Dict, stability_score: float,
                             compliance: Dict) -> Dict[str, float]:
        """
        计算综合评分
        
        Args:
            stats: 统计特征
            stability_score: 稳定性评分
            compliance: 角度符合性
            
        Returns:
            scores: 各维度评分
        """
        # 角度准确性评分 (根据符合性)
        if compliance:
            accuracy_compliance = sum(1 for v in compliance.values() if v)
            accuracy_score = (accuracy_compliance / len(compliance)) * 10
        else:
            accuracy_score = 5.0
        
        # 综合评分
        overall_score = (accuracy_score * 0.6 + stability_score * 0.4)
        
        return {
            "overall": round(overall_score, 2),
            "accuracy": round(accuracy_score, 2),
            "stability": round(stability_score, 2)
        }
