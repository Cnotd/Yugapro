# 归档系统使用指南

## 目录结构

```
data/
├── raw/              # 原始视频（待处理）
├── temp/             # 临时输出（处理过程中的中间文件）
│   └── {动作名}/
│       ├── 视频.mp4
│       └── 视频_annotated/  # 临时标注文件夹
│           ├── video_annotated.mp4
│           ├── frame_*.jpg
│           └── analysis.png
└── archive/          # 最终归档（长期保存）
    ├── index.json    # 归档索引
    └── {动作名}/
        └── {视频名}/
            ├── video_annotated.mp4  # 标注视频
            ├── best_frames/         # 最佳帧
            │   ├── frame_1.jpg
            │   ├── frame_2.jpg
            │   └── ...
            ├── analysis.png          # 分析图表
            └── metadata.json        # 元数据（可选）
```

## 使用方法

### 1. 自动归档（推荐）

运行单个视频测试脚本时，会自动归档：

```bash
python temp_tests/test_ardhakati.py
```

脚本会：
- 处理视频并生成标注
- 自动将结果归档到 `data/archive/`

### 2. 批量归档

运行批量处理脚本：

```bash
python temp_tests/test_mediapipe_batch.py
```

每个视频处理完成后都会自动归档。

### 3. 手动归档

如果想手动归档 `data/temp/` 下的所有标注结果：

```bash
python archive_results.py
```

这会将 `temp/` 下所有 `_annotated` 文件夹复制到 `archive/`。

### 4. 查看归档

查看归档内容和统计：

```bash
python view_archive.py
```

## 归档内容说明

### 标注视频 (video_annotated.mp4)
- 包含关键点和骨骼连线的标注视频
- 只包含有效帧（通过质量过滤）

### 最佳帧 (best_frames/)
- 选取评分最高的 5 帧
- 每帧都包含完整的关键点标注
- 文件名格式：`frame_1.jpg`, `frame_2.jpg`, ...

### 分析图表 (analysis.png)
- 4 个子图的分析报告：
  - 置信度分布
  - 清晰度随时间变化
  - 亮度随时间变化
  - 有效关键点比例分布

### 元数据 (metadata.json)
- 处理参数（采样率、阈值等）
- 统计信息（有效率、平均置信度等）
- 处理时间戳

## 归档管理工具

### ArchiveManager 类

位于 `src/archive_manager.py`，提供以下功能：

```python
from src.archive_manager import ArchiveManager

# 初始化
manager = ArchiveManager("data/archive")

# 归档单个视频结果
archive_dir = manager.archive_video_result(
    action_name="Ardhakati_Chakrasana",
    video_name="视频名称",
    annotated_video_path="标注视频路径",
    best_frames=["帧1.jpg", "帧2.jpg", ...],
    analysis_chart="分析图路径",
    metadata={"key": "value"}
)

# 批量归档（从 temp 目录）
archived_dirs = manager.batch_archive_from_temp(
    action_name="动作名",
    temp_dir="data/temp/动作名",
    move=False  # True=移动，False=复制
)

# 创建索引
manager.create_archive_index()

# 获取统计
stats = manager.get_archive_stats()

# 列出内容
manager.list_archives()
```

## 归档索引 (index.json)

JSON 格式的索引文件，记录所有归档内容：

```json
{
  "created_at": "2026-03-18T14:23:59.977153",
  "actions": [
    {
      "name": "Ardhakati_Chakrasana",
      "videos": [
        {
          "name": "Ardhakati Chakrasana Right Step Angle 1",
          "annotated_video": true,
          "best_frames_count": 5,
          "metadata_file": false
        }
      ]
    }
  ]
}
```

## 常见操作

### 清理临时文件

归档完成后，可以删除 `data/temp/` 下的临时标注文件夹：

```bash
# 删除所有 _annotated 文件夹
python -c "import shutil; [shutil.rmtree(d) for d in Path('data/temp').rglob('*_annotated')]"
```

### 备份归档

将整个 `data/archive/` 目录压缩备份：

```bash
# Windows
tar -czf archive_backup.tar.gz data/archive/

# 或者使用 7-Zip、WinRAR 等工具
```

### 导出归档列表

导出归档目录树：

```bash
tree data/archive /F > archive_tree.txt
```

## 注意事项

1. **归档是复制而非移动**：原始文件仍在 `temp/` 中，需要手动清理
2. **索引自动更新**：每次归档后建议运行 `manager.create_archive_index()`
3. **定期备份**：`archive/` 是长期保存目录，建议定期备份
4. **存储空间**：归档文件较大，注意磁盘空间

## 快速命令参考

```bash
# 查看归档
python view_archive.py

# 手动归档
python archive_results.py

# 处理并归档（自动）
python temp_tests/test_ardhakati.py

# 批量处理并归档（自动）
python temp_tests/test_mediapipe_batch.py
```
