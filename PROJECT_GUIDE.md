# 瑜伽动作评估系统 - 完整指南

## 📋 目录

1. [快速开始](#快速开始)
2. [环境配置](#环境配置)
3. [项目结构](#项目结构)
4. [使用方法](#使用方法)
5. [归档系统](#归档系统)
6. [常见问题](#常见问题)

## 🚀 快速开始

### Windows 用户

1. **激活环境**
   ```bash
   conda activate yuga
   ```

2. **运行测试**
   ```bash
   # 处理单个视频
   python temp_tests/test_ardhakati.py

   # 批量处理
   python temp_tests/test_mediapipe_batch.py

   # 查看归档
   python view_archive.py
   ```

3. **或使用快速启动脚本**
   ```bash
   quick_start.bat
   ```

## ⚙️ 环境配置

### 已配置环境

- **环境名称**: `yuga`
- **Python 版本**: 3.9
- **Conda 路径**: `D:\conda`

### 关键依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| opencv-python | 4.13.0 | 视频处理 |
| mediapipe | 0.10.5 | 姿态检测 |
| numpy | 2.0.2 | 数值计算 |
| matplotlib | 3.9.4 | 数据可视化 |
| gradio | 4.44.1 | Web 界面 |
| protobuf | 3.20.3 | 序列化 |

### 环境激活

**方法1：手动激活**
```bash
conda activate yuga
```

**方法2：使用启动脚本**
```bash
start_yuga.bat
```

详细环境配置请查看 [ENV_SETUP.md](ENV_SETUP.md)。

## 📁 项目结构

```
yuga_test/
├── src/                           # 核心源代码
│   ├── pose_detector.py           # MediaPipe 姿态检测
│   ├── frame_sampler.py           # 帧采样与过滤
│   ├── archive_manager.py         # 归档管理
│   └── ...
├── config/                        # 配置文件
│   └── settings.py               # 动作标准定义
├── data/                          # 数据目录
│   ├── raw/                      # 原始视频
│   ├── temp/                     # 临时输出
│   └── archive/                  # 最终归档
│       └── index.json            # 归档索引
├── temp_tests/                    # 测试脚本
│   ├── test_ardhakati.py         # 单视频测试
│   └── test_mediapipe_batch.py   # 批量处理
├── utils/                         # 工具函数
├── archive_results.py             # 手动归档脚本
├── view_archive.py                # 查看归档脚本
├── quick_start.bat               # 快速启动脚本
├── start_yuga.bat               # 环境启动脚本
├── README.md                     # 项目说明
├── ARCHIVE_GUIDE.md             # 归档系统指南
└── ENV_SETUP.md                 # 环境配置说明
```

## 🎯 使用方法

### 1. 处理单个视频

```bash
python temp_tests/test_ardhakati.py
```

**功能**：
- 视频帧采样（每秒 2 帧）
- 质量过滤（模糊、亮度、置信度）
- 关键点检测与标注
- 生成标注视频
- 提取最佳 5 帧
- 生成分析图表
- **自动归档**到 `data/archive/`

**输出位置**：
```
data/archive/Ardhakati_Chakrasana/{视频名}/
├── video_annotated.mp4
├── best_frames/
│   ├── frame_1.jpg
│   └── ...
├── analysis.png
└── metadata.json
```

### 2. 批量处理视频

```bash
python temp_tests/test_mediapipe_batch.py
```

**功能**：
- 遍历 `data/temp/` 下的所有视频
- 逐个处理并生成标注
- **每个视频自动归档**
- 生成归档索引和统计

### 3. 查看归档内容

```bash
python view_archive.py
```

**显示信息**：
- 归档统计（动作数、视频数、总大小）
- 详细目录结构
- 每个视频的文件清单
- 归档索引内容

### 4. 手动归档

```bash
python archive_results.py
```

**功能**：
- 将 `data/temp/` 下所有 `_annotated` 文件夹
- 复制到 `data/archive/`
- 更新归档索引

### 5. 启动 Web 界面

```bash
python run.py
```

然后访问 http://localhost:7860

## 📦 归档系统

### 归档流程

```
原始视频
    ↓
[处理] → 生成标注
    ↓
[临时] → temp/{动作名}/{视频名}_annotated/
    ↓
[归档] → archive/{动作名}/{视频名}/
    ↓
[索引] → index.json
```

### 归档内容

每个归档包含：

1. **标注视频** (`video_annotated.mp4`)
   - 包含 33 个关键点和骨骼连线
   - 只包含有效帧（通过质量过滤）

2. **最佳帧** (`best_frames/`)
   - 评分最高的 5 帧
   - 完整的关键点标注

3. **分析图表** (`analysis.png`)
   - 置信度分布
   - 清晰度变化
   - 亮度变化
   - 有效点比例

4. **元数据** (`metadata.json`)
   - 处理参数
   - 统计信息
   - 时间戳

### 归档管理

**ArchiveManager 类**提供完整的管理功能：

```python
from src.archive_manager import ArchiveManager

manager = ArchiveManager("data/archive")

# 归档单个视频
archive_dir = manager.archive_video_result(...)

# 批量归档
archived = manager.batch_archive_from_temp(...)

# 创建索引
manager.create_archive_index()

# 获取统计
stats = manager.get_archive_stats()

# 列出内容
manager.list_archives()
```

详细说明请查看 [ARCHIVE_GUIDE.md](ARCHIVE_GUIDE.md)。

## ❓ 常见问题

### Q1: 每次打开终端都要激活环境？

**A**: 是的。每次打开新终端需要运行：
```bash
conda activate yuga
```

或者使用启动脚本：
```bash
start_yuga.bat
```

### Q2: cv2 模块找不到？

**A**: 确保环境已激活：
```bash
conda activate yuga
python temp_tests/test_ardhakati.py
```

### Q3: MediaPipe 版本问题？

**A**: MediaPipe 已降级到 0.10.5 版本。如果遇到问题：
```bash
pip install mediapipe==0.10.5 --force-reinstall
```

### Q4: 中文乱码？

**A**: 脚本已添加 UTF-8 编码设置。如果仍有问题：
```bash
chcp 65001
```

### Q5: 归档在哪里？

**A**: 归档位置：`data/archive/`

查看归档：
```bash
python view_archive.py
```

## 📚 相关文档

- [README.md](README.md) - 项目概述
- [ARCHIVE_GUIDE.md](ARCHIVE_GUIDE.md) - 归档系统详细指南
- [ENV_SETUP.md](ENV_SETUP.md) - 环境配置说明

## 🔧 技术栈

- **计算机视觉**: OpenCV, MediaPipe
- **数值计算**: NumPy
- **可视化**: Matplotlib
- **Web 界面**: Gradio
- **大模型**: Ollama (可选)

## 📝 开发笔记

### 关键特性

1. **智能帧采样**
   - 均匀采样（每秒 2 帧）
   - 质量过滤（模糊、亮度、置信度）
   - 无效帧自动剔除

2. **完整归档系统**
   - 自动归档
   - 索引管理
   - 统计分析

3. **批量处理**
   - 支持批量视频处理
   - 每个视频独立归档

4. **可视化输出**
   - 标注视频
   - 最佳帧预览
   - 分析图表

## 📞 获取帮助

如遇问题，请检查：
1. 环境是否正确激活
2. 依赖是否正确安装
3. 视频文件路径是否正确
4. 查看错误日志信息

---

**项目路径**: `d:/yuga_test/`

**归档路径**: `d:/yuga_test/data/archive/`

**环境名称**: `yuga`
