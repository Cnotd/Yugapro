# -*- coding: utf-8 -*-
"""
将标注结果归档到 archive 目录
"""

from pathlib import Path
import sys
import os

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
    print("归档标注结果")
    print("=" * 60)

    # 初始化归档管理器
    archive_root = project_root / "data" / "archive"
    manager = ArchiveManager(archive_root)

    # 查找临时目录
    temp_dir = project_root / "data" / "temp"

    print(f"\n临时目录: {temp_dir.relative_to(project_root)}")
    print(f"归档目录: {archive_root.relative_to(project_root)}")

    # 检查临时目录
    if not temp_dir.exists():
        print(f"\n错误: 临时目录不存在: {temp_dir}")
        return

    # 列出所有动作目录
    action_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
    if not action_dirs:
        print("\n没有找到需要归档的内容")
        return

    print(f"\n找到 {len(action_dirs)} 个动作目录:")
    for action_dir in action_dirs:
        print(f"  - {action_dir.name}")

    # 逐个归档
    for action_dir in action_dirs:
        print(f"\n{'='*60}")
        print(f"归档动作: {action_dir.name}")
        print(f"{'='*60}")

        archived = manager.batch_archive_from_temp(
            action_name=action_dir.name,
            temp_dir=action_dir,
            move=False  # 先复制，不删除原文件
        )

        if archived:
            print(f"\n✓ 成功归档 {len(archived)} 个视频")
        else:
            print(f"\n✗ 没有找到标注结果")

    # 创建索引
    print(f"\n{'='*60}")
    print("创建归档索引")
    print(f"{'='*60}")
    manager.create_archive_index()

    # 显示统计
    print(f"\n{'='*60}")
    print("归档统计")
    print(f"{'='*60}")
    manager.list_archives()

    print("\n" + "=" * 60)
    print("归档完成！")
    print(f"归档位置: {archive_root.relative_to(project_root)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
