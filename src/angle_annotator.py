"""
角度标注和可视化模块
在图像上绘制角度标注和统计信息
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False


class AngleAnnotator:
    """角度标注器"""

    # MediaPipe 关键点映射
    POSE_LANDMARKS = {
        11: "左肩", 12: "右肩",
        13: "左肘", 14: "右肘",
        15: "左腕", 16: "右腕",
        23: "左髋", 24: "右髋",
        25: "左膝", 26: "右膝",
        27: "左踝", 28: "右踝"
    }

    # 角度定义（三个关键点索引）
    ANGLE_DEFINITIONS = {
        "左肘": (11, 13, 15),
        "右肘": (12, 14, 16),
        "左膝": (23, 25, 27),
        "右膝": (24, 26, 28),
        "左髋": (11, 23, 25),
        "右髋": (12, 24, 26),
        "左肩": (13, 11, 23),
        "右肩": (14, 12, 24)
    }

    def __init__(self, font_scale: float = 0.7, line_thickness: int = 3):
        """
        初始化标注器

        Args:
            font_scale: 字体大小
            line_thickness: 线条粗细
        """
        self.font_scale = font_scale
        self.line_thickness = line_thickness
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def draw_angle(self, frame: np.ndarray, landmarks: List[Dict],
                 angle_name: str, angle_value: float,
                 point_indices: Tuple[int, int, int]) -> np.ndarray:
        """
        在图像上绘制单个角度标注

        Args:
            frame: 图像帧
            landmarks: 关键点列表
            angle_name: 角度名称
            angle_value: 角度值（度）
            point_indices: 三个关键点索引 (p1, p2, p3)，p2是顶点

        Returns:
            标注后的图像
        """
        frame = frame.copy()

        # 获取关键点坐标
        points = []
        for idx in point_indices:
            point = self._get_point(landmarks, idx)
            if point is None:
                return frame
            points.append(point)

        p1, p2, p3 = points

        # 绘制角度弧线
        self._draw_angle_arc(frame, p1, p2, p3, angle_value)

        # 绘制连接线
        self._draw_angle_lines(frame, p1, p2, p3)

        # 绘制角度文字
        self._draw_angle_text(frame, p2, angle_name, angle_value)

        # 绘制关键点
        for point in points:
            cv2.circle(frame, point, 5, (0, 255, 0), -1)

        return frame

    def draw_all_angles(self, frame: np.ndarray,
                     landmarks: List[Dict],
                     angles: Dict[str, float]) -> np.ndarray:
        """
        在图像上绘制所有角度标注

        Args:
            frame: 图像帧
            landmarks: 关键点列表
            angles: 角度字典 {名称: 值}

        Returns:
            标注后的图像
        """
        frame = frame.copy()

        # 绘制每个角度
        for angle_name, angle_value in angles.items():
            if angle_name not in self.ANGLE_DEFINITIONS:
                continue

            point_indices = self.ANGLE_DEFINITIONS[angle_name]
            if angle_value is None:
                continue

            frame = self.draw_angle(frame, landmarks, angle_name, angle_value, point_indices)

        return frame

    def _draw_angle_arc(self, frame: np.ndarray, p1: Tuple, p2: Tuple, p3: Tuple, angle_value: float):
        """绘制角度弧线"""
        # 计算两个向量
        v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])

        # 计算角度
        angle1 = np.degrees(np.arctan2(v1[1], v1[0]))
        angle2 = np.degrees(np.arctan2(v2[1], v2[0]))

        # 规范化角度
        if angle1 < 0:
            angle1 += 360
        if angle2 < 0:
            angle2 += 360

        # 确保弧线方向正确
        start_angle = min(angle1, angle2)
        end_angle = max(angle1, angle2)

        # 如果角度差大于180度，说明需要反向绘制
        if end_angle - start_angle > 180:
            start_angle, end_angle = end_angle, start_angle + 360

        # 绘制弧线
        radius = 30
        cv2.ellipse(frame, p2, (radius, radius), 0,
                   start_angle, end_angle, (255, 255, 0), 2)

    def _draw_angle_lines(self, frame: np.ndarray, p1: Tuple, p2: Tuple, p3: Tuple):
        """绘制角度连接线"""
        # 绘制两条边
        cv2.line(frame, p1, p2, (255, 255, 0), self.line_thickness)
        cv2.line(frame, p2, p3, (255, 255, 0), self.line_thickness)

    def _draw_angle_text(self, frame: np.ndarray, p2: Tuple, name: str, value: float):
        """绘制角度文字"""
        text = f"{name}: {value:.1f}°"

        # 计算文字位置（在角度顶点上方）
        text_x = p2[0] - 30
        text_y = p2[1] - 50

        # 绘制文字背景
        (text_w, text_h), baseline = cv2.getTextSize(text, self.font, self.font_scale, 2)
        cv2.rectangle(frame, (text_x - 5, text_y - text_h - 5),
                   (text_x + text_w + 5, text_y + baseline + 5), (0, 0, 0), -1)

        # 绘制文字
        cv2.putText(frame, text, (text_x, text_y), self.font,
                  self.font_scale, (0, 255, 255), 2)

    def _get_point(self, landmarks: List[Dict], idx: int) -> Optional[Tuple[int, int]]:
        """获取关键点的像素坐标"""
        for lm in landmarks:
            if lm["id"] == idx:
                # 假设图像尺寸是标准的，需要根据实际尺寸调整
                # 这里暂时返回归一化坐标，使用时需要转换
                return (int(lm["x"] * frame.shape[1] if 'frame' in locals() else lm["x"]),
                        int(lm["y"] * frame.shape[0] if 'frame' in locals() else lm["y"]))
        return None

    def create_angle_summary_image(self, angles_seq: List[Dict[str, float]],
                                avg_angles: Dict[str, float],
                                std_angles: Dict[str, float],
                                image_size: Tuple[int, int] = (800, 600)) -> np.ndarray:
        """
        创建角度汇总图像

        Args:
            angles_seq: 角度序列
            avg_angles: 平均角度
            std_angles: 角度标准差
            image_size: 图像尺寸

        Returns:
            汇总图像
        """
        # 创建白色背景
        img = np.ones(image_size, dtype=np.uint8) * 255

        # 标题
        title = "Angle Analysis Summary"
        cv2.putText(img, title, (50, 50), self.font, 1.2, (0, 0, 0), 2)

        # 绘制表格头
        headers = ["Joint", "Avg Angle", "Std Dev", "Status"]
        y_pos = 100
        for i, header in enumerate(headers):
            x_pos = 50 + i * 200
            cv2.putText(img, header, (x_pos, y_pos), self.font,
                      self.font_scale, (0, 0, 255), 2)

        # 绘制角度数据
        y_pos += 50
        for angle_name in ["左肘", "右肘", "左膝", "右膝", "左髋", "右髋"]:
            avg = avg_angles.get(angle_name, 0)
            std = std_angles.get(angle_name, 0)

            # 判断稳定性
            status = "Stable" if std < 5 else "Unstable"
            status_color = (0, 255, 0) if std < 5 else (0, 0, 255)

            # 绘制数据行
            x_pos = 50
            cv2.putText(img, angle_name, (x_pos, y_pos), self.font,
                      self.font_scale, (0, 0, 0), 2)
            cv2.putText(img, f"{avg:.1f}", (x_pos + 200, y_pos), self.font,
                      self.font_scale, (0, 0, 0), 2)
            cv2.putText(img, f"{std:.2f}", (x_pos + 400, y_pos), self.font,
                      self.font_scale, (0, 0, 0), 2)
            cv2.putText(img, status, (x_pos + 600, y_pos), self.font,
                      self.font_scale, status_color, 2)

            y_pos += 40

        return img

    def create_angle_time_series_plot(self, angles_seq: List[Dict[str, float]],
                                  timestamps: List[float]) -> np.ndarray:
        """
        创建角度随时间变化的图表

        Args:
            angles_seq: 角度序列
            timestamps: 时间戳列表

        Returns:
            图表图像
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))

        # 收集数据
        data = {
            "左肘": [], "右肘": [],
            "左膝": [], "右膝": [],
            "左髋": [], "右髋": []
        }

        for angles in angles_seq:
            for key in data.keys():
                if key in angles and angles[key] is not None:
                    data[key].append(angles[key])
                else:
                    data[key].append(None)

        # 绘制肘关节
        ax1 = axes[0, 0]
        ax1.plot(timestamps, data["左肘"], label='左肘', color='blue')
        ax1.plot(timestamps, data["右肘"], label='右肘', color='cyan')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Angle (°)')
        ax1.set_title('肘关节角度变化')
        ax1.legend()
        ax1.grid(True)

        # 绘制膝关节
        ax2 = axes[0, 1]
        ax2.plot(timestamps, data["左膝"], label='左膝', color='green')
        ax2.plot(timestamps, data["右膝"], label='右膝', color='lime')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Angle (°)')
        ax2.set_title('膝关节角度变化')
        ax2.legend()
        ax2.grid(True)

        # 绘制髋关节
        ax3 = axes[1, 0]
        ax3.plot(timestamps, data["左髋"], label='左髋', color='red')
        ax3.plot(timestamps, data["右髋"], label='右髋', color='orange')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Angle (°)')
        ax3.set_title('髋关节角度变化')
        ax3.legend()
        ax3.grid(True)

        # 绘制稳定性对比
        ax4 = axes[1, 1]
        joint_names = ['左肘', '右肘', '左膝', '右膝', '左髋', '右髋']
        std_values = [np.std([angles.get(name, 0) for angles in angles_seq
                          if angles.get(name) is not None]) for name in joint_names]
        colors = ['blue', 'cyan', 'green', 'lime', 'red', 'orange']
        ax4.bar(joint_names, std_values, color=colors)
        ax4.set_ylabel('Standard Deviation (°)')
        ax4.set_title('关节角度稳定性')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True)

        plt.tight_layout()

        # 保存为图像
        from io import BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img = plt.imread(buf)
        plt.close()

        # 转换为 OpenCV 格式
        img = (img * 255).astype(np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        return img


def draw_landmarks_with_angles(frame: np.ndarray, landmarks: List[Dict],
                           angles: Dict[str, float]) -> np.ndarray:
    """
    在图像上同时绘制关键点、骨骼和角度标注

    Args:
        frame: 图像帧
        landmarks: 关键点列表
        angles: 角度字典

    Returns:
        标注后的图像
    """
    annotator = AngleAnnotator()
    frame = annotator.draw_all_angles(frame, landmarks, angles)
    return frame
