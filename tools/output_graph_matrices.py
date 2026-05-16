"""
输出姿态图的矩阵信息
从视频帧中提取姿态并输出详细的无向图数据
"""

import sys
import cv2
import numpy as np
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from pose_detector import PoseDetector
from pose_graph import PoseGraph


def print_graph_matrices(graph: PoseGraph):
    """打印姿态图的矩阵信息"""

    print("=" * 80)
    print("姿态图矩阵信息")
    print("=" * 80)

    # 1. 节点位置矩阵 (33x3)
    print("\n1. 节点位置矩阵 (33x3) - [x, y, z]")
    print("-" * 80)
    position_matrix = []
    for idx in range(33):
        if idx in graph.nodes:
            node = graph.nodes[idx]
            position_matrix.append([node.x, node.y, node.z])
        else:
            position_matrix.append([0, 0, 0])

    position_matrix = np.array(position_matrix)
    print(f"Shape: {position_matrix.shape}")
    print(position_matrix)

    # 2. 可见性矩阵 (33x1)
    print("\n2. 可见性矩阵 (33x1)")
    print("-" * 80)
    visibility_matrix = np.array([graph.nodes.get(i, None) for i in range(33)])
    visibility_values = []
    for i in range(33):
        if visibility_matrix[i] is not None:
            visibility_values.append(visibility_matrix[i].visibility)
        else:
            visibility_values.append(0.0)
    visibility_values = np.array(visibility_values)
    print(f"Shape: {visibility_values.shape}")
    print(visibility_values)

    # 3. 邻接矩阵 (33x33)
    print("\n3. 邻接矩阵 (33x33)")
    print("-" * 80)
    adjacency_matrix = np.zeros((33, 33))
    for (from_id, to_id), edge in graph.edges.items():
        adjacency_matrix[from_id, to_id] = edge.distance_3d
        adjacency_matrix[to_id, from_id] = edge.distance_3d  # 无向图，对称
    print(f"Shape: {adjacency_matrix.shape}")
    print(adjacency_matrix)

    # 4. 关节角度向量
    print("\n4. 关节角度向量")
    print("-" * 80)
    print("肘关节角度:")
    left_elbow_angle = graph._calc_angle(11, 13, 15)
    right_elbow_angle = graph._calc_angle(12, 14, 16)
    print(f"  左肘 (11-13-15): {left_elbow_angle:.2f}°")
    print(f"  右肘 (12-14-16): {right_elbow_angle:.2f}°")

    print("\n膝关节角度:")
    left_knee_angle = graph._calc_angle(23, 25, 27)
    right_knee_angle = graph._calc_angle(24, 26, 28)
    print(f"  左膝 (23-25-27): {left_knee_angle:.2f}°")
    print(f"  右膝 (24-26-28): {right_knee_angle:.2f}°")

    # 5. 相对位置向量矩阵
    print("\n5. 关键相对位置向量")
    print("-" * 80)
    important_connections = [
        ('left_shoulder', 'left_elbow', 11, 13),
        ('left_elbow', 'left_wrist', 13, 15),
        ('right_shoulder', 'right_elbow', 12, 14),
        ('right_elbow', 'right_wrist', 14, 16),
        ('left_hip', 'left_knee', 23, 25),
        ('left_knee', 'left_ankle', 25, 27),
        ('right_hip', 'right_knee', 24, 26),
        ('right_knee', 'right_ankle', 26, 28),
    ]

    for from_name, to_name, from_id, to_id in important_connections:
        edge = graph.edges.get((from_id, to_id))
        if edge:
            print(f"{from_name} -> {to_name}:")
            print(f"  相对向量: {edge.relative_vector}")
            print(f"  归一化向量: {edge.normalized_vector}")
            print(f"  3D距离: {edge.distance_3d:.4f}")
            print(f"  2D距离: {edge.distance_2d:.4f}")

    # 6. 图统计信息
    print("\n6. 图统计信息")
    print("-" * 80)
    stats = graph.get_graph_descriptor()['graph_stats']
    print(f"节点数: {stats['num_nodes']}")
    print(f"边数: {stats['num_edges']}")
    print(f"平均可见性: {stats['avg_visibility']:.4f}")
    print(f"最大距离: {stats['max_distance']:.4f}")
    print(f"最小距离: {stats['min_distance']:.4f}")
    print(f"平均距离: {stats['avg_distance']:.4f}")

    # 7. 骨骼连接距离矩阵
    print("\n7. 标准骨骼连接距离")
    print("-" * 80)
    for from_id, to_id in graph.STANDARD_CONNECTIONS:
        edge = graph.edges.get((from_id, to_id))
        if edge:
            print(f"{edge.from_name:20} -> {edge.to_name:20}: {edge.distance_3d:.4f}")


def main():
    # 初始化姿态检测器
    detector = PoseDetector()

    # 视频路径
    video_path = Path("data/archive/Ardhakati_Chakrasana/Ardhakati Chakrasana Right Step Angle 1/video_annotated.mp4")

    if not video_path.exists():
        print(f"错误: 视频文件不存在: {video_path}")
        return

    # 打开视频
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"\n视频: {video_path.name}")
    print(f"总帧数: {total_frames}")
    print(f"\n处理第1帧...")

    # 读取第一帧
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, frame = cap.read()

    if not ret:
        print("错误: 无法读取视频帧")
        cap.release()
        return

    # 检测姿态
    landmarks = detector.detect(frame)

    if landmarks:
        print("姿态检测成功！\n")

        # 构建姿态图
        graph = PoseGraph(landmarks)

        # 输出矩阵信息
        print_graph_matrices(graph)

    else:
        print("错误: 未检测到姿态")

    cap.release()


if __name__ == "__main__":
    main()
