"""
提示词构建模块
构建用于大模型评估的结构化提示词
"""

import json
from typing import Dict, Optional


class PromptBuilder:
    """提示词构建器"""
    
    def __init__(self):
        self.role = "你是一位专业的瑜伽教练,拥有10年以上的教学经验,擅长瑜伽动作评估和指导。"
        self.task = "请根据用户提供的数据,对用户的瑜伽动作进行专业评估。"
    
    def build(self, stats: Dict, stability_score: float, 
             pose_name: str, pose_standards: Optional[Dict] = None) -> str:
        """
        构建评估提示词
        
        Args:
            stats: 统计特征
            stability_score: 稳定性评分
            pose_name: 动作名称
            pose_standards: 动作标准库
            
        Returns:
            prompt: 结构化提示词
        """
        prompt_parts = [
            self._build_role_section(),
            self._build_pose_info_section(pose_name, pose_standards),
            self._build_data_section(stats, stability_score),
            self._build_instruction_section()
        ]
        
        return "\n\n".join(prompt_parts)
    
    def _build_role_section(self) -> str:
        """构建角色设定部分"""
        return f"""# 角色设定
{self.role}

你的任务: {self.task}"""
    
    def _build_pose_info_section(self, pose_name: str, 
                                pose_standards: Optional[Dict] = None) -> str:
        """构建动作信息部分"""
        section = f"# 动作信息\n动作名称: {pose_name}"
        
        if pose_standards:
            section += f"\n动作描述: {pose_standards.get('description', '')}"
            
            if "angles" in pose_standards:
                section += "\n标准角度范围:"
                for angle_name, angle_range in pose_standards["angles"].items():
                    section += f"\n  - {angle_name}: {angle_range[0]}° - {angle_range[1]}°"
            
            if "common_errors" in pose_standards:
                section += "\n常见错误:"
                for error in pose_standards["common_errors"]:
                    section += f"\n  - {error}"
        
        return section
    
    def _build_data_section(self, stats: Dict, stability_score: float) -> str:
        """构建数据展示部分"""
        section = "# 评估数据"
        
        # 稳定性评分
        section += f"\n稳定性评分: {stability_score}/10"
        
        # 角度统计
        if "mean" in stats:
            section += "\n各关节角度平均值:"
            for angle_name, value in stats["mean"].items():
                section += f"\n  - {angle_name}: {value:.2f}°"
        
        if "std" in stats:
            section += "\n各关节角度标准差(稳定性):"
            for angle_name, value in stats["std"].items():
                section += f"\n  - {angle_name}: {value:.2f}°"
        
        if "min" in stats and "max" in stats:
            section += "\n各关节角度范围:"
            for angle_name in stats["mean"].keys():
                if angle_name in stats["min"] and angle_name in stats["max"]:
                    section += f"\n  - {angle_name}: {stats['min'][angle_name]:.2f}° - {stats['max'][angle_name]:.2f}°"
        
        return section
    
    def _build_instruction_section(self) -> str:
        """构建评估指令部分"""
        return """# 评估要求
请根据上述数据,提供以下评估结果:

1. 评分 (总分0-100分)
   - 角度准确性 (0-40分): 主要关节角度是否在标准范围内
   - 动作稳定性 (0-30分): 动作是否稳定,是否有过大晃动
   - 整体协调性 (0-30分): 动作是否流畅,身体各部位是否协调

2. 主要问题 (2-3个)
   - 列出用户动作中最明显的2-3个问题
   - 每个问题要具体,不要泛泛而谈

3. 改进建议 (2-3条)
   - 针对每个问题给出具体、可操作的改进建议
   - 建议要实用,用户可以直接实施

输出JSON格式,只返回JSON,不要包含其他文字:

{
  "score": {
    "total": 85,
    "accuracy": 35,
    "stability": 25,
    "coordination": 25
  },
  "problems": [
    "问题1描述",
    "问题2描述",
    "问题3描述"
  ],
  "suggestions": [
    "建议1",
    "建议2",
    "建议3"
  ]
}

注意: 所有分数必须是整数,总分 = accuracy + stability + coordination"""
    
    def build_with_image(self, stats: Dict, stability_score: float,
                        pose_name: str, pose_standards: Optional[Dict] = None) -> str:
        """
        构建带图像的提示词
        
        Args:
            stats: 统计特征
            stability_score: 稳定性评分
            pose_name: 动作名称
            pose_standards: 动作标准库
            
        Returns:
            prompt: 结构化提示词
        """
        prompt = self.build(stats, stability_score, pose_name, pose_standards)
        
        # 添加图像说明
        image_note = """

# 图像说明
我还会提供一张动作的参考图像,请结合图像和上述数据进行综合评估。

在评估时,请同时考虑:
1. 图像中显示的姿态
2. 统计数据中提供的角度信息
3. 动作标准库中的标准

请给出更准确、专业的评估结果。"""
        
        return prompt + image_note
    
    def get_system_prompt(self) -> str:
        """获取系统提示词(用于设置模型行为)"""
        return """你是一位专业的瑜伽教练和动作分析师。你需要:
1. 客观、准确地评估用户的瑜伽动作
2. 提供具体、可操作的改进建议
3. 使用专业但易懂的语言
4. 严格按照要求的JSON格式输出结果
5. 评估要公平公正,基于数据和标准"""
