"""
Ollama 集成测试 - 快速版本
只测试 Ollama 调用部分
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.prompt_builder import PromptBuilder
from src.ollama_client import OllamaClient
from src.result_parser import ResultParser
from config.settings import POSE_STANDARDS


def test_ollama_integration():
    """测试 Ollama 集成"""
    print("="*60)
    print("Ollama 集成测试")
    print("="*60)

    # 模拟统计数据
    mock_stats = {
        'mean': {
            'left_elbow': 170.5,
            'right_elbow': 155.2,
            'left_knee': 172.8,
            'right_knee': 168.3,
            'left_hip': 85.0,
            'right_hip': 88.5,
            'left_shoulder': 175.0,
            'right_shoulder': 170.0
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

    mock_stability = 0.85

    # 初始化模块
    print("\n[1/4] 初始化模块...")
    prompt_builder = PromptBuilder()
    ollama_client = OllamaClient()
    result_parser = ResultParser()
    print("[OK] 模块初始化完成")

    # 检查连接
    print("\n[2/4] 检查 Ollama 连接...")
    if not ollama_client.check_connection():
        print("[FAIL] Ollama 服务不可用")
        return
    print("[OK] Ollama 连接正常")

    # 列出模型
    print("\n[3/4] 列出可用模型...")
    models = ollama_client.list_models()
    print(f"[OK] 找到 {len(models)} 个模型:")
    for model in models:
        print(f"  - {model.get('name', 'Unknown')}")

    # 构建提示词
    print("\n[4/4] 测试完整评估流程...")
    pose_name = "下犬式"
    pose_standard = POSE_STANDARDS.get(pose_name)
    prompt = prompt_builder.build(mock_stats, mock_stability, pose_name, pose_standard)

    print(f"\n提示词构建完成 (长度: {len(prompt)} 字符)")
    print(f"\n提示词预览:")
    print("-" * 60)
    print(prompt[:400] + "...")
    print("-" * 60)

    # 调用模型 (不带图片)
    print(f"\n[正在调用 Ollama 模型...]")
    try:
        model_response = ollama_client.generate(prompt)
        print(f"[OK] 模型返回成功 (长度: {len(model_response)} 字符)")

        print(f"\n模型完整响应:")
        print("=" * 60)
        print(model_response)
        print("=" * 60)

        # 解析结果
        print(f"\n[正在解析响应...]")
        assessment_result = result_parser.parse(model_response)

        if assessment_result.get('success', False):
            print("[OK] 解析成功!")
            result_data = assessment_result['data']
            score = result_data['score']

            print(f"\n评估结果:")
            print("-" * 60)
            print(f"总分: {score['total']}/100")
            print(f"  - 角度准确性: {score['accuracy']}/40")
            print(f"  - 动作稳定性: {score['stability']}/30")
            print(f"  - 整体协调性: {score['coordination']}/30")
            print(f"\n主要问题 ({len(result_data['problems'])}个):")
            for prob in result_data['problems']:
                print(f"  - {prob}")
            print(f"\n改进建议 ({len(result_data['suggestions'])}个):")
            for sugg in result_data['suggestions']:
                print(f"  - {sugg}")
            print("-" * 60)
        else:
            print(f"[WARN] 解析失败")
            print(f"错误: {assessment_result.get('error', 'Unknown')}")

    except Exception as e:
        print(f"[FAIL] 模型调用失败: {str(e)}")

    print("\n" + "="*60)
    print("Ollama 集成测试完成!")
    print("="*60)


if __name__ == "__main__":
    test_ollama_integration()
