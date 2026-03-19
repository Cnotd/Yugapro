# -*- coding: utf-8 -*-
"""
测试图像resize功能
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
from src.prompt_builder import PromptBuilder
from src.result_parser import ResultParser
from config.settings import POSE_STANDARDS
import cv2
import numpy as np


def test_image_resize():
    """测试图像resize功能"""
    print("\n" + "="*70)
    print(" "*20 + "图像Resize测试")
    print("="*70)

    # 加载测试图像
    image_path = Path("data/archive/Ardhakati_Chakrasana/Ardhakati Chakrasana Right Step Angle 1/angle_analysis/best_frames_with_angles/frame_3_angles.jpg")

    if not image_path.exists():
        print(f"\n错误: 测试图像不存在: {image_path}")
        return

    # 读取图像
    image = cv2.imread(str(image_path))
    original_size = (image.shape[1], image.shape[0])  # (width, height)

    print(f"\n[1] 原始图像信息:")
    print(f"  路径: {image_path.name}")
    print(f"  尺寸: {original_size[0]} x {original_size[1]}")
    print(f"  最大边: {max(original_size)} 像素")

    # 创建Ollama客户端
    client = OllamaClient()

    # 测试图像转换（会自动resize）
    print(f"\n[2] 测试图像转换...")
    try:
        base64_str = client._image_to_base64(image)
        print(f"  ✓ 图像转换成功")
        print(f"  Base64长度: {len(base64_str)} 字符")

        # 估算压缩后大小
        estimated_size = len(base64_str) * 0.75 / 1024  # base64解码后的大小（KB）
        print(f"  估计大小: {estimated_size:.1f} KB")

    except Exception as e:
        print(f"  ✗ 图像转换失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 测试带图像的评估
    print(f"\n[3] 测试带图像的评估...")

    # 准备测试数据
    test_stats = {
        'mean': {
            'left_elbow': 169.9,
            'right_elbow': 154.2,
            'left_knee': 171.8,
            'right_knee': 168.3,
            'left_hip': 158.5,
            'right_hip': 164.0,
            'left_shoulder': 58.0,
            'right_shoulder': 78.4
        },
        'std': {
            'left_elbow': 8.73,
            'right_elbow': 13.49,
            'left_knee': 3.15,
            'right_knee': 2.00,
            'left_hip': 11.13,
            'right_hip': 1.59,
            'left_shoulder': 32.04,
            'right_shoulder': 44.67
        }
    }
    stability = 0.72

    # 构建带图像的提示词
    prompt_builder = PromptBuilder()
    pose_name = "半月式"
    pose_standard = POSE_STANDARDS.get(pose_name)

    if not pose_standard:
        print(f"  ✗ 未找到 '{pose_name}' 的标准配置")
        return

    prompt = prompt_builder.build_with_image(test_stats, stability, pose_name, pose_standard)
    print(f"  提示词长度: {len(prompt)} 字符")

    # 调用模型
    print(f"\n[4] 调用模型进行评估...")
    print(f"  正在等待模型响应...")

    try:
        response = client.generate(prompt, image)
        print(f"  ✓ 模型响应成功 (长度: {len(response)} 字符)")

        # 解析结果
        parser = ResultParser()
        result = parser.parse(response)

        if result.get('success'):
            print(f"\n  ✓ 评估结果解析成功!")
            data = result['data']
            score = data['score']

            print(f"\n" + "-"*60)
            print(f"评估结果:")
            print(f"  总分: {score['total']}/100")
            print(f"  角度准确性: {score['accuracy']}/40")
            print(f"  动作稳定性: {score['stability']}/30")
            print(f"  整体协调性: {score['coordination']}/30")

            if data['problems']:
                print(f"\n  主要问题:")
                for i, prob in enumerate(data['problems'], 1):
                    print(f"    {i}. {prob}")

            if data['suggestions']:
                print(f"\n  改进建议:")
                for i, sugg in enumerate(data['suggestions'], 1):
                    print(f"    {i}. {sugg}")

            print("-"*60)
        else:
            print(f"\n  ✗ 解析失败: {result.get('error')}")

    except Exception as e:
        print(f"  ✗ 评估失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)
    print(" "*25 + "测试完成")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_image_resize()
