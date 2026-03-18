"""
完整流程测试脚本
测试从视频上传到评估的完整流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.video_reader import VideoReader
from src.pose_detector import PoseDetector
from src.angle_calculator import AngleCalculator
from src.stats_calculator import StatsCalculator
from src.prompt_builder import PromptBuilder
from src.ollama_client import OllamaClient
from src.result_parser import ResultParser
from src.simple_evaluator import SimpleEvaluator
from config.settings import POSE_STANDARDS
import json


def test_full_pipeline():
    """测试完整流程"""
    print("="*60)
    print("完整流程测试")
    print("="*60)

    # 初始化模块
    print("\n[1/8] 初始化各模块...")
    video_reader = VideoReader()
    pose_detector = PoseDetector()
    angle_calculator = AngleCalculator()
    stats_calculator = StatsCalculator()
    prompt_builder = PromptBuilder()
    ollama_client = OllamaClient()
    result_parser = ResultParser()
    simple_evaluator = SimpleEvaluator()
    print("[OK] 所有模块初始化完成")

    # 检查Ollama连接
    print("\n[2/8] 检查Ollama服务连接...")
    ollama_available = ollama_client.check_connection()
    if not ollama_available:
        print("[FAIL] Ollama服务不可用")
        return
    print("[OK] Ollama服务连接正常")

    # 选择测试视频
    print("\n[3/8] 查找测试视频...")
    test_video_dir = "data/videos/Ardhakati_Chakrasana"
    if os.path.exists(test_video_dir):
        video_files = [f for f in os.listdir(test_video_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
        if video_files:
            video_path = os.path.join(test_video_dir, video_files[0])
            print(f"[OK] 找到测试视频: {video_files[0]}")
        else:
            print("[WARN] 未找到视频文件,使用临时视频...")
            video_path = "data/temp/Ardhakati_Chakrasana/Ardhakati Chakrasana Right Step Angle 1_annotated.mp4"
            if not os.path.exists(video_path):
                print("[FAIL] 未找到任何测试视频")
                return
    else:
        print(f"[WARN] 目录不存在: {test_video_dir}")

    # 读取视频
    print("\n[4/8] 读取视频...")
    video_info, frames = video_reader.read(video_path)
    print(f"[OK] 视频信息: {video_info}")
    print(f"[OK] 读取帧数: {len(frames)}")

    # 关键点检测
    print("\n[5/8] 进行关键点检测...")
    landmarks_seq = pose_detector.detect_sequence(frames)
    valid_landmarks = [lm for lm in landmarks_seq if lm is not None]
    print(f"[OK] 检测完成,有效帧数: {len(valid_landmarks)}/{len(landmarks_seq)}")

    # 角度计算
    print("\n[6/8] 计算关节角度...")
    angles_seq = angle_calculator.compute_all(landmarks_seq)
    print(f"[OK] 角度计算完成")

    # 统计分析
    print("\n[7/8] 统计分析...")
    stats = stats_calculator.compute(angles_seq)
    stability_score = stats_calculator.compute_stability(landmarks_seq)
    print(f"[OK] 统计分析完成")
    print(f"      - 平均角度: {json.dumps(stats['mean'], indent=12, ensure_ascii=False)}")
    print(f"      - 稳定性评分: {stability_score:.2f}")

    # 构建提示词并调用模型
    print("\n[8/8] 模型评估...")
    pose_name = "下犬式"
    pose_standard = POSE_STANDARDS.get(pose_name)
    prompt = prompt_builder.build(stats, stability_score, pose_name, pose_standard)

    print(f"\n提示词预览:")
    print("-" * 60)
    print(prompt[:300] + "...")
    print("-" * 60)

    try:
        middle_idx = len(frames) // 2
        key_frame = frames[middle_idx]
        print(f"\n[正在调用Ollama模型...]")
        model_response = ollama_client.generate(prompt, key_frame)
        print(f"[OK] 模型返回内容长度: {len(model_response)} 字符")

        print(f"\n模型响应预览:")
        print("-" * 60)
        print(model_response[:500])
        print("-" * 60)

        # 解析结果
        print(f"\n[正在解析模型响应...]")
        assessment_result = result_parser.parse(model_response)

        if assessment_result.get('success', False):
            print("[OK] 模型评估成功")
            result_data = assessment_result['data']
            score = result_data['score']

            print(f"\n评估结果:")
            print("-" * 60)
            print(f"总分: {score['total']}/100")
            print(f"  - 角度准确性: {score['accuracy']}/40")
            print(f"  - 动作稳定性: {score['stability']}/30")
            print(f"  - 整体协调性: {score['coordination']}/30")
            print(f"\n主要问题:")
            for prob in result_data['problems']:
                print(f"  - {prob}")
            print(f"\n改进建议:")
            for sugg in result_data['suggestions']:
                print(f"  - {sugg}")
            print("-" * 60)
        else:
            print(f"[WARN] 模型解析失败,使用简化评估")
            print(f"解析错误: {assessment_result.get('error', 'Unknown')}")

            # 使用简化评估器
            assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
            result_data = assessment_result['data']
            score = result_data['score']

            print(f"\n简化评估结果:")
            print("-" * 60)
            print(f"总分: {score['total']}/100")
            print(f"  - 角度准确性: {score['accuracy']}/40")
            print(f"  - 动作稳定性: {score['stability']}/30")
            print(f"  - 整体协调性: {score['coordination']}/30")
            print("-" * 60)

    except Exception as e:
        print(f"[WARN] Ollama调用失败: {str(e)}")
        print("使用简化评估模式")

        assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
        result_data = assessment_result['data']
        score = result_data['score']

        print(f"\n简化评估结果:")
        print("-" * 60)
        print(f"总分: {score['total']}/100")
        print(f"  - 角度准确性: {score['accuracy']}/40")
        print(f"  - 动作稳定性: {score['stability']}/30")
        print(f"  - 整体协调性: {score['coordination']}/30")
        print("-" * 60)

    print("\n" + "="*60)
    print("完整流程测试完成!")
    print("="*60)


if __name__ == "__main__":
    test_full_pipeline()
