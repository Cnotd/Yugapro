"""
测试 MediaPipe 人体关键点检测（使用新的采样器）
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pose_detector import PoseDetector
from src.video_reader import VideoReader
from src.frame_sampler import FrameSampler

print("=" * 60)
print("MediaPipe 人体关键点检测测试（智能采样）")
print("=" * 60)

# 1. 查找测试视频
print("\n1. 查找测试视频...")
video_paths = list(Path("data").rglob("*.mp4"))
if not video_paths:
    print("✗ 未找到测试视频")
    print("提示: 请将 mp4 视频文件放入 data/ 目录")
    sys.exit(1)

video_path = video_paths[0]
print(f"✓ 找到视频: {video_path.name}")

# 2. 初始化采样器
print("\n2. 初始化帧采样器...")
sampler = FrameSampler(
    confidence_threshold=0.5,
    min_valid_ratio=0.7,
    blur_threshold=50.0,
    brightness_range=(30, 225)
)
print("✓ 采样器初始化成功")

# 3. 采样并过滤（每秒2帧）
print("\n3. 开始均匀采样并过滤无效帧...")
print("(每秒抽 2 帧)")

valid_frames, stats = sampler.sample_from_video(
    video_path=str(video_path),
    frame_interval=0.5  # 间隔0.5秒（每秒2帧）
)

# 4. 显示统计信息
print("\n" + "=" * 60)
print("采样统计报告")
print("=" * 60)
print(f"采样帧数: {stats['total_sampled']}")
print(f"有效帧数: {stats['valid_frames']}")
print(f"无效帧数: {stats['invalid_frames']}")
print(f"有效率: {stats['valid_ratio']*100:.1f}%")
print(f"平均置信度: {stats['avg_confidence']:.3f}")
print(f"平均清晰度: {stats['avg_blur']:.1f}")
print(f"平均亮度: {stats['avg_brightness']:.1f}")
print(f"处理时间: {stats['processing_time']:.2f}秒")

print("\n无效原因统计:")
for reason, count in stats['invalid_reasons'].items():
    print(f"  - {reason}: {count}帧")

# 5. 显示有效帧信息
if valid_frames:
    print("\n" + "=" * 60)
    print("有效帧详情")
    print("=" * 60)
    print(f"{'时间点':<12} {'置信度':<10} {'清晰度':<10} {'亮度':<10} {'有效点比例':<12}")
    print("-" * 60)
    
    for frame_info in valid_frames[:10]:  # 显示前10个有效帧
        print(f"{frame_info.timestamp:<12.1f} "
              f"{frame_info.confidence:<10.3f} "
              f"{frame_info.blur_score:<10.1f} "
              f"{frame_info.brightness:<10.1f} "
              f"{frame_info.valid_points_ratio:<12.2f}")
    
    if len(valid_frames) > 10:
        print(f"... 还有 {len(valid_frames) - 10} 帧")
    
    # 6. 保存标注视频
    print("\n6. 保存标注视频...")
    
    # 初始化 PoseDetector 用于绘制
    pose_detector = PoseDetector()
    
    # 读取视频信息
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    output_path = project_root / "data" / "output_test.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    # 为每个有效帧绘制关键点
    for frame_info in valid_frames:
        # 转换 landmarks
        landmarks = []
        if frame_info.landmarks:
            for idx, lm in enumerate(frame_info.landmarks.landmark):
                landmarks.append({
                    "id": idx,
                    "x": lm.x,
                    "y": lm.y,
                    "z": lm.z,
                    "visibility": lm.visibility
                })
        
        # 绘制骨骼
        annotated = pose_detector.draw_landmarks(frame_info.frame, landmarks)
        out.write(annotated)
    
    cap.release()
    out.release()
    print(f"✓ 标注视频已保存: {output_path}")
    print(f"  包含 {len(valid_frames)} 个有效帧")
    
    # 7. 选择最佳帧
    best_frames = sampler.get_best_frames(valid_frames, top_k=5)
    print(f"\n7. 最佳5帧:")
    for i, frame_info in enumerate(best_frames):
        print(f"  {i+1}. 帧{frame_info.frame_idx} (时间: {frame_info.timestamp:.1f}秒) "
              f"- 置信度: {frame_info.confidence:.3f}, "
              f"综合评分: {frame_info.composite_score:.3f}")

print("\n" + "=" * 60)
if valid_frames:
    print("✓ MediaPipe 关键点检测测试通过!")
    print(f"✓ 成功检测并标注 {len(valid_frames)} 个有效帧")
else:
    print("⚠ 没有检测到有效帧")
    print("可能有以下原因:")
    print("  - 视频中人体不够清晰")
    print("  - 视频质量较差")
    print("  - 视频中无人")
print("=" * 60)
