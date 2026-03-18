# -*- coding: utf-8 -*-
"""
查看归档内容
"""

from pathlib import Path
import sys
import json

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.archive_manager import ArchiveManager


def main():
    print("=" * 60)
    print("归档内容查看")
    print("=" * 60)

    # 初始化归档管理器
    archive_root = project_root / "data" / "archive"
    manager = ArchiveManager(archive_root)

    # 检查归档是否存在
    if not archive_root.exists():
        print(f"\n错误: 归档目录不存在: {archive_root}")
        return

    # 显示统计
    stats = manager.get_archive_stats()
    print(f"\n归档统计:")
    print(f"  动作数: {stats['total_actions']}")
    print(f"  视频数: {stats['total_videos']}")
    print(f"  标注视频: {stats['total_annotated_videos']}")
    print(f"  最佳帧: {stats['total_best_frames']}")
    print(f"  总大小: {stats['total_size_mb']:.2f} MB")

    # 详细目录
    print(f"\n详细目录:")
    for action_dir in sorted(archive_root.iterdir()):
        if not action_dir.is_dir() or action_dir.name == "__pycache__":
            continue

        print(f"\n  动作: {action_dir.name}")
        print(f"  路径: {action_dir.relative_to(project_root)}")

        for video_dir in sorted(action_dir.iterdir()):
            if not video_dir.is_dir():
                continue

            print(f"\n    视频: {video_dir.name}")

            # 检查文件
            video_file = video_dir / "video_annotated.mp4"
            if video_file.exists():
                size_mb = video_file.stat().st_size / (1024 * 1024)
                print(f"      ✓ 标注视频: {size_mb:.2f} MB")

            best_frames_dir = video_dir / "best_frames"
            if best_frames_dir.exists():
                frames = list(best_frames_dir.glob("*.jpg"))
                print(f"      ✓ 最佳帧: {len(frames)} 张")

            analysis_file = video_dir / "analysis.png"
            if analysis_file.exists():
                print(f"      ✓ 分析图表: 是")

            metadata_file = video_dir / "metadata.json"
            if metadata_file.exists():
                print(f"      ✓ 元数据: 是")

    # 显示索引
    index_file = archive_root / "index.json"
    if index_file.exists():
        print(f"\n" + "=" * 60)
        print("归档索引 (index.json):")
        print("=" * 60)

        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)

        print(f"\n创建时间: {index['created_at']}")
        print(f"\n动作列表:")
        for action in index['actions']:
            print(f"  - {action['name']}: {len(action['videos'])} 个视频")

    print("\n" + "=" * 60)
    print(f"归档位置: {archive_root.relative_to(project_root)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
