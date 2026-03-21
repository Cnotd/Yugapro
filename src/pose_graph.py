"""
姿态图模块
用无向图表示人体姿态，包含距离、角度、相对位置等特征
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import json


@dataclass
class JointNode:
    """关节节点"""
    id: int
    name: str
    x: float
    y: float
    z: float
    visibility: float
    confidence: float
    position_3d: np.ndarray = field(init=False)

    def __post_init__(self):
        self.position_3d = np.array([self.x, self.y, self.z])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'position': [self.x, self.y, self.z],
            'visibility': self.visibility,
            'confidence': self.confidence
        }


@dataclass
class JointEdge:
    """关节边"""
    from_id: int
    to_id: int
    from_name: str
    to_name: str
    distance_3d: float  # 三维欧氏距离
    distance_2d: float  # 二维投影距离
    angle: float  # 关节角度
    relative_vector: np.ndarray  # 相对位置向量
    normalized_vector: np.ndarray  # 归一化向量

    def to_dict(self):
        return {
            'from': self.from_name,
            'to': self.to_name,
            'distance_3d': self.distance_3d,
            'distance_2d': self.distance_2d,
            'angle': self.angle,
            'relative_vector': self.relative_vector.tolist()
        }


class PoseGraph:
    """
    人体姿态无向图
    节点: 33个人体关键点
    边: 基于骨骼连接的边 + 额外添加的长距离边
    """

    # 标准骨骼连接（MediaPipe定义）
    STANDARD_CONNECTIONS = [
        # 躯干
        (11, 12),  # 左右肩
        (23, 24),  # 左右髋
        (11, 23),  # 左肩-左髋
        (12, 24),  # 右肩-右髋

        # 左臂
        (11, 13), (13, 15),  # 肩-肘-腕
        # 右臂
        (12, 14), (14, 16),  # 肩-肘-腕

        # 左腿
        (23, 25), (25, 27),  # 髋-膝-踝
        # 右腿
        (24, 26), (26, 28),  # 髋-膝-踝

        # 头部
        (0, 11), (0, 12),  # 鼻子-肩
        (0, 10),  # 鼻子-额头
    ]

    # 额外长距离边（捕捉整体姿态）
    EXTENDED_CONNECTIONS = [
        (11, 25), (12, 26),  # 肩-膝
        (13, 23), (14, 24),  # 肘-髋
        (15, 25), (16, 26),  # 腕-膝
        (0, 23), (0, 24),  # 鼻子-髋
        (11, 27), (12, 28),  # 肩-踝
    ]

    # 关节名称映射
    JOINT_NAMES = {
        0: 'nose',
        1: 'left_eye_inner', 2: 'left_eye', 3: 'left_eye_outer',
        4: 'right_eye_inner', 5: 'right_eye', 6: 'right_eye_outer',
        7: 'left_ear', 8: 'right_ear',
        9: 'mouth_left', 10: 'mouth_right',
        11: 'left_shoulder', 12: 'right_shoulder',
        13: 'left_elbow', 14: 'right_elbow',
        15: 'left_wrist', 16: 'right_wrist',
        17: 'left_pinky', 18: 'right_pinky',
        19: 'left_index', 20: 'right_index',
        21: 'left_thumb', 22: 'right_thumb',
        23: 'left_hip', 24: 'right_hip',
        25: 'left_knee', 26: 'right_knee',
        27: 'left_ankle', 28: 'right_ankle',
        29: 'left_heel', 30: 'right_heel',
        31: 'left_foot_index', 32: 'right_foot_index'
    }

    def __init__(self, landmarks):
        """
        从MediaPipe landmarks构建姿态图

        Args:
            landmarks: MediaPipe检测到的33个关键点
        """
        self.nodes: Dict[int, JointNode] = {}
        self.edges: Dict[Tuple[int, int], JointEdge] = {}

        # 构建节点
        for idx, lm in enumerate(landmarks.landmark):
            name = self.JOINT_NAMES.get(idx, f'joint_{idx}')
            node = JointNode(
                id=idx,
                name=name,
                x=lm.x,
                y=lm.y,
                z=lm.z if hasattr(lm, 'z') else 0,
                visibility=lm.visibility if hasattr(lm, 'visibility') else 1.0,
                confidence=lm.visibility if hasattr(lm, 'visibility') else 1.0
            )
            self.nodes[idx] = node

        # 构建边
        self._build_edges()

    def _build_edges(self):
        """构建所有边（标准连接 + 扩展连接）"""
        all_connections = self.STANDARD_CONNECTIONS + self.EXTENDED_CONNECTIONS

        for from_id, to_id in all_connections:
            if from_id in self.nodes and to_id in self.nodes:
                edge = self._create_edge(from_id, to_id)
                if edge:
                    self.edges[(from_id, to_id)] = edge

    def _create_edge(self, from_id: int, to_id: int) -> Optional[JointEdge]:
        """创建单条边"""
        node_a = self.nodes[from_id]
        node_b = self.nodes[to_id]

        # 检查可见性（至少一个点可见）
        if node_a.visibility < 0.3 and node_b.visibility < 0.3:
            return None

        # 计算三维欧氏距离
        distance_3d = np.linalg.norm(node_a.position_3d - node_b.position_3d)

        # 计算二维距离（忽略z轴）
        pos_2d_a = node_a.position_3d[:2]
        pos_2d_b = node_b.position_3d[:2]
        distance_2d = np.linalg.norm(pos_2d_a - pos_2d_b)

        # 计算相对位置向量
        relative_vector = node_b.position_3d - node_a.position_3d

        # 归一化向量
        norm = np.linalg.norm(relative_vector)
        normalized_vector = relative_vector / norm if norm > 0 else relative_vector

        # 计算关节角度（如果是肘、膝等关节）
        angle = self._calculate_joint_angle(from_id, to_id)

        return JointEdge(
            from_id=from_id,
            to_id=to_id,
            from_name=self.JOINT_NAMES.get(from_id, str(from_id)),
            to_name=self.JOINT_NAMES.get(to_id, str(to_id)),
            distance_3d=distance_3d,
            distance_2d=distance_2d,
            angle=angle,
            relative_vector=relative_vector,
            normalized_vector=normalized_vector
        )

    def _calculate_joint_angle(self, joint_id: int, neighbor_id: int) -> float:
        """
        计算关节角度（如果需要）
        针对特定关节（肘、膝）计算弯曲角度
        """
        # 肘关节（肩-肘-腕）
        if joint_id == 13 and neighbor_id == 11:  # 左肘-左肩
            return self._calc_angle(11, 13, 15)  # 肩-肘-腕
        if joint_id == 14 and neighbor_id == 12:  # 右肘-右肩
            return self._calc_angle(12, 14, 16)

        # 膝关节（髋-膝-踝）
        if joint_id == 25 and neighbor_id == 23:  # 左膝-左髋
            return self._calc_angle(23, 25, 27)
        if joint_id == 26 and neighbor_id == 24:  # 右膝-右髋
            return self._calc_angle(24, 26, 28)

        return 0.0

    def _calc_angle(self, a_id: int, b_id: int, c_id: int) -> float:
        """计算三点夹角"""
        if a_id not in self.nodes or b_id not in self.nodes or c_id not in self.nodes:
            return 0.0

        a = self.nodes[a_id].position_3d
        b = self.nodes[b_id].position_3d
        c = self.nodes[c_id].position_3d

        ba = a - b
        bc = c - b

        cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))

        return np.degrees(angle)

    def get_graph_descriptor(self) -> Dict:
        """
        获取图的描述信息（用于提示词构建）
        """
        descriptor = {
            'nodes': [],
            'edges': [],
            'graph_stats': {}
        }

        # 节点信息
        for node in self.nodes.values():
            descriptor['nodes'].append({
                'id': node.id,
                'name': node.name,
                'position': f"({node.x:.3f}, {node.y:.3f})",
                'visibility': f"{node.visibility:.2f}"
            })

        # 边信息
        for edge in self.edges.values():
            descriptor['edges'].append({
                'from': edge.from_name,
                'to': edge.to_name,
                'distance': f"{edge.distance_3d:.3f}",
                'angle': f"{edge.angle:.1f}°" if edge.angle > 0 else None
            })

        # 图统计
        if self.edges:
            descriptor['graph_stats'] = {
                'num_nodes': len(self.nodes),
                'num_edges': len(self.edges),
                'avg_visibility': np.mean([n.visibility for n in self.nodes.values()]),
                'max_distance': max([e.distance_3d for e in self.edges.values()]),
                'min_distance': min([e.distance_3d for e in self.edges.values()]),
                'avg_distance': np.mean([e.distance_3d for e in self.edges.values()])
            }
        else:
            descriptor['graph_stats'] = {
                'num_nodes': len(self.nodes),
                'num_edges': 0,
                'avg_visibility': 0.0,
                'max_distance': 0.0,
                'min_distance': 0.0,
                'avg_distance': 0.0
            }

        return descriptor

    def to_text_description(self) -> str:
        """
        转换为文本描述（用于LLM提示词）
        """
        desc = f"人体姿态图包含 {len(self.nodes)} 个关节节点和 {len(self.edges)} 条连接边。\n\n"

        # 关键节点位置
        key_joints = ['nose', 'left_shoulder', 'right_shoulder', 'left_hip', 'right_hip',
                      'left_knee', 'right_knee', 'left_ankle', 'right_ankle']

        desc += "关键关节位置:\n"
        for joint in key_joints:
            node = next((n for n in self.nodes.values() if n.name == joint), None)
            if node:
                desc += f"  - {joint}: ({node.x:.3f}, {node.y:.3f}, {node.z:.3f})\n"

        desc += "\n关节距离关系:\n"
        important_edges = [('left_shoulder', 'left_elbow'), ('left_elbow', 'left_wrist'),
                          ('left_hip', 'left_knee'), ('left_knee', 'left_ankle')]

        for from_name, to_name in important_edges:
            edge = next((e for e in self.edges.values()
                        if e.from_name == from_name and e.to_name == to_name), None)
            if edge:
                desc += f"  - {from_name} → {to_name}: {edge.distance_3d:.3f} (角度: {edge.angle:.1f}°)\n"

        return desc

    def to_json(self) -> str:
        """导出为JSON"""
        data = {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges.values()],
            'stats': self.get_graph_descriptor()['graph_stats']
        }
        return json.dumps(data, indent=2)
