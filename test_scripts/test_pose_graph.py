# -*- coding: utf-8 -*-
"""
测试姿态图功能
"""

import sys
import os
from pathlib import Path
import cv2
import json

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pose_detector import PoseDetector
from src.pose_graph import PoseGraph
from src.prompt_builder import PromptBuilder
from src.ollama_client import OllamaClient
from src.result_parser import ResultParser
from config.settings import POSE_STANDARDS


def main():
    print("\n" + "="*70)
    print(" "*20 + "姿态图测试")
    print("="*70)

    # 读取测试图像
    image_path = Path("data/archive/Ardhakati_Chakrasana/Ardhakati Chakrasana Right Step Angle 1/angle_analysis/best_frames_with_angles/frame_3_angles.jpg")

    if not image_path.exists():
        print(f"\n错误: 测试图像不存在: {image_path}")
        return

    # 读取图像
    image = cv2.imread(str(image_path))
    print(f"\n[1] 读取图像: {image_path.name}")
    print(f"  原始尺寸: {image.shape[1]} x {image.shape[0]}")

    # 姿态检测
    print(f"\n[2] 检测姿态...")
    pose_detector = PoseDetector()
    results = pose_detector.detect(image)

    if not results.pose_landmarks:
        print("  错误: 未检测到人体姿态")
        return

    print("  ✓ 姿态检测成功")

    # 构建姿态图
    print(f"\n[3] 构建姿态图...")
    pose_graph = PoseGraph(results.pose_landmarks[0])

    print(f"  节点数: {len(pose_graph.nodes)}")
    print(f"  边数: {len(pose_graph.edges)}")

    # 获取图描述
    descriptor = pose_graph.get_graph_descriptor()

    print(f"\n[4] 图统计信息:")
    print(f"  平均可见度: {descriptor['graph_stats']['avg_visibility']:.3f}")
    print(f"  最大距离: {descriptor['graph_stats']['max_distance']:.3f}")
    print(f"  最小距离: {descriptor['graph_stats']['min_distance']:.3f}")
    print(f"  平均距离: {descriptor['graph_stats']['avg_distance']:.3f}")

    # 生成文本描述
    print(f"\n[5] 生成文本描述...")
    text_desc = pose_graph.to_text_description()
    print(f"  文本描述长度: {len(text_desc)} 字符")

    # 保存图数据
    output_dir = image_path.parent.parent / "graph_analysis"
    output_dir.mkdir(exist_ok=True)

    graph_json_path = output_dir / "pose_graph.json"
    with open(graph_json_path, 'w', encoding='utf-8') as f:
        f.write(pose_graph.to_json())
    print(f"  保存图数据: {graph_json_path.name}")

    # 构建提示词（使用图信息）
    print(f"\n[6] 构建提示词...")
    prompt_builder = PromptBuilder()
    pose_name = "半月式"
    pose_standard = POSE_STANDARDS.get(pose_name)

    if not pose_standard:
        print(f"  警告: 未找到 '{pose_name}' 的标准配置")
        return

    prompt = prompt_builder.build_with_graph(pose_graph, pose_name, pose_standard)
    print(f"  提示词长度: {len(prompt)} 字符")

    # 显示提示词（前500字符）
    print(f"\n  提示词预览:")
    print("-" * 70)
    print(prompt[:500])
    print("-" * 70)

    # 保存完整提示词
    prompt_path = output_dir / "prompt.txt"
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)
    print(f"  保存提示词: {prompt_path.name}")

    print(f"\n" + "="*70)
    print(" "*25 + "测试完成")
    print("="*70 + "\n")

    print("\n📊 姿态图优势:")
    print("  ✓ 包含关节距离信息")
    print("  ✓ 包含相对位置关系")
    print("  ✓ 保留空间拓扑结构")
    print("  ✓ 可以计算整体平衡性")
    print("  ✓ 特征维度更丰富（~200维 vs ~10维）")


if __name__ == "__main__":
    main()
