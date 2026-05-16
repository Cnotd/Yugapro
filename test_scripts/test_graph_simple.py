# -*- coding: utf-8 -*-
"""
快速测试姿态图功能（不调用模型）
"""

import sys
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


def main():
    print("\n" + "="*70)
    print(" "*20 + "姿态图快速测试")
    print("="*70)

    # 读取测试图像
    image_path = Path("data/archive/Ardhakati_Chakrasana/Ardhakati Chakrasana Right Step Angle 1/angle_analysis/best_frames_with_angles/frame_3_angles.jpg")

    if not image_path.exists():
        print(f"\n错误: 测试图像不存在: {image_path}")
        return

    # 读取图像
    image = cv2.imread(str(image_path))
    print(f"\n图像: {image_path.name}")
    print(f"尺寸: {image.shape[1]} x {image.shape[0]}")

    # 姿态检测
    print(f"\n检测姿态...")
    pose_detector = PoseDetector()
    results = pose_detector.detect(image)

    if not results.pose_landmarks:
        print("错误: 未检测到人体姿态")
        return

    # 构建姿态图
    print(f"\n构建姿态图...")
    pose_graph = PoseGraph(results.pose_landmarks[0])

    print(f"\n图结构:")
    print(f"  节点数: {len(pose_graph.nodes)}")
    print(f"  边数: {len(pose_graph.edges)}")

    # 统计信息
    descriptor = pose_graph.get_graph_descriptor()

    print(f"\n统计信息:")
    print(f"  平均可见度: {descriptor['graph_stats']['avg_visibility']:.3f}")
    print(f"  最大距离: {descriptor['graph_stats']['max_distance']:.3f}")
    print(f"  最小距离: {descriptor['graph_stats']['min_distance']:.3f}")
    print(f"  平均距离: {descriptor['graph_stats']['avg_distance']:.3f}")

    # 关键关节
    print(f"\n关键关节位置:")
    key_joints = {
        'nose': '鼻子',
        'left_shoulder': '左肩',
        'right_shoulder': '右肩',
        'left_hip': '左髋',
        'right_hip': '右髋',
        'left_knee': '左膝',
        'right_knee': '右膝'
    }

    for joint_name, cn_name in key_joints.items():
        node = next((n for n in pose_graph.nodes.values() if n.name == joint_name), None)
        if node:
            print(f"  {cn_name}: ({node.x:.3f}, {node.y:.3f}, {node.z:.3f})")

    # 重要边
    print(f"\n重要连接:")
    important_edges = [
        ('left_shoulder', 'left_elbow'),
        ('left_elbow', 'left_wrist'),
        ('left_hip', 'left_knee'),
        ('left_knee', 'left_ankle')
    ]

    for from_name, to_name in important_edges:
        edge = next((e for e in pose_graph.edges.values()
                    if e.from_name == from_name and e.to_name == to_name), None)
        if edge:
            print(f"  {from_name} → {to_name}:")
            print(f"    距离: {edge.distance_3d:.3f}")
            print(f"    角度: {edge.angle:.1f}°" if edge.angle > 0 else "    角度: N/A")

    # 特征对比
    print(f"\n" + "="*70)
    print("特征对比")
    print("="*70)
    print(f"\n传统角度法:")
    print(f"  特征数: ~10个关节角度")
    print(f"  信息类型: 角度")
    print(f"  维度: 一维标量")

    print(f"\n姿态图法:")
    print(f"  特征数: {len(pose_graph.nodes) + len(pose_graph.edges) * 5}")
    print(f"  信息类型: 角度 + 距离 + 相对位置 + 空间拓扑")
    print(f"  维度: 多维向量")

    print(f"\n优势:")
    print(f"  ✓ 捕捉关节间的空间关系")
    print(f"  ✓ 包含肢体长度信息")
    print(f"  ✓ 保留人体结构拓扑")
    print(f"  ✓ 可以计算整体平衡性")
    print(f"  ✓ 更适合大模型理解")

    # 保存结果
    output_dir = image_path.parent.parent / "graph_analysis"
    output_dir.mkdir(exist_ok=True)

    # 保存JSON
    json_path = output_dir / "pose_graph.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(pose_graph.to_json())
    print(f"\n保存JSON: {json_path.name}")

    # 保存文本描述
    text_path = output_dir / "graph_description.txt"
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(pose_graph.to_text_description())
    print(f"保存描述: {text_path.name}")

    print(f"\n" + "="*70)
    print(" "*25 + "测试完成")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
