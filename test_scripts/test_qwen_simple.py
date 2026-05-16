# -*- coding: utf-8 -*-
"""
简化版测试：测试qwen:4b模型的JSON输出
"""

import sys
import os
from pathlib import Path

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ollama_client import OllamaClient
from src.result_parser import ResultParser


def main():
    print("\n" + "="*70)
    print(" "*20 + "简化版JSON测试")
    print("="*70)

    client = OllamaClient()
    parser = ResultParser()

    # 测试1：简单JSON
    print("\n[测试1] 简单JSON输出...")
    simple_prompt = """Return a JSON object with this exact format:
{"name":"test","value":42}

Only return the JSON, no other text."""

    try:
        response = client.generate(simple_prompt)
        print(f"模型响应: {response}")
        result = parser.parse(response)
        if result.get('success'):
            print(f"✓ 解析成功: {result['data']}")
        else:
            print(f"✗ 解析失败: {result.get('error')}")
    except Exception as e:
        print(f"✗ 错误: {e}")

    # 测试2：瑜伽评分JSON
    print("\n[测试2] 瑜伽评分JSON...")
    yoga_prompt = """You are a yoga instructor. Assess this pose and return only this JSON format:
{"score":{"total":80,"accuracy":30,"stability":25,"coordination":25},"problems":["Knee too bent","Back arched"],"suggestions":["Straighten knee slightly","Engage core"]}

Only return the JSON, no other text."""

    try:
        response = client.generate(yoga_prompt)
        print(f"模型响应: {response}")
        result = parser.parse(response)
        if result.get('success'):
            print(f"✓ 解析成功: {result['data']}")
        else:
            print(f"✗ 解析失败: {result.get('error')}")
    except Exception as e:
        print(f"✗ 错误: {e}")

    # 测试3：使用prompt builder
    print("\n[测试3] 使用PromptBuilder...")
    from src.prompt_builder import PromptBuilder
    from config.settings import POSE_STANDARDS

    test_stats = {
        'mean': {
            'left_elbow': 170.0,
            'right_elbow': 165.0,
            'left_knee': 172.0,
            'right_knee': 168.0,
            'left_hip': 90.0,
            'right_hip': 95.0,
            'left_shoulder': 175.0,
            'right_shoulder': 170.0
        },
        'std': {
            'left_elbow': 3.0,
            'right_elbow': 4.0,
            'left_knee': 2.0,
            'right_knee': 3.0,
            'left_hip': 5.0,
            'right_hip': 4.0,
            'left_shoulder': 2.5,
            'right_shoulder': 3.0
        }
    }
    test_stability = 0.85

    prompt_builder = PromptBuilder()
    pose_name = "下犬式"
    pose_standard = POSE_STANDARDS.get(pose_name)

    if pose_standard:
        prompt = prompt_builder.build(test_stats, test_stability, pose_name, pose_standard)
        print(f"Prompt长度: {len(prompt)} 字符")

        try:
            response = client.generate(prompt)
            print(f"模型响应长度: {len(response)} 字符")
            print(f"模型响应: {response[:500]}...")  # 只显示前500字符

            result = parser.parse(response)
            if result.get('success'):
                print(f"✓ 解析成功")
                print(f"得分: {result['data']['score']}")
            else:
                print(f"✗ 解析失败: {result.get('error')}")
        except Exception as e:
            print(f"✗ 错误: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)
    print(" "*25 + "测试完成")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
