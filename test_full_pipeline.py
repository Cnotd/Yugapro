# -*- coding: utf-8 -*-
"""
完整功能测试 - 从视频采样到关键点检测
"""

import sys
import os
from pathlib import Path
import cv2
import numpy as np

# 设置为 UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    print("\n" + "=" * 70)
    print("完整功能测试: 视频采样 -> 关键点检测 -> 角度计算")
    print("=" * 70)
    
    # 准备测试视频
    video_path = project_root / "data" / "temp" / "Ardhakati_Chakrasana" / "Ardhakati Chakrasana Right Step Angle 1.mp4"
    
    if not video_path.exists():
        print(f"[ERROR] 视频不存在: {video_path}")
        return 1
    
    print(f"\n[步骤 1/5] 加载视频")
    print(f"视频路径: {video_path.name}")
    print(f"文件大小: {video_path.stat().st_size / (1024*1024):.1f} MB")
    
    # 初始化组件
    from src.pose_detector import PoseDetector
    from src.frame_sampler import FrameSampler
    from src.angle_calculator import AngleCalculator
    from src.stats_calculator import StatsCalculator
    
    try:
        print("\n[步骤 2/5] 初始化帧采样器")
        sampler = FrameSampler(
            confidence_threshold=0.5,
            min_valid_ratio=0.5,
            blur_threshold=50.0,
            brightness_range=(30, 225)
        )
        print("采样配置: 每秒 2 帧, 置信度阈值 0.5")
        
        print("\n[步骤 3/5] 从视频采样帧")
        valid_frames, stats = sampler.sample_from_video(
            video_path=str(video_path),
            frame_interval=0.5  # 每0.5秒采样一帧（每秒2帧）
        )
        
        print(f"采样结果:")
        print(f"  - 总采样帧数: {stats['total_sampled']}")
        print(f"  - 有效帧数: {stats['valid_frames']}")
        print(f"  - 无效帧数: {stats['invalid_frames']}")
        print(f"  - 有效率: {stats['valid_ratio']*100:.1f}%")
        print(f"  - 平均置信度: {stats['avg_confidence']:.3f}")
        print(f"  - 平均亮度: {stats['avg_brightness']:.1f}")
        print(f"  - 平均模糊度: {stats['avg_blur']:.1f}")
        
        if not valid_frames:
            print("\n[WARNING] 未采样到有效帧，跳过后续步骤")
            return 1
        
        print("\n[步骤 4/5] 检测人体关键点")
        pose_detector = PoseDetector()
        angle_calc = AngleCalculator()
        stats_calc = StatsCalculator()
        
        all_keypoints = []
        all_angles = {}
        
        for i, frame in enumerate(valid_frames[:5]):  # 只处理前5帧作为示例
            landmarks = pose_detector.detect(frame.frame)  # frame 是 FrameInfo 对象，needs .frame 属性
            
            if landmarks:  # landmarks 返回的是 [{id, x, y, z, visibility}, ...] 列表
                keypoints = [(lm['x'], lm['y'], lm['z'], lm['visibility']) 
                            for lm in landmarks]
                all_keypoints.append(keypoints)
                
                # 计算角度
                angles = angle_calc._compute_frame_angles(landmarks)
                for joint, angle in angles.items():
                    if joint not in all_angles:
                        all_angles[joint] = []
                    all_angles[joint].append(angle)
                
                print(f"  帧 {i+1}: 检测到 {len(keypoints)} 个关键点")
            else:
                print(f"  帧 {i+1}: 未检测到人体")
        
        print(f"\n共处理帧数: {len(all_keypoints)}")
        
        if all_keypoints:
            print("\n[步骤 5/5] 统计分析")
            print("\n关键关节角度统计:")
            
            for joint in ['右肩关节', '右肘关节', '左肩关节', '左肘关节', '右髋关节', '左髋关节']:
                if joint in all_angles and all_angles[joint]:
                    angles = all_angles[joint]
                    print(f"  {joint}:")
                    print(f"    - 平均角度: {np.mean(angles):.1f}°")
                    print(f"    - 最小值: {np.min(angles):.1f}°")
                    print(f"    - 最大值: {np.max(angles):.1f}°")
                    print(f"    - 方差: {np.var(angles):.1f}°")
        
        print("\n" + "=" * 70)
        print("测试完成: [OK] 系统运行正常")
        print("=" * 70 + "\n")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
