# Temp Tests 文件夹说明

此文件夹包含开发过程中的临时测试文件和辅助工具。

## 文件列表

### 测试文件
- `test_mediapipe.py` - MediaPipe 关键点检测测试（使用智能采样）
- `test_model_output.py` - 测试大模型输出格式
- `test_ollama.py` - Ollama 连接测试

### 辅助工具
- `video_compressor.py` - 视频压缩工具（处理大视频文件）
- `view_video.py` - Python 视频播放器
- `view_video.html` - HTML 视频查看器

### 备用启动脚本
- `run_no_proxy.py` - 禁用代理的启动脚本
- `run_simple.py` - 简化版启动脚本
- `install.py` - 自动安装脚本

### 其他
- `model_output.txt` - 模型输出测试结果

## 使用说明

这些文件是开发过程中的临时文件，不是核心系统的一部分。

### 运行测试

```bash
# 测试 MediaPipe 关键点检测
python temp_tests/test_mediapipe.py

# 测试 Ollama 连接
python temp_tests/test_ollama.py

# 测试模型输出
python temp_tests/test_model_output.py
```

### 使用视频工具

```bash
# 压缩视频
python temp_tests/video_compressor.py

# 查看视频
python temp_tests/view_video.py
# 或打开 view_video.html 在浏览器中查看
```

## 主系统文件

**核心系统文件位于项目根目录：**
- `run.py` - 主启动脚本
- `src/web_app.py` - Flask Web 界面
- `src/` - 所有核心模块
- `tests/` - 单元测试文件

## 注意

- 这些文件不会被正式发布
- 可以随时删除或修改
- 仅用于开发和调试
