"""
简化版评估器
直接基于角度数据和稳定性进行评估,不依赖大模型
"""

from typing import Dict, List


class SimpleEvaluator:
    """简化版评估器"""
    
    def evaluate(self, stats: Dict, stability_score: float, 
              pose_name: str, pose_standards: Dict) -> Dict:
        """
        基于数据和规则进行评估
        
        Args:
            stats: 统计特征
            stability_score: 稳定性评分
            pose_name: 动作名称
            pose_standards: 动作标准库
            
        Returns:
            评估结果字典
        """
        # 1. 计算角度准确性 (40分)
        accuracy_score = self._calculate_accuracy(stats, pose_standards)
        
        # 2. 计算动作稳定性 (30分)
        stability_scaled_score = min(30, int(stability_score * 3))
        
        # 3. 计算整体协调性 (30分)
        coordination_score = self._calculate_coordination(stats, stability_score)
        
        # 总分
        total_score = accuracy_score + stability_scaled_score + coordination_score
        
        # 4. 识别主要问题
        problems = self._identify_problems(stats, pose_standards)
        
        # 5. 提供改进建议
        suggestions = self._generate_suggestions(problems, pose_standards)
        
        return {
            "success": True,
            "data": {
                "score": {
                    "total": total_score,
                    "accuracy": accuracy_score,
                    "stability": stability_scaled_score,
                    "coordination": coordination_score
                },
                "problems": problems,
                "suggestions": suggestions
            }
        }
    
    def _calculate_accuracy(self, stats: Dict, pose_standards: Dict) -> int:
        """计算角度准确性评分 (0-40分)"""
        if "mean" not in stats or not pose_standards or "angles" not in pose_standards:
            return 20  # 默认中等分数
        
        mean_angles = stats["mean"]
        standard_angles = pose_standards["angles"]
        
        # 匹配角度名称
        angle_mapping = {
            "left_knee": ["膝关节", "支撑腿膝关节", "前腿膝关节"],
            "right_knee": ["膝关节", "支撑腿膝关节", "前腿膝关节"],
            "left_hip": ["髋关节", "抬髋关节"],
            "right_hip": ["髋关节", "抬髋关节"],
            "spine_angle": ["脊柱角度", "脊柱延展"],
            "left_elbow": ["肩关节"],
            "right_elbow": ["肩关节"],
        }
        
        # 计算符合标准的角度数量
        compliant_count = 0
        total_checks = 0
        
        for measured_name, measured_value in mean_angles.items():
            for standard_name, angle_range in standard_angles.items():
                if standard_name in angle_mapping.get(measured_name, []):
                    total_checks += 1
                    min_val, max_val = angle_range
                    if min_val <= measured_value <= max_val:
                        compliant_count += 1
                    break
        
        if total_checks == 0:
            return 25  # 默认分数
        
        # 计算准确性得分
        accuracy_ratio = compliant_count / total_checks
        return int(accuracy_ratio * 40)
    
    def _calculate_coordination(self, stats: Dict, stability_score: float) -> int:
        """计算整体协调性评分 (0-30分)"""
        # 基于角度标准差来评估协调性
        if "std" not in stats:
            return 15  # 默认中等分数
        
        std_angles = stats["std"]
        avg_std = sum(std_angles.values()) / len(std_angles)
        
        # 标准差越小,动作越协调
        if avg_std < 2:
            return 28
        elif avg_std < 4:
            return 25
        elif avg_std < 6:
            return 20
        else:
            return 15
    
    def _identify_problems(self, stats: Dict, pose_standards: Dict) -> List[str]:
        """识别主要问题"""
        problems = []
        
        if "mean" not in stats or not pose_standards or "angles" not in pose_standards:
            return ["需要更多信息来分析问题"]
        
        mean_angles = stats["mean"]
        standard_angles = pose_standards["angles"]
        
        # 检查角度是否符合标准
        angle_mapping = {
            "left_knee": ["膝关节"],
            "right_knee": ["膝关节"],
            "left_hip": ["髋关节"],
            "right_hip": ["髋关节"],
            "spine_angle": ["脊柱角度", "脊柱延展"],
        }
        
        for measured_name, measured_value in mean_angles.items():
            for standard_name, angle_range in standard_angles.items():
                if standard_name in angle_mapping.get(measured_name, []):
                    min_val, max_val = angle_range
                    if measured_value < min_val:
                        problems.append(f"{standard_name}角度过小({measured_value:.1f}°,标准范围{min_val}-{max_val}°)")
                    elif measured_value > max_val:
                        problems.append(f"{standard_name}角度过大({measured_value:.1f}°,标准范围{min_val}-{max_val}°)")
                    break
        
        # 如果问题不足2个,添加常见问题
        if len(problems) < 2 and "common_errors" in pose_standards:
            common_errors = pose_standards["common_errors"]
            problems.extend(common_errors[:2 - len(problems)])
        
        return problems[:3]  # 最多3个问题
    
    def _generate_suggestions(self, problems: List[str], pose_standards: Dict) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if "common_errors" in pose_standards:
            common_errors = pose_standards["common_errors"]
            # 基于问题生成建议
            for problem in problems[:3]:
                if "膝关节" in problem:
                    suggestions.append("注意膝盖对齐,保持小腿与地面垂直")
                elif "髋关节" in problem:
                    suggestions.append("调整髋部位置,保持骨盆正位")
                elif "脊柱" in problem:
                    suggestions.append("保持脊柱延展,避免拱背或塌腰")
                elif "角度" in problem:
                    suggestions.append("微调角度,逐渐达到标准范围")
        
        # 如果建议不足2个,添加通用建议
        if len(suggestions) < 2:
            suggestions.extend([
                "多练习核心力量,提高身体稳定性",
                "在镜子前练习,及时纠正错误姿势"
            ][:2 - len(suggestions)])
        
        return suggestions[:3]  # 最多3条建议
