"""
角度计算模块测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.angle_calculator import AngleCalculator


def test_angle_calculator():
    """测试角度计算功能"""
    print("测试角度计算模块...")
    
    calc = AngleCalculator()
    
    # 创建测试关键点数据
    landmarks = [
        {"id": 11, "x": 0.5, "y": 0.3, "z": 0.0, "visibility": 1.0},  # 左肩
        {"id": 13, "x": 0.5, "y": 0.4, "z": 0.0, "visibility": 1.0},  # 左肘
        {"id": 15, "x": 0.5, "y": 0.5, "z": 0.0, "visibility": 1.0},  # 左腕
    ]
    
    # 测试角度计算
    angle = calc.compute_angle(landmarks, 11, 13, 15)
    
    if angle is not None:
        print(f"✓ 角度计算成功: {angle:.2f}°")
    else:
        print("✗ 角度计算失败")
    
    # 测试角度序列计算
    landmarks_seq = [landmarks] * 10
    angles_seq = calc.compute_all(landmarks_seq)
    
    if len(angles_seq) == 10:
        print(f"✓ 角度序列计算成功: {len(angles_seq)}帧")
    else:
        print("✗ 角度序列计算失败")
    
    # 测试角度范围检查
    is_in_range = calc.check_angle_in_range(95, (80, 100))
    
    if is_in_range:
        print("✓ 角度范围检查成功")
    else:
        print("✗ 角度范围检查失败")
    
    print("\n角度计算模块测试完成!")


if __name__ == "__main__":
    test_angle_calculator()
