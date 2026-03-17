"""
Gradio主界面
用户交互界面
"""

import gradio as gr
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict
import json

from src.video_reader import VideoReader
from src.pose_detector import PoseDetector
from src.angle_calculator import AngleCalculator
from src.stats_calculator import StatsCalculator
from src.prompt_builder import PromptBuilder
from src.ollama_client import OllamaClient
from src.result_parser import ResultParser
from config.settings import POSE_STANDARDS


class YogaAssessmentApp:
    """瑜伽动作评估应用"""
    
    def __init__(self):
        # 初始化各模块
        self.video_reader = VideoReader()
        self.pose_detector = PoseDetector()
        self.angle_calculator = AngleCalculator()
        self.stats_calculator = StatsCalculator()
        self.prompt_builder = PromptBuilder()
        self.ollama_client = OllamaClient()
        self.result_parser = ResultParser()
        
        # 检查Ollama连接
        self.ollama_available = self.ollama_client.check_connection()
        if not self.ollama_available:
            print("警告: 无法连接到Ollama服务,部分功能将不可用")
    
    def assess_video(self, video_path: str, pose_name: str) -> Tuple:
        """
        主评估函数
        
        Args:
            video_path: 视频路径
            pose_name: 动作名称
            
        Returns:
            评估结果元组
        """
        try:
            # 1. 读取视频
            print(f"正在读取视频: {video_path}")
            video_info, frames = self.video_reader.read(video_path)
            
            # 2. 关键点检测
            print("正在检测关键点...")
            landmarks_seq = self.pose_detector.detect_sequence(frames)
            
            # 过滤无效帧
            valid_landmarks = [lm for lm in landmarks_seq if lm is not None]
            if not valid_landmarks:
                return None, None, None, "错误: 未检测到有效的人体关键点,请确保视频中有人物且光线充足"
            
            # 3. 角度计算
            print("正在计算角度...")
            angles_seq = self.angle_calculator.compute_all(landmarks_seq)
            
            # 4. 统计分析
            print("正在分析统计数据...")
            stats = self.stats_calculator.compute(angles_seq)
            stability_score = self.stats_calculator.compute_stability(landmarks_seq)
            
            # 5. 构建提示词
            pose_standard = POSE_STANDARDS.get(pose_name)
            prompt = self.prompt_builder.build(stats, stability_score, pose_name, pose_standard)
            
            # 6. 调用大模型评估
            assessment_result = None
            if self.ollama_available:
                print("正在调用大模型评估...")
                try:
                    # 使用中间帧作为参考图像
                    middle_idx = len(frames) // 2
                    key_frame = frames[middle_idx]
                    
                    model_response = self.ollama_client.generate(prompt, key_frame)
                    assessment_result = self.result_parser.parse(model_response)
                except Exception as e:
                    print(f"模型评估失败: {e}")
                    assessment_result = self._create_fallback_result(stats, stability_score)
            else:
                print("使用备用评估方法...")
                assessment_result = self._create_fallback_result(stats, stability_score)
            
            # 7. 绘制骨骼标注视频
            print("正在生成标注视频...")
            annotated_frames = []
            for i, (frame, landmarks) in enumerate(zip(frames, landmarks_seq)):
                if landmarks:
                    annotated = self.pose_detector.draw_landmarks(frame, landmarks)
                else:
                    annotated = frame
                annotated_frames.append(annotated)
            
            # 保存标注视频(临时文件)
            output_dir = Path("data/processed")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            video_name = Path(video_path).stem
            annotated_video_path = str(output_dir / f"{video_name}_annotated.mp4")
            
            import cv2
            height, width = frames[0].shape[:2]
            fps = video_info.get("fps", 30)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(annotated_video_path, fourcc, fps, (width, height))
            
            for frame in annotated_frames:
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame_bgr)
            
            out.release()
            
            # 8. 生成评估报告
            report = self._generate_report(video_info, stats, stability_score, 
                                         assessment_result, pose_name)
            
            # 9. 创建可视化图表
            try:
                from utils.visualization import plot_score_breakdown, plot_angle_over_time
                
                # 生成分数图表
                score_chart = plot_score_breakdown(assessment_result["data"]["score"])
                
                # 生成角度变化图
                angle_names = ["left_knee", "right_knee", "left_hip", "right_hip", "spine_angle"]
                angle_chart = plot_angle_over_time(angles_seq, angle_names)
                
                return annotated_video_path, score_chart, angle_chart, report
            
            except Exception as e:
                print(f"生成可视化图表失败: {e}")
                return annotated_video_path, None, None, report
        
        except Exception as e:
            error_msg = f"评估过程中发生错误: {str(e)}"
            print(error_msg)
            return None, None, None, error_msg
    
    def _create_fallback_result(self, stats: Dict, stability_score: float) -> Dict:
        """创建备用评估结果(当大模型不可用时)"""
        score = {
            "total": int(min(100, max(60, stability_score * 10))),
            "accuracy": 25,
            "stability": int(min(30, stability_score * 3)),
            "coordination": 20
        }
        
        return {
            "success": True,
            "data": {
                "score": score,
                "problems": [
                    "由于大模型服务不可用,无法进行详细问题分析"
                ],
                "suggestions": [
                    "请确保Ollama服务正在运行",
                    "建议咨询专业瑜伽教练获取详细指导"
                ]
            }
        }
    
    def _generate_report(self, video_info: Dict, stats: Dict, 
                        stability_score: float, assessment_result: Dict,
                        pose_name: str) -> str:
        """生成文本评估报告"""
        if not assessment_result["success"]:
            return f"评估失败: {assessment_result.get('error', '未知错误')}"
        
        data = assessment_result["data"]
        score = data["score"]
        
        lines = [
            f"# 瑜伽动作评估报告",
            f"",
            f"## 基本信息",
            f"- 动作名称: {pose_name}",
            f"- 视频分辨率: {video_info.get('resolution', '未知')}",
            f"- 视频时长: {video_info.get('duration', 0):.1f}秒",
            f"- 总帧数: {video_info.get('frame_count', 0)}帧",
            f"",
            f"## 综合评分",
            f"**总分: {score['total']}/100**",
            f"",
            f"### 详细评分",
            f"- 角度准确性: {score['accuracy']}/40",
            f"- 动作稳定性: {score['stability']}/30",
            f"- 整体协调性: {score['coordination']}/30",
            f"",
            f"### 关节角度统计",
        ]
        
        # 添加角度统计
        for angle_name, mean_value in stats.get("mean", {}).items():
            std_value = stats.get("std", {}).get(angle_name, 0)
            lines.append(f"- {angle_name}: {mean_value:.1f}° ± {std_value:.1f}°")
        
        lines.extend([
            f"",
            f"### 稳定性评分",
            f"动作稳定性: {stability_score:.1f}/10",
            f"",
            f"## 主要问题",
        ])
        
        for i, problem in enumerate(data["problems"], 1):
            lines.append(f"{i}. {problem}")
        
        lines.extend([
            f"",
            f"## 改进建议",
        ])
        
        for i, suggestion in enumerate(data["suggestions"], 1):
            lines.append(f"{i}. {suggestion}")
        
        return "\n".join(lines)
    
    def create_interface(self):
        """创建Gradio界面"""
        with gr.Blocks(title="瑜伽动作评估系统") as interface:
            gr.Markdown("# 🧘 瑜伽动作评估系统")
            gr.Markdown("上传瑜伽视频,选择动作类型,获取专业的AI评估报告")
            
            with gr.Row():
                with gr.Column(scale=1):
                    video_input = gr.Video(
                        label="上传视频",
                        sources=["upload"],
                        format=["mp4", "avi", "mov"]
                    )
                    pose_select = gr.Dropdown(
                        choices=list(POSE_STANDARDS.keys()),
                        value="下犬式",
                        label="选择动作类型"
                    )
                    submit_btn = gr.Button("开始评估", variant="primary", size="lg")
                    
                    # 添加动作说明
                    pose_info = gr.Markdown("### 动作说明")
                    
                    # 更新动作说明的函数
                    def update_pose_info(pose_name):
                        pose = POSE_STANDARDS.get(pose_name, {})
                        desc = pose.get("description", "暂无说明")
                        common_errors = pose.get("common_errors", [])
                        errors_text = "\n".join([f"- {e}" for e in common_errors])
                        
                        return f"**{pose_name}**\n\n{desc}\n\n**常见错误:**\n{errors_text}"
                    
                    pose_select.change(
                        update_pose_info,
                        inputs=[pose_select],
                        outputs=[pose_info]
                    )
                    # 初始化显示第一个动作的说明
                    interface.load(
                        update_pose_info,
                        inputs=[pose_select],
                        outputs=[pose_info]
                    )
                
                with gr.Column(scale=2):
                    with gr.Tab("评估结果"):
                        annotated_video = gr.Video(label="标注视频")
                        
                        with gr.Row():
                            score_chart = gr.Image(label="评分分布")
                            angle_chart = gr.Image(label="角度变化曲线")
                        
                        report_text = gr.Markdown(label="评估报告")
                    
                    with gr.Tab("使用说明"):
                        gr.Markdown("""
                        ## 使用说明
                        
                        1. **上传视频**: 选择一个瑜伽动作视频文件(支持mp4, avi, mov格式)
                        
                        2. **选择动作**: 从下拉菜单中选择对应的瑜伽动作类型
                        
                        3. **开始评估**: 点击"开始评估"按钮,系统将自动分析视频
                        
                        4. **查看结果**: 
                           - 标注视频: 显示骨骼连线
                           - 评分分布: 展示各项得分
                           - 角度变化: 关键关节角度随时间变化
                           - 评估报告: 详细的文字报告
                        
                        ## 系统要求
                        
                        - Python 3.9+
                        - Ollama服务(用于AI评估,可选)
                        - 建议使用NVIDIA GPU加速
                        """)
            
            # 绑定事件
            submit_btn.click(
                fn=self.assess_video,
                inputs=[video_input, pose_select],
                outputs=[annotated_video, score_chart, angle_chart, report_text],
                api_name="assess"
            )
        
        return interface


def main():
    """主函数"""
    app = YogaAssessmentApp()
    interface = app.create_interface()
    
    print("启动瑜伽动作评估系统...")
    
    interface.launch(
        server_name="localhost",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    main()
