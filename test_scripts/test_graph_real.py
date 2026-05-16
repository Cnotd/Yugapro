# -*- coding: utf-8 -*-
"""
真实图像姿态图测试
"""

import sys
from pathlib import Path
import cv2

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pose_detector import PoseDetector
from src.pose_graph import PoseGraph


def main():
    print("\n" + "="*70)
    print(" "*20 + "Real Image Graph Test")
    print("="*70)

    # 读取测试图像
    image_path = Path("data/archive/Ardhakati_Chakrasana/Ardhakati Chakrasana Right Step Angle 1/angle_analysis/best_frames_with_angles/frame_3_angles.jpg")

    if not image_path.exists():
        print(f"\nError: Test image not found: {image_path}")
        return

    # 读取图像
    image = cv2.imread(str(image_path))
    print(f"\n[1] Load image: {image_path.name}")
    print(f"  Size: {image.shape[1]} x {image.shape[0]}")

    # Pose detection
    print(f"\n[2] Detect pose...")
    pose_detector = PoseDetector()
    results = pose_detector.detect(image)

    if not results.pose_landmarks:
        print("  Error: No pose detected")
        return

    print(f"  [OK] Pose detected")

    # Build pose graph
    print(f"\n[3] Build pose graph...")
    pose_graph = PoseGraph(results.pose_landmarks[0])

    print(f"  Nodes: {len(pose_graph.nodes)}")
    print(f"  Edges: {len(pose_graph.edges)}")

    # Key joint positions
    print(f"\n[4] Key joint positions:")
    key_joints = {
        'nose': 'Nose',
        'left_shoulder': 'Left Shoulder',
        'right_shoulder': 'Right Shoulder',
        'left_hip': 'Left Hip',
        'right_hip': 'Right Hip',
        'left_knee': 'Left Knee',
        'right_knee': 'Right Knee'
    }

    for joint_name, cn_name in key_joints.items():
        node = next((n for n in pose_graph.nodes.values() if n.name == joint_name), None)
        if node:
            print(f"  {cn_name}: ({node.x:.3f}, {node.y:.3f}, {node.z:.3f})")

    # Statistics
    print(f"\n[5] Graph statistics:")
    descriptor = pose_graph.get_graph_descriptor()
    stats = descriptor['graph_stats']
    print(f"  Average visibility: {stats['avg_visibility']:.3f}")
    print(f"  Max distance: {stats['max_distance']:.3f}")
    print(f"  Min distance: {stats['min_distance']:.3f}")
    print(f"  Average distance: {stats['avg_distance']:.3f}")

    # Important edges with distances
    print(f"\n[6] Important connections:")
    important_edges = [
        ('left_shoulder', 'left_elbow'),
        ('left_elbow', 'left_wrist'),
        ('left_hip', 'left_knee'),
        ('left_knee', 'left_ankle'),
        ('right_shoulder', 'right_elbow'),
        ('right_elbow', 'right_wrist'),
        ('right_hip', 'right_knee'),
        ('right_knee', 'right_ankle')
    ]

    for from_name, to_name in important_edges:
        edge = next((e for e in pose_graph.edges.values()
                    if e.from_name == from_name and e.to_name == to_name), None)
        if edge:
            print(f"  {from_name} -> {to_name}:")
            print(f"    3D Distance: {edge.distance_3d:.3f}")
            print(f"    2D Distance: {edge.distance_2d:.3f}")
            print(f"    Angle: {edge.angle:.1f} deg" if edge.angle > 0 else "    Angle: N/A")

    # Feature comparison
    print(f"\n" + "="*70)
    print("Feature Comparison")
    print("="*70)
    print(f"\nTraditional Angle Method:")
    print(f"  Features: ~10 joint angles")
    print(f"  Info: Angles only")
    print(f"  Dimensions: 1D scalar")

    print(f"\nPose Graph Method:")
    print(f"  Features: {len(pose_graph.nodes) + len(pose_graph.edges) * 5}")
    print(f"  Info: Angles + Distances + Relative Positions + Topology")
    print(f"  Dimensions: Multi-dimensional vectors")

    print(f"\nAdvantages:")
    print(f"  [+] Captures spatial relationships between joints")
    print(f"  [+] Includes limb length information")
    print(f"  [+] Preserves body structural topology")
    print(f"  [+] Can calculate overall balance")
    print(f"  [+] Better for LLM understanding")

    # Save results
    output_dir = image_path.parent.parent / "graph_analysis"
    output_dir.mkdir(exist_ok=True)

    # Save JSON
    json_path = output_dir / "pose_graph.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(pose_graph.to_json())
    print(f"\n[7] Save results:")
    print(f"  JSON: {json_path.name}")

    # Save text description
    text_path = output_dir / "graph_description.txt"
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(pose_graph.to_text_description())
    print(f"  Text: {text_path.name}")

    print(f"\n" + "="*70)
    print(" "*25 + "Test Completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
