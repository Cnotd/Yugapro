"""
快速演示 - 使用预设数据测试 Ollama 完整流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.prompt_builder import PromptBuilder
from src.ollama_client import OllamaClient
from src.result_parser import ResultParser
from config.settings import POSE_STANDARDS


def quick_demo():
    """快速演示"""
    print("\n" + "="*70)
    print(" "*15 + "Ollama 完整流程演示")
    print("="*70)

    # 步骤1: 初始化
    print("\n[步骤 1/5] 初始化模块...")
    prompt_builder = PromptBuilder()
    ollama_client = OllamaClient()
    result_parser = ResultParser()
    print("        模块初始化完成")

    # 步骤2: 检查连接
    print("\n[步骤 2/5] 检查 Ollama 服务...")
    if not ollama_client.check_connection():
        print("        错误: Ollama 服务不可用")
        return
    print("        Ollama 服务连接正常")

    # 步骤3: 模拟数据
    print("\n[步骤 3/5] 准备测试数据...")
    test_stats = {
        'mean': {
            'left_elbow': 168.5,
            'right_elbow': 155.2,
            'left_knee': 172.8,
            'right_knee': 168.3,
            'left_hip': 88.0,
            'right_hip': 92.5,
            'left_shoulder': 175.0,
            'right_shoulder': 172.0
        },
        'std': {
            'left_elbow': 3.2,
            'right_elbow': 4.5,
            'left_knee': 2.1,
            'right_knee': 3.8,
            'left_hip': 5.0,
            'right_hip': 4.2,
            'left_shoulder': 2.5,
            'right_shoulder': 3.0
        }
    }
    test_stability = 0.78
    print("        测试数据准备完成")
    print(f"        稳定性评分: {test_stability:.2f}")

    # 步骤4: 构建提示词
    print("\n[步骤 4/5] 构建 AI 评估提示词...")
    pose_name = "下犬式"
    pose_standard = POSE_STANDARDS.get(pose_name)
    prompt = prompt_builder.build(test_stats, test_stability, pose_name, pose_standard)
    print(f"        提示词构建完成 (长度: {len(prompt)} 字符)")

    # 步骤5: 调用模型
    print("\n[步骤 5/5] 调用 Ollama 模型进行评估...")
    print("        正在等待模型响应...")

    try:
        model_response = ollama_client.generate(prompt)
        print(f"        模型响应成功 (长度: {len(model_response)} 字符)")

        # 显示结果
        print("\n" + "="*70)
        print(" "*10 + "模型响应内容")
        print("="*70)
        print(model_response)
        print("="*70)

        # 解析结果
        print("\n正在解析评估结果...")
        assessment_result = result_parser.parse(model_response)

        if assessment_result.get('success', False):
            print("\n[成功] 评估结果解析成功!")
            result_data = assessment_result['data']
            score = result_data['score']

            print("\n" + "="*70)
            print(" "*20 + "最终评估报告")
            print("="*70)
            print(f"\n  总分: {score['total']}/100")
            print(f"  {'─'*60}")
            print(f"  角度准确性: {score['accuracy']}/40  分")
            print(f"  动作稳定性: {score['stability']}/30  分")
            print(f"  整体协调性: {score['coordination']}/30  分")

            if result_data['problems']:
                print(f"\n  主要问题:")
                for i, prob in enumerate(result_data['problems'], 1):
                    print(f"    {i}. {prob}")

            if result_data['suggestions']:
                print(f"\n  改进建议:")
                for i, sugg in enumerate(result_data['suggestions'], 1):
                    print(f"    {i}. {sugg}")

            print("="*70)
        else:
            print("\n[警告] 无法解析模型响应")
            print(f"  错误: {assessment_result.get('error', 'Unknown')}")

    except Exception as e:
        print(f"\n[错误] 模型调用失败: {str(e)}")

    print("\n" + "="*70)
    print(" "*25 + "演示完成!")
    print("="*70 + "\n")


if __name__ == "__main__":
    quick_demo()
