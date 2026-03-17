# 瑜伽动作评估系统

基于多模态大模型的智能瑜伽动作评估系统

## 项目概述

本系统利用计算机视觉和人工智能技术,对用户上传的瑜伽动作视频进行自动分析,给出专业评分和改进建议。

### 核心功能

- ✅ 视频上传与预处理
- ✅ 人体关键点检测(33个关键点)
- ✅ 关节角度计算与分析
- ✅ 动作稳定性评估
- ✅ AI大模型专业评估(支持Ollama)
- ✅ 可视化结果展示
- ✅ 骨骼标注视频生成

### 支持的瑜伽动作

1. 下犬式
2. 树式
3. 战士一式
4. 三角式
5. 猫牛式

## 环境要求

- Python 3.9+
- Windows 10/11 或 Linux
- (可选) NVIDIA GPU 6GB+ 显存
- (可选) Ollama 本地大模型服务

## 安装步骤

### 1. 克隆或下载项目

```bash
cd d:/yuga_test
```

### 2. 创建虚拟环境(推荐)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 方法一: 使用Ollama(推荐,获得AI评估)

1. 安装Ollama: https://ollama.ai/

2. 拉取Qwen模型(或其他支持视觉的模型):
```bash
ollama pull qwen:7b
```

3. 启动系统:
```bash
python run.py
```

4. 打开浏览器访问: http://localhost:7860

### 方法二: 不使用Ollama(基础评估)

1. 直接启动系统:
```bash
python run.py
```

2. 系统将使用基础统计分析进行评估,功能受限

## 项目结构

```
yoga_assessment_system/
├── src/                    # 源代码目录
│   ├── video_reader.py     # 视频读取模块
│   ├── pose_detector.py    # 关键点检测模块
│   ├── angle_calculator.py # 角度计算模块
│   ├── stats_calculator.py # 统计分析模块
│   ├── prompt_builder.py   # 提示词构建模块
│   ├── ollama_client.py    # Ollama客户端
│   ├── result_parser.py    # 结果解析模块
│   └── app.py             # Gradio主界面
├── config/                 # 配置文件
│   └── settings.py        # 动作标准库
├── utils/                  # 工具函数
│   ├── video_utils.py     # 视频处理工具
│   └── visualization.py   # 可视化工具
├── data/                  # 数据目录
│   ├── raw/              # 原始视频
│   ├── processed/        # 处理结果
│   └── test_set/         # 测试集
├── requirements.txt       # 依赖列表
├── README.md              # 项目说明
└── run.py                 # 启动脚本
```

## 系统架构

```
用户上传视频
    ↓
[VideoReader] → 视频信息
    ↓
[PoseDetector] → 33个关键点坐标(逐帧)
    ↓
[AngleCalculator] → 各关节角度(逐帧)
    ↓
[StatsCalculator] → 统计特征 + 稳定性评分
    ↓
[PromptBuilder] → 结构化提示词
    ↓
[OllamaClient] → 调用Qwen模型
    ↓
[ResultParser] → 分数 + 问题 + 建议
    ↓
[Gradio界面] → 可视化展示
```

## 评估维度

系统从三个维度评估瑜伽动作:

1. **角度准确性** (40分): 主要关节角度是否在标准范围内
2. **动作稳定性** (30分): 动作是否稳定,是否有过大晃动
3. **整体协调性** (30分): 动作是否流畅,身体各部位是否协调

## 评估输出

每个视频评估后,系统将生成:

1. **标注视频**: 显示骨骼连线和关键点
2. **评分分布图**: 各维度得分可视化
3. **角度变化曲线**: 关键关节角度随时间变化
4. **评估报告**: 包含分数、主要问题和改进建议

## 性能要求

- 视频处理速度: ≤30秒/分钟视频
- 模型推理速度: ≤10秒/次
- 显存占用: ≤4GB
- 支持视频格式: mp4, avi, mov
- 最大文件大小: 100MB
- 最大视频时长: 2分钟

## 常见问题

### Q: 无法连接到Ollama服务怎么办?

A: 请确保:
1. Ollama服务已启动
2. 端口11434未被占用
3. 已拉取对应的模型

### Q: 关键点检测失败怎么办?

A: 请确保:
1. 视频中有人物
2. 光线充足
3. 人物姿态清晰可见

### Q: 评估结果不准确怎么办?

A: 系统评估仅供参考,建议:
1. 配合专业瑜伽教练指导
2. 从多个角度拍摄视频
3. 选择光线明亮、背景整洁的环境

## 技术栈

- **计算机视觉**: OpenCV, MediaPipe
- **机器学习**: NumPy
- **大模型**: Ollama (可选)
- **界面框架**: Gradio
- **可视化**: Matplotlib

## 许可证

MIT License

## 作者

AI助手 - 基于多模态大模型的瑜伽动作评估系统

## 更新日志

### v1.0.0 (2024)
- 初始版本发布
- 支持5种瑜伽动作评估
- 集成MediaPose关键点检测
- 集成Ollama大模型评估
- Web界面展示
