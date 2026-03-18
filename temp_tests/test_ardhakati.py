# -*- coding: utf-8 -*-
"""
测试 MediaPipe 人体关键点检测 - Ardhakati Chakrasana 动作
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import os

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pose_detector import PoseDetector
from src.frame_sampler import FrameSampler

print("=" * 60)
print("MediaPipe 关键点检测测试 - Ardhakati Chakrasana")
print("=" * 60)

# 1. 查找 Ardhakati Chakrasana 视频
print("\n1. 查找视频...")
video_dir = project_root / "data" / "temp" / "Ardhakati_Chakrasana"

# 查找可能的文件名
possible_names = [
    "Ardhakati Chakrasana Right Step Angle 1.mp4",
    "Ardhakati_Chakrasana.mp4",
    "Ardhakati_Chakrasana.avi", 
    "Ardhakati Chakrasana.mp4",
    "Ardhakati Chakrasana.avi"
]

video_path = None
for name in possible_names:
    test_path = video_dir / name
    if test_path.exists():
        video_path = test_path
        print(f"✓ 找到视频: {name}")
        break

if not video_path:
    print(f"✗ 未找到 Ardhakati Chakrasana 视频")
    print(f"\n请确保视频文件在 {video_dir} 目录下")
    print(f"支持的文件名: {', '.join(possible_names)}")
    
    # 列出目录下的所有文件
    print(f"\n{video_dir} 目录下的所有视频:")
    for f in video_dir.glob("*.mp4"):
        print(f"  - {f.name}")
    sys.exit(1)

# 2. 初始化采样器
print("\n2. 初始化帧采样器...")
sampler = FrameSampler(
    confidence_threshold=0.5,
    min_valid_ratio=0.7,
    blur_threshold=50.0,
    brightness_range=(30, 225)
)
print("✓ 采样器初始化成功")

# 3. 初始化 PoseDetector 用于绘制
pose_detector = PoseDetector()

# 4. 创建输出文件夹
video_name = video_path.stem
output_dir = video_path.parent / f"{video_name}_annotated"
output_dir.mkdir(exist_ok=True)
print(f"\n3. 输出目录: {output_dir.relative_to(project_root)}")

# 5. 采样并过滤（每秒2帧）
print("\n4. 开始采样和过滤...")
print("(每秒抽 2 帧)")

valid_frames, stats = sampler.sample_from_video(
    video_path=str(video_path),
    frame_interval=0.5  # 每秒2帧
)

# 6. 显示详细统计
print("\n" + "=" * 60)
print("采样统计报告 - Ardhakati Chakrasana")
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
    percentage = count / stats['total_sampled'] * 100
    print(f"  - {reason}: {count}帧 ({percentage:.1f}%)")

if not valid_frames:
    print(f"\n✗ 没有检测到有效帧")
    sys.exit(1)

# 7. 显示有效帧详情
print("\n" + "=" * 60)
print("有效帧详情 (显示前20帧）")
print("=" * 60)
print(f"{'时间点':<12} {'置信度':<10} {'清晰度':<10} {'亮度':<10} {'有效点比例':<12} {'综合评分':<10}")
print("-" * 66)

for frame_info in valid_frames[:20]:
    if hasattr(frame_info, 'composite_score'):
        score_str = f"{frame_info.composite_score:.3f}"
    else:
        score_str = "N/A"
    
    print(f"{frame_info.timestamp:<12.1f} "
          f"{frame_info.confidence:<10.3f} "
          f"{frame_info.blur_score:<10.1f} "
          f"{frame_info.brightness:<10.1f} "
          f"{frame_info.valid_points_ratio:<12.2f} "
          f"{score_str:<10}")

if len(valid_frames) > 20:
    print(f"... 还有 {len(valid_frames) - 20} 帧")

# 8. 保存标注视频
print("\n" + "=" * 60)
print("保存标注视频")
print("=" * 60)

cap = cv2.VideoCapture(str(video_path))
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

annotated_video_path = output_dir / f"{video_name}_annotated.mp4"
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(str(annotated_video_path), fourcc, fps, (width, height))

print(f"输出文件: {annotated_video_path.name}")
print(f"分辨率: {width}x{height}")
print(f"帧率: {fps} FPS")

draw_count = 0
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
        draw_count += 1

cap.release()
out.release()

print(f"✓ 标注视频已保存")
print(f"  包含 {draw_count} 个有效帧")

# 9. 选择并保存最佳帧
print("\n" + "=" * 60)
print("保存最佳帧预览")
print("=" * 60)

best_frames = sampler.get_best_frames(valid_frames, top_k=5)
print(f"\n最佳5帧（按综合评分排序）:")
print(f"{'排名':<6} {'帧索引':<10} {'时间':<10} {'置信度':<10} {'综合评分':<10}")
print("-" * 60)

for i, frame_info in enumerate(best_frames):
    print(f"{i+1:<6} "
          f"{frame_info.frame_idx:<10} "
          f"{frame_info.timestamp:<10.1f}s "
          f"{frame_info.confidence:<10.3f} "
          f"{frame_info.composite_score:<10.3f}")
    
    # 绘制骨骼
    if frame_info.landmarks:
        landmarks = [{
            "id": idx,
            "x": lm.x,
            "y": lm.y,
            "z": lm.z,
            "visibility": lm.visibility
        } for idx, lm in enumerate(frame_info.landmarks.landmark)]
        annotated = pose_detector.draw_landmarks(frame_info.frame, landmarks)
    else:
        annotated = frame_info.frame
    
    # 保存图片
    preview_path = output_dir / f"frame_{i+1}_score_{frame_info.composite_score:.2f}.jpg"
    cv2.imwrite(str(preview_path), annotated)
    print(f"  ✓ 保存: {preview_path.name}")

# 10. 生成统计图表
print("\n" + "=" * 60)
print("生成统计图表")
print("=" * 60)

try:
    import matplotlib.pyplot as plt
    
    # 创建子图
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. 置信度分布
    ax1 = axes[0, 0]
    confidences = [f.confidence for f in valid_frames]
    ax1.hist(confidences, bins=20, alpha=0.7, color='blue', edgecolor='black')
    ax1.set_xlabel('置信度')
    ax1.set_ylabel('帧数')
    ax1.set_title('有效帧置信度分布')
    ax1.axvline(stats['avg_confidence'], color='red', linestyle='--', 
               label=f'平均: {stats["avg_confidence"]:.3f}')
    ax1.legend()
    
    # 2. 清晰度随时间变化
    ax2 = axes[0, 1]
    timestamps = [f.timestamp for f in valid_frames]
    blur_scores = [f.blur_score for f in valid_frames]
    ax2.scatter(timestamps, blur_scores, alpha=0.5, c='orange', s=10)
    ax2.set_xlabel('时间 (秒)')
    ax2.set_ylabel('清晰度 (拉普拉斯方差)')
    ax2.set_title('清晰度随时间变化')
    ax2.axhline(stats['avg_blur'], color='red', linestyle='--',
               label=f'平均: {stats["avg_blur"]:.1f}')
    ax2.legend()
    
    # 3. 亮度随时间变化
    ax3 = axes[1, 0]
    brightness_scores = [f.brightness for f in valid_frames]
    ax3.scatter(timestamps, brightness_scores, alpha=0.5, c='green', s=10)
    ax3.set_xlabel('时间 (秒)')
    ax3.set_ylabel('亮度')
    ax3.set_title('亮度随时间变化')
    ax3.axhline(stats['avg_brightness'], color='red', linestyle='--',
               label=f'平均: {stats["avg_brightness"]:.1f}')
    ax3.legend()
    
    # 4. 有效点比例分布
    ax4 = axes[1, 1]
    valid_ratios = [f.valid_points_ratio for f in valid_frames]
    ax4.hist(valid_ratios, bins=20, alpha=0.7, color='purple', edgecolor='black')
    ax4.set_xlabel('有效关键点比例')
    ax4.set_ylabel('帧数')
    ax4.set_title('有效关键点比例分布')
    
    plt.tight_layout()
    
    # 保存图表
    chart_path = output_dir / f"{video_name}_analysis.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    print(f"✓ 统计图表已保存: {chart_path.name}")
    plt.close()
    
except ImportError:
    print("⚠ matplotlib 未安装，跳过图表生成")
except Exception as e:
    print(f"⚠ 生成图表失败: {e}")

# 11. 归档结果
print("\n" + "=" * 60)
print("归档标注结果")
print("=" * 60)

try:
    from src.archive_manager import ArchiveManager

    archive_manager = ArchiveManager(project_root / "data" / "archive")

    # 准备归档数据
    best_frame_paths = []
    for i, frame_info in enumerate(best_frames):
        preview_path = output_dir / f"frame_{i+1}_score_{frame_info.composite_score:.2f}.jpg"
        if preview_path.exists():
            best_frame_paths.append(preview_path)

    # 准备元数据
    metadata = {
        "video_name": video_name,
        "action_name": "Ardhakati_Chakrasana",
        "processing_date": stats.get("processing_time"),
        "total_sampled": stats['total_sampled'],
        "valid_frames": stats['valid_frames'],
        "valid_ratio": stats['valid_ratio'],
        "avg_confidence": stats['avg_confidence'],
        "avg_blur": stats['avg_blur'],
        "avg_brightness": stats['avg_brightness'],
        "frame_interval": 0.5,  # 每秒2帧
        "best_frames_count": len(best_frame_paths)
    }

    # 归档
    archive_dir = archive_manager.archive_video_result(
        action_name="Ardhakati_Chakrasana",
        video_name=video_name,
        annotated_video_path=annotated_video_path,
        best_frames=best_frame_paths,
        analysis_chart=chart_path if 'chart_path' in locals() and chart_path.exists() else None,
        metadata=metadata
    )

    print(f"\n✓ 归档成功: {archive_dir.relative_to(project_root)}")

except ImportError:
    print("⚠ 归档管理器未找到，跳过归档")
except Exception as e:
    print(f"⚠ 归档失败: {e}")

# 12. 最终总结
print("\n" + "=" * 60)
print("测试完成总结")
print("=" * 60)
print(f"✓ 视频处理完成: {video_name}")
print(f"✓ 有效帧数: {len(valid_frames)}")
print(f"✓ 有效率: {stats['valid_ratio']*100:.1f}%")
print(f"\n输出文件位置: {output_dir.relative_to(project_root)}")
print(f"  - 标注视频: {annotated_video_path.name}")
print(f"  - 最佳帧预览: 5个 JPG 文件")
if 'chart_path' in locals():
    print(f"  - 统计图表: {chart_path.name}")

print("\n标注说明:")
print("  - 红色关键点: 深度较浅 (离镜头近)")
print("  - 蓝色关键点: 深度较深 (离镜头远)")
print("  - 绿色连线: 骨骼连接")
print("  - 共 33 个关键点")

print("\n" + "=" * 60)
