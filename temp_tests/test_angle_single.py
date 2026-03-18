# -*- coding: utf-8 -*-
"""
单个视频的角度检测和标注
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import json

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pose_detector import PoseDetector
from src.angle_calculator import AngleCalculator
from src.angle_annotator import AngleAnnotator
from src.frame_sampler import FrameSampler


def main():
    print("=" * 60)
    print("单个视频角度检测和标注")
    print("=" * 60)

    # 指定归档视频路径
    video_path = project_root / "data" / "archive" / "Ardhakati_Chakrasana" / "Ardhakati Chakrasana Right Step Angle 1" / "video_annotated.mp4"

    if not video_path.exists():
        print(f"\n错误: 视频不存在: {video_path}")
        return

    # 输出目录
    output_dir = video_path.parent / "angle_analysis"
    output_dir.mkdir(exist_ok=True)

    print(f"\n视频路径: {video_path.name}")
    print(f"输出目录: {output_dir}")

    # 1. 初始化检测器和采样器
    print(f"\n1. 初始化检测器...")
    pose_detector = PoseDetector()
    sampler = FrameSampler(
        confidence_threshold=0.5,
        min_valid_ratio=0.7,
        blur_threshold=50.0,
        brightness_range=(30, 225)
    )

    # 2. 初始化角度计算器和标注器
    print(f"2. 初始化角度计算器...")
    angle_calculator = AngleCalculator()
    angle_annotator = AngleAnnotator()

    # 3. 采样有效帧
    print(f"\n3. 采样视频（每2秒1帧）...")
    valid_frames, stats = sampler.sample_from_video(
        video_path=str(video_path),
        frame_interval=2.0  # 减少采样率，加快处理速度
    )

    print(f"  采样帧数: {stats['total_sampled']}")
    print(f"  有效帧数: {stats['valid_frames']}")
    print(f"  有效率: {stats['valid_ratio']*100:.1f}%")

    if not valid_frames:
        print("\n没有有效帧，退出")
        return

    # 4. 计算所有帧的角度
    print(f"\n4. 计算角度...")
    angles_seq = []
    timestamps = []

    for frame_info in valid_frames:
        if frame_info.landmarks:
            # 转换 landmarks 为字典格式
            landmarks = []
            for idx, lm in enumerate(frame_info.landmarks.landmark):
                landmarks.append({
                    "id": idx,
                    "x": lm.x,
                    "y": lm.y,
                    "z": lm.z,
                    "visibility": lm.visibility
                })

            timestamps.append(frame_info.timestamp)
            angles = angle_calculator._compute_frame_angles(landmarks)
            angles_seq.append(angles)

    print(f"  计算 {len(angles_seq)} 帧的角度")

    # 5. 计算统计信息
    print(f"\n5. 计算统计信息...")
    avg_angles = angle_calculator.get_average_angles(angles_seq)
    std_angles = angle_calculator.get_angle_std(angles_seq)

    print(f"\n平均角度:")
    for name, value in avg_angles.items():
        print(f"  {name}: {value:.1f}°")

    print(f"\n角度标准差（稳定性）:")
    for name, value in std_angles.items():
        status = "稳定" if value < 5 else "不稳定"
        print(f"  {name}: {value:.2f}° ({status})")

    # 6. 生成最佳帧的角度标注
    print(f"\n6. 生成最佳帧角度标注...")
    best_frames = sampler.get_best_frames(valid_frames, top_k=3)

    best_frames_dir = output_dir / "best_frames_with_angles"
    best_frames_dir.mkdir(exist_ok=True)

    for i, frame_info in enumerate(best_frames):
        # 找到对应的角度
        frame_index = valid_frames.index(frame_info)
        angles = angles_seq[frame_index]

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

        # 绘制角度标注
        annotated_frame = angle_annotator.draw_all_angles(
            frame_info.frame, landmarks, angles
        )

        # 保存
        save_path = best_frames_dir / f"frame_{i+1}_angles.jpg"
        cv2.imwrite(str(save_path), annotated_frame)
        print(f"  保存: {save_path.name}")

    # 7. 生成角度汇总图像
    print(f"\n7. 生成角度汇总...")
    summary_img = angle_annotator.create_angle_summary_image(
        angles_seq, avg_angles, std_angles
    )
    summary_path = output_dir / "angle_summary.png"
    cv2.imwrite(str(summary_path), summary_img)
    print(f"  保存: {summary_path.name}")

    # 8. 生成角度分析图表
    print(f"\n8. 生成角度时间序列图表...")
    try:
        angle_chart = angle_annotator.create_angle_time_series_plot(
            angles_seq, timestamps
        )
        chart_path = output_dir / "angle_time_series.png"
        cv2.imwrite(str(chart_path), angle_chart)
        print(f"  保存: {chart_path.name}")
    except Exception as e:
        print(f"  生成图表失败: {e}")

    # 9. 保存角度数据
    print(f"\n9. 保存角度数据...")
    angle_data_path = output_dir / "angle_data.json"

    angle_data = {
        "video_name": video_path.stem,
        "total_frames": len(angles_seq),
        "avg_angles": avg_angles,
        "std_angles": std_angles,
        "angle_sequence": [
            {
                "timestamp": timestamps[i],
                "angles": angles_seq[i]
            } for i in range(len(angles_seq))
        ]
    }

    with open(angle_data_path, 'w', encoding='utf-8') as f:
        json.dump(angle_data, f, indent=2, ensure_ascii=False)

    print(f"  保存: {angle_data_path.name}")

    # 10. 生成评估报告
    print(f"\n10. 生成评估报告...")
    report_path = output_dir / "angle_assessment_report.txt"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("角度分析评估报告\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"视频名称: {video_path.stem}\n")
        f.write(f"处理帧数: {len(angles_seq)}\n")
        f.write(f"采样率: 0.5 帧/秒\n\n")

        f.write("1. 平均角度\n")
        f.write("-" * 40 + "\n")
        for name, value in avg_angles.items():
            f.write(f"  {name}: {value:.1f}°\n")

        f.write("\n2. 角度稳定性（标准差）\n")
        f.write("-" * 40 + "\n")
        for name, value in std_angles.items():
            status = "稳定" if value < 5 else "不稳定"
            f.write(f"  {name}: {value:.2f}° ({status})\n")

        f.write("\n3. 整体评估\n")
        f.write("-" * 40 + "\n")
        stable_joints = sum(1 for v in std_angles.values() if v < 5)
        total_joints = len(std_angles)
        stability_ratio = stable_joints / total_joints if total_joints > 0 else 0

        f.write(f"  稳定关节数: {stable_joints}/{total_joints}\n")
        f.write(f"  整体稳定性: {stability_ratio*100:.1f}%\n")

        if stability_ratio >= 0.8:
            f.write("  评价: 动作非常稳定\n")
        elif stability_ratio >= 0.5:
            f.write("  评价: 动作比较稳定\n")
        else:
            f.write("  评价: 动作不够稳定，需要改进\n")

    print(f"  保存: {report_path.name}")

    print("\n" + "=" * 60)
    print("处理完成！")
    print(f"\n输出目录: {output_dir}")
    print(f"\n生成文件:")
    print(f"  - best_frames_with_angles/ (3张角度标注帧)")
    print(f"  - angle_summary.png (角度汇总)")
    print(f"  - angle_time_series.png (时间序列图表)")
    print(f"  - angle_data.json (角度数据)")
    print(f"  - angle_assessment_report.txt (评估报告)")
    print("=" * 60)


if __name__ == "__main__":
    main()
