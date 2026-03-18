"""
归档管理模块
负责将标注结果组织到归档目录中
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, List
import shutil
import json


class ArchiveManager:
    """归档管理器"""

    def __init__(self, archive_root: Path):
        """
        初始化归档管理器

        Args:
            archive_root: 归档根目录，如 data/archive
        """
        self.archive_root = Path(archive_root)

    def archive_video_result(
        self,
        action_name: str,
        video_name: str,
        annotated_video_path: Path,
        best_frames: List[Path],
        analysis_chart: Optional[Path] = None,
        metadata: Optional[dict] = None
    ) -> Path:
        """
        归档视频标注结果

        Args:
            action_name: 动作名称，如 "Ardhakati_Chakrasana"
            video_name: 视频名称（不带扩展名）
            annotated_video_path: 标注视频路径
            best_frames: 最佳帧图片路径列表
            analysis_chart: 分析图表路径（可选）
            metadata: 元数据信息（可选）

        Returns:
            归档目录路径
        """
        # 创建归档目录结构
        archive_dir = self.archive_root / action_name / video_name
        archive_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        frames_dir = archive_dir / "best_frames"
        frames_dir.mkdir(exist_ok=True)

        # 复制标注视频
        dest_video = archive_dir / "video_annotated.mp4"
        shutil.copy2(annotated_video_path, dest_video)
        print(f"  [归档] 标注视频 -> {dest_video.name}")

        # 复制最佳帧
        for i, frame_path in enumerate(best_frames, 1):
            dest_frame = frames_dir / f"frame_{i}.jpg"
            shutil.copy2(frame_path, dest_frame)
            print(f"  [归档] 最佳帧 {i} -> {dest_frame.name}")

        # 复制分析图表
        if analysis_chart and analysis_chart.exists():
            dest_chart = archive_dir / "analysis.png"
            shutil.copy2(analysis_chart, dest_chart)
            print(f"  [归档] 分析图表 -> {dest_chart.name}")

        # 保存元数据
        if metadata:
            metadata_path = archive_dir / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"  [归档] 元数据 -> {metadata_path.name}")

        return archive_dir

    def batch_archive_from_temp(
        self,
        action_name: str,
        temp_dir: Path,
        move: bool = False
    ) -> List[Path]:
        """
        从临时目录批量归档

        Args:
            action_name: 动作名称
            temp_dir: 临时目录（包含 xxx_annotated 文件夹）
            move: 是否移动（默认为复制）

        Returns:
            归档目录路径列表
        """
        archived_dirs = []

        # 查找所有 annotated 文件夹
        for annotated_dir in temp_dir.glob("*_annotated"):
            # 提取视频名称（去掉 _annotated 后缀）
            video_name = annotated_dir.stem.replace("_annotated", "")

            # 查找标注视频
            annotated_videos = list(annotated_dir.glob("*_annotated.mp4"))
            if not annotated_videos:
                continue
            annotated_video = annotated_videos[0]

            # 查找最佳帧
            best_frames = list((annotated_dir).glob("frame_*.jpg"))

            # 查找分析图表
            analysis_chart = annotated_dir / f"{video_name}_analysis.png"
            if not analysis_chart.exists():
                analysis_chart = None

            # 归档
            archive_dir = self.archive_video_result(
                action_name=action_name,
                video_name=video_name,
                annotated_video_path=annotated_video,
                best_frames=best_frames,
                analysis_chart=analysis_chart
            )

            archived_dirs.append(archive_dir)

            # 如果需要移动，删除原文件
            if move:
                shutil.rmtree(annotated_dir)

        return archived_dirs

    def create_archive_index(self) -> Path:
        """
        创建归档索引文件

        Returns:
            索引文件路径
        """
        index = {
            "created_at": datetime.now().isoformat(),
            "actions": []
        }

        # 遍历所有动作目录
        for action_dir in sorted(self.archive_root.iterdir()):
            if not action_dir.is_dir():
                continue

            action_info = {
                "name": action_dir.name,
                "videos": []
            }

            # 遍历所有视频归档
            for video_dir in sorted(action_dir.iterdir()):
                if not video_dir.is_dir():
                    continue

                # 检查标注视频是否存在
                annotated_video = video_dir / "video_annotated.mp4"
                best_frames_dir = video_dir / "best_frames"

                video_info = {
                    "name": video_dir.name,
                    "annotated_video": annotated_video.exists(),
                    "best_frames_count": len(list(best_frames_dir.glob("*.jpg"))) if best_frames_dir.exists() else 0,
                    "metadata_file": (video_dir / "metadata.json").exists()
                }

                action_info["videos"].append(video_info)

            index["actions"].append(action_info)

        # 保存索引
        index_path = self.archive_root / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        print(f"[索引] 已创建归档索引: {index_path}")
        return index_path

    def get_archive_stats(self) -> dict:
        """
        获取归档统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "total_actions": 0,
            "total_videos": 0,
            "total_annotated_videos": 0,
            "total_best_frames": 0,
            "total_size_mb": 0.0
        }

        for action_dir in self.archive_root.iterdir():
            if not action_dir.is_dir():
                continue

            stats["total_actions"] += 1

            for video_dir in action_dir.iterdir():
                if not video_dir.is_dir():
                    continue

                stats["total_videos"] += 1

                # 统计标注视频
                if (video_dir / "video_annotated.mp4").exists():
                    stats["total_annotated_videos"] += 1

                # 统计最佳帧
                best_frames_dir = video_dir / "best_frames"
                if best_frames_dir.exists():
                    stats["total_best_frames"] += len(list(best_frames_dir.glob("*.jpg")))

                # 统计大小
                for file_path in video_dir.rglob("*"):
                    if file_path.is_file():
                        stats["total_size_mb"] += file_path.stat().st_size / (1024 * 1024)

        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats

    def list_archives(self) -> None:
        """列出所有归档内容"""
        print("\n" + "=" * 60)
        print("归档内容")
        print("=" * 60)

        stats = self.get_archive_stats()
        print(f"动作数: {stats['total_actions']}")
        print(f"视频数: {stats['total_videos']}")
        print(f"标注视频: {stats['total_annotated_videos']}")
        print(f"最佳帧: {stats['total_best_frames']}")
        print(f"总大小: {stats['total_size_mb']:.2f} MB")

        print("\n详细目录:")
        for action_dir in sorted(self.archive_root.iterdir()):
            if not action_dir.is_dir():
                continue

            print(f"\n  动作: {action_dir.name}")
            for video_dir in sorted(action_dir.iterdir()):
                if not video_dir.is_dir():
                    continue

                print(f"    - {video_dir.name}")
