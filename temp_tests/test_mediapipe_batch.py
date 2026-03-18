"""
测试 MediaPipe 人体关键点检测（批量处理视频）
为每个视频生成对应的标注文件夹和标注视频
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pose_detector import PoseDetector
from src.frame_sampler import FrameSampler

print("=" * 60)
print("MediaPipe 批量关键点检测")
print("=" * 60)

# 1. 查找data/temp目录下的所有视频
print("\n1. 查找视频...")
video_dir = project_root / "data" / "temp"
video_files = list(video_dir.glob("*.mp4")) + list(video_dir.glob("*.avi")) + list(video_dir.glob("*.mov"))

if not video_files:
    print(f"✗ 在 {video_dir} 目录下未找到视频文件")
    sys.exit(1)

print(f"✓ 找到 {len(video_files)} 个视频:")
for i, video_path in enumerate(video_files):
    print(f"  {i+1}. {video_path.name}")

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

# 4. 批量处理每个视频
print("\n3. 开始批量处理...")

for video_idx, video_path in enumerate(video_files, 1):
    print(f"\n{'='*60}")
    print(f"处理视频 {video_idx}/{len(video_files)}: {video_path.name}")
    print(f"{'='*60}")
    
    # 为每个视频创建对应的输出文件夹
    video_name = video_path.stem  # 去掉扩展名
    output_dir = video_path.parent / f"{video_name}_annotated"
    output_dir.mkdir(exist_ok=True)
    
    print(f"输出目录: {output_dir}")
    
    # 采样并过滤（每秒2帧）
    valid_frames, stats = sampler.sample_from_video(
        video_path=str(video_path),
        frame_interval=0.5  # 每秒2帧
    )
    
    # 显示统计信息
    print(f"\n采样统计:")
    print(f"  采样帧数: {stats['total_sampled']}")
    print(f"  有效帧数: {stats['valid_frames']}")
    print(f"  无效帧数: {stats['invalid_frames']}")
    print(f"  有效率: {stats['valid_ratio']*100:.1f}%")
    print(f"  平均置信度: {stats['avg_confidence']:.3f}")
    
    # 显示无效原因
    if stats['invalid_reasons']:
        print(f"\n  无效原因统计:")
        for reason, count in stats['invalid_reasons'].items():
            print(f"    - {reason}: {count}帧")
    
    if not valid_frames:
        print(f"\n✗ 没有检测到有效帧，跳过此视频")
        continue
    
    # 保存标注视频
    print(f"\n4. 保存标注视频...")
    
    # 读取视频信息
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 标注视频输出路径
    annotated_video_path = output_dir / f"{video_name}_annotated.mp4"
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(annotated_video_path), fourcc, fps, (width, height))
    
    # 为每个有效帧绘制关键点
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
    
    print(f"✓ 标注视频已保存: {annotated_video_path.name}")
    print(f"  包含 {draw_count} 个有效帧")
    
    # 保存最佳帧图片
    print(f"\n5. 保存最佳帧预览...")
    best_frames = sampler.get_best_frames(valid_frames, top_k=5)
    
    for i, frame_info in enumerate(best_frames):
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
    
    print(f"✓ 已保存 {len(best_frames)} 个最佳帧预览")

    # 归档结果
    print(f"\n6. 归档标注结果...")
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
            "processing_date": stats.get("processing_time"),
            "total_sampled": stats['total_sampled'],
            "valid_frames": stats['valid_frames'],
            "valid_ratio": stats['valid_ratio'],
            "avg_confidence": stats['avg_confidence'],
            "avg_blur": stats['avg_blur'],
            "avg_brightness": stats['avg_brightness'],
            "frame_interval": 0.5,
            "best_frames_count": len(best_frame_paths)
        }

        # 归档
        archive_dir = archive_manager.archive_video_result(
            action_name=video_path.parent.name,  # 使用父目录名作为动作名
            video_name=video_name,
            annotated_video_path=annotated_video_path,
            best_frames=best_frame_paths,
            metadata=metadata
        )

        print(f"✓ 归档成功: {archive_dir.relative_to(project_root)}")

    except ImportError:
        print("⚠ 归档管理器未找到，跳过归档")
    except Exception as e:
        print(f"⚠ 归档失败: {e}")

# 6. 总结
print(f"\n{'='*60}")
print("批量处理完成!")
print(f"{'='*60}")
print(f"总共处理了 {len(video_files)} 个视频")

# 显示归档统计
try:
    from src.archive_manager import ArchiveManager
    archive_manager = ArchiveManager(project_root / "data" / "archive")
    print(f"\n归档统计:")
    archive_manager.list_archives()
except:
    pass

print(f"\n标注视频位置:")
for video_path in video_files:
    video_name = video_path.stem
    output_dir = video_path.parent / f"{video_name}_annotated"
    annotated_video = output_dir / f"{video_name}_annotated.mp4"
    if annotated_video.exists():
        print(f"  - {annotated_video.relative_to(project_root)}")
