# 安装指南

## 快速安装

### 步骤 1: 安装 Python 依赖

```bash
cd d:/yuga_test
pip install -r requirements.txt
```

如果安装速度慢，可以使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步骤 2: 验证安装

```bash
python test_system.py
```

### 步骤 3: 启动应用

```bash
python run.py
```

## 可选步骤：配置 Ollama（用于 AI 评估）

如果想要使用 AI 评估功能：

1. 下载安装 Ollama: https://ollama.ai/

2. 拉取模型：
```bash
ollama pull qwen:7b
```

3. 验证服务：
```bash
curl http://localhost:11434/api/tags
```

## 常见问题

### 问题：pip 安装失败

**解决方案：**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题：MediaPipe 安装失败

**解决方案：**
```bash
# 单独安装 MediaPipe
pip install mediapipe
```

### 问题：OpenCV 安装失败

**解决方案：**
```bash
# 单独安装 OpenCV
pip install opencv-python
```

## 依赖包列表

- opencv-python >= 4.8.0
- mediapipe >= 0.10.0
- numpy >= 1.24.0
- requests >= 2.31.0
- matplotlib >= 3.7.0
- gradio >= 4.0.0
- pillow >= 10.0.0
- pandas >= 1.5.0
- tqdm >= 4.65.0

## 系统要求

- Python 3.9 或更高版本
- Windows 10/11 或 Linux
- （推荐）NVIDIA GPU 6GB+ 显存
- （可选）Ollama 本地大模型服务

## 安装验证

运行以下命令检查所有模块是否正确安装：

```bash
python test_system.py
```

成功输出应显示：
```
✓ 所有依赖包已安装
✓ 所有模块导入成功
```
