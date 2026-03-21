"""
提示词构建模块 (英文版)
构建用于大模型评估的结构化提示词
"""

import json
from typing import Dict, Optional


class PromptBuilder:
    """提示词构建器"""

    def __init__(self):
        self.role = "You are a professional yoga instructor with 10+ years of experience specializing in yoga pose assessment and guidance."
        self.task = "Assess the user's yoga pose based on provided data."

    def build_with_graph(self, pose_graph, pose_name: str, pose_standards: Optional[Dict] = None) -> str:
        """
        使用姿态图信息构建评估提示词

        Args:
            pose_graph: PoseGraph对象，包含完整的关节图信息
            pose_name: 动作名称
            pose_standards: 动作标准库

        Returns:
            prompt: 结构化提示词
        """
        prompt_parts = [
            self._build_role_section(),
            self._build_pose_info_section(pose_name, pose_standards),
            self._build_graph_data_section(pose_graph),
            self._build_instruction_section()
        ]

        return "\n\n".join(prompt_parts)

    def build(self, stats: Dict, stability_score: float,
             pose_name: str, pose_standards: Optional[Dict] = None) -> str:
        """
        构建评估提示词（传统方法，使用角度统计）

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
        return f"""# Role
{self.role}

Your task: {self.task}"""

    def _build_pose_info_section(self, pose_name: str,
                                pose_standards: Optional[Dict] = None) -> str:
        """构建动作信息部分"""
        section = f"# Pose Information\nPose Name: {pose_name}"

        if pose_standards:
            section += f"\nDescription: {pose_standards.get('description', '')}"

            if "angles" in pose_standards:
                section += "\nStandard Angle Ranges:"
                for angle_name, angle_range in pose_standards["angles"].items():
                    section += f"\n  - {angle_name}: {angle_range[0]}° - {angle_range[1]}°"

            if "common_errors" in pose_standards:
                section += "\nCommon Errors:"
                for error in pose_standards["common_errors"]:
                    section += f"\n  - {error}"

        return section

    def _build_data_section(self, stats: Dict, stability_score: float) -> str:
        """构建数据展示部分"""
        section = "# Assessment Data"

        # 稳定性评分
        section += f"\nStability Score: {stability_score}/10"

        # 角度统计
        if "mean" in stats:
            section += "\nAverage Joint Angles:"
            for angle_name, value in stats["mean"].items():
                section += f"\n  - {angle_name}: {value:.2f}°"

        if "std" in stats:
            section += "\nJoint Angle Standard Deviation (Stability):"
            for angle_name, value in stats["std"].items():
                section += f"\n  - {angle_name}: {value:.2f}°"

        if "min" in stats and "max" in stats:
            section += "\nJoint Angle Ranges:"
            for angle_name in stats["mean"].keys():
                if angle_name in stats["min"] and angle_name in stats["max"]:
                    section += f"\n  - {angle_name}: {stats['min'][angle_name]:.2f}° - {stats['max'][angle_name]:.2f}°"

        return section

    def _build_graph_data_section(self, pose_graph) -> str:
        """构建姿态图数据部分"""
        descriptor = pose_graph.get_graph_descriptor()
        text_desc = pose_graph.to_text_description()

        section = "# Pose Graph Information"
        section += "\n\n" + text_desc
        section += "\n\nGraph Statistics:"
        section += f"\n- Number of joints: {descriptor['graph_stats']['num_nodes']}"
        section += f"\n- Number of connections: {descriptor['graph_stats']['num_edges']}"
        section += f"\n- Average visibility: {descriptor['graph_stats']['avg_visibility']:.2f}"
        section += f"\n- Maximum limb span: {descriptor['graph_stats']['max_distance']:.3f}"
        section += f"\n- Minimum limb span: {descriptor['graph_stats']['min_distance']:.3f}"
        section += f"\n- Average distance: {descriptor['graph_stats']['avg_distance']:.3f}"

        return section

    def _build_instruction_section(self) -> str:
        """构建评估指令部分"""
        return """# Assessment Requirements
Based on the above data, provide the following assessment:

1. Scoring (Total 0-100)
   - Angle Accuracy (0-40): Whether main joint angles are within standard ranges
   - Movement Stability (0-30): Whether movement is stable without excessive shaking
   - Overall Coordination (0-30): Whether movement is smooth and body parts coordinated

2. Main Problems (2-3 items)
   - List the 2-3 most obvious problems in the user's pose
   - Each problem should be specific, not general

3. Improvement Suggestions (2-3 items)
   - Provide specific, actionable improvement suggestions for each problem
   - Suggestions should be practical and directly implementable

# Output Format
You MUST return ONLY a valid JSON object. Do not include any text before or after the JSON. Do not use markdown code blocks. Do not add comments.

JSON format:
{"score":{"total":85,"accuracy":35,"stability":25,"coordination":25},"problems":["Problem 1","Problem 2","Problem 3"],"suggestions":["Suggestion 1","Suggestion 2","Suggestion 3"]}

Note: All scores are integers and must sum to total = accuracy + stability + coordination."""

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

# Image Information
I will also provide a reference image of the pose. Please combine the image and the above data for a comprehensive assessment.

When assessing, please consider simultaneously:
1. The pose shown in the image
2. The angle information provided in the statistical data
3. The standards in the pose standard library

Please provide a more accurate and professional assessment result."""

        return prompt + image_note

    def get_system_prompt(self) -> str:
        """获取系统提示词(用于设置模型行为)"""
        return """You are a professional yoga instructor and movement analyst. You need to:
1. Objectively and accurately assess the user's yoga poses
2. Provide specific, actionable improvement suggestions
3. Use professional but accessible language
4. Output results strictly in the required JSON format
5. Assess fairly and justly based on data and standards"""
